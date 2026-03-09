"""
app/routers/inference.py — Inference endpoints.
"""
from __future__ import annotations

import time
import logging

from fastapi import APIRouter, HTTPException, Body

logger = logging.getLogger(__name__)
from app import ollama_client
from app.prompts import apply_template
from app.schemas import InferenceMetrics, InferenceRequest, InferenceResponse, ExecutionStep

router = APIRouter(prefix="/inference", tags=["Inference"])


async def _run_rlm_pipeline(prompt: str, model: str, neo4j_client, max_iterations: int = 3) -> tuple[str, list[ExecutionStep]]:
    """True RLM: generate → check if needs more → retrieve → loop."""
    logger.info(f"=== RLM PIPELINE START ===")
    steps = []
    iteration = 0
    all_context = []

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"--- Iteration {iteration}/{max_iterations} ---")
        context_text = "\n---\n".join(all_context) if all_context else ""

        if context_text:
            generate_prompt = f"""Use the provided context. If lacking info, state what's missing.

Research question: {prompt}

Available context:
{context_text}

Provide answer or state what's needed."""
        else:
            generate_prompt = f"""Answer. If lacking info, state what's needed.

Research question: {prompt}

Provide answer:"""

        try:
            raw = await ollama_client.generate(prompt=generate_prompt, model=model, system="Be precise.")
            partial_answer = raw.get("response", "")
        except Exception as e:
            partial_answer = f"Error: {e}"

        needs_more, missing_info = _check_if_needs_more_info(partial_answer)
        logger.info(f"  Needs more: {needs_more}")

        steps.append(ExecutionStep(
            id=len(steps) + 1,
            type="reason" if iteration == 1 else "retrieve",
            text=f"Iteration {iteration}: {'Generated' if not needs_more else f'Retrieved for: {missing_info[:50]}...'}",
            details={"iteration": iteration, "needs_more": needs_more, "missing_info": missing_info}
        ))

        if not needs_more:
            steps.append(ExecutionStep(id=len(steps) + 1, type="resolve", text=f"Final answer after {iteration} iteration(s).", details={}))
            return partial_answer, steps

        if missing_info:
            try:
                graph_data = await neo4j_client.search_entities(missing_info)
                nodes = graph_data.get("nodes", [])
                if nodes:
                    new_context = f"Iteration {iteration}:\n"
                    for n in nodes[:5]:
                        new_context += f"- {n.get('id')} ({n.get('label', 'UNKNOWN')})\n"
                    all_context.append(new_context)
                    steps[-1].details["entities_retrieved"] = [n.get("id") for n in nodes[:5]]
            except Exception as e:
                logger.error(f"    Error retrieving: {e}")

    final_context = "\n---\n".join(all_context)
    try:
        raw = await ollama_client.generate(
            prompt=f"Research: {prompt}\nContext: {final_context}\nPrevious: {partial_answer}\nSynthesize final answer.",
            model=model, system="You are a helpful research assistant."
        )
        final_answer = raw.get("response", "")
    except:
        final_answer = partial_answer

    steps.append(ExecutionStep(id=len(steps) + 1, type="resolve", text=f"Synthesized after {max_iterations} iterations.", details={}))
    return final_answer, steps


def _check_if_needs_more_info(answer: str) -> tuple[bool, str]:
    answer_lower = answer.lower()
    patterns = ["don't have enough", "not enough", "insufficient", "i need more", "need more", "cannot answer", "what is", "who is"]
    for p in patterns:
        if p in answer_lower:
            sentences = answer.split('.')
            for s in sentences:
                if p in s.lower() and len(s.strip()) > 10:
                    return True, s.strip()
            return True, answer[:200]
    return False, ""


@router.post("", response_model=InferenceResponse)
async def run_inference(body: InferenceRequest = Body(...)) -> InferenceResponse:
    """Run inference: Standard RAG or RLM pipeline."""
    t0 = time.perf_counter()
    use_rlm = body.strategy in ("Recursive RLM (Decomp)", "Graph Traversal")

    from app.services.neo4j_client import neo4j_client
    trace = []

    if use_rlm:
        answer, trace = await _run_rlm_pipeline(body.prompt, body.model, neo4j_client)
        latency = time.perf_counter() - t0
        eval_count = len(trace) * 50
    else:
        formatted_prompt, auto_system = apply_template(body.prompt_template, body.prompt)
        resolved_system = body.system or auto_system
        try:
            raw = await ollama_client.generate(prompt=formatted_prompt, model=body.model, system=resolved_system)
            answer = raw.get("response", "")
            eval_count = raw.get("eval_count")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")
        latency = time.perf_counter() - t0

    return InferenceResponse(
        answer=answer,
        metrics=InferenceMetrics(model=body.model, strategy=body.strategy, eval_count=eval_count, eval_duration=None, latency_s=round(latency, 3)),
        trace=trace,
    )
