"""
app/routers/inference.py — /api/v1/inference endpoints.
"""
from __future__ import annotations

import time
import json
import logging

from fastapi import APIRouter, HTTPException, Body

logger = logging.getLogger(__name__)
from app import ollama_client
from app.prompts import apply_template
from app.schemas import InferenceMetrics, InferenceRequest, InferenceResponse, ExecutionStep

router = APIRouter(prefix="/inference", tags=["Inference"])


async def _run_raptor_pipeline(
    prompt: str,
    model: str,
    document_name: str = "default",
) -> tuple[str, list[ExecutionStep]]:
    """
    Run the RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) pipeline:
    1. Retrieve relevant nodes from hierarchical tree across multiple levels
    2. Synthesize answer using multi-level context
    Returns (answer, trace_steps).
    """
    from app.services.raptor_service import retrieve_from_raptor, get_raptor_tree_stats
    
    steps = []
    
    # Check if RAPTOR tree exists
    tree_stats = get_raptor_tree_stats(document_name)
    if tree_stats is None:
        steps.append(ExecutionStep(
            id=1, type="retrieve",
            text=f"No RAPTOR tree found for document: {document_name}",
            details={"error": "Tree not built yet"}
        ))
        return f"Error: No RAPTOR tree exists for document '{document_name}'. Please process the document first.", steps
    
    steps.append(ExecutionStep(
        id=1, type="split",
        text=f"Accessing RAPTOR tree with {tree_stats['levels']} levels and {tree_stats['total_nodes']} nodes",
        details=tree_stats
    ))
    
    # Retrieve from multiple levels (level 0 for specific details, higher levels for context)
    try:
        contexts = await retrieve_from_raptor(
            document_name=document_name,
            query=prompt,
            top_k=5,
            levels_to_search=None,  # Search all levels
        )
        
        if not contexts:
            steps.append(ExecutionStep(
                id=2, type="retrieve",
                text="No relevant context found in RAPTOR tree",
                details={"query": prompt}
            ))
            return "No relevant information found in the document for your query.", steps
        
        # Group contexts by level
        level_groups = {}
        for ctx in contexts:
            level = ctx["level"]
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(ctx)
        
        steps.append(ExecutionStep(
            id=2, type="retrieve",
            text=f"Retrieved {len(contexts)} relevant nodes from {len(level_groups)} tree levels",
            details={
                "total_contexts": len(contexts),
                "levels_used": sorted(level_groups.keys()),
                "top_similarities": [f"{ctx['similarity']:.3f}" for ctx in contexts[:3]],
            }
        ))
        
        # Build hierarchical context text
        context_parts = []
        for level in sorted(level_groups.keys(), reverse=True):  # Start from highest level (most abstract)
            level_contexts = level_groups[level]
            context_parts.append(f"=== Level {level} Context (Abstraction Level) ===")
            for ctx in level_contexts:
                context_parts.append(ctx["text"])
                context_parts.append("")
        
        context_text = "\n".join(context_parts)
        
        steps.append(ExecutionStep(
            id=3, type="reason",
            text=f"Synthesizing answer from hierarchical context ({len(context_text)} chars)",
            details={"context_length": len(context_text)}
        ))
        
        # Synthesize answer using hierarchical context
        synthesize_prompt = f"""Answer the following question using the provided hierarchical context from a document.
The context is organized from high-level summaries to specific details.

Question: {prompt}

Hierarchical Context:
{context_text}

Provide a comprehensive answer based on the context above:"""
        
        raw = await ollama_client.generate(
            prompt=synthesize_prompt,
            model=model,
            system="You are a helpful assistant that answers questions using hierarchical document context.",
        )
        final_answer = raw.get("response", "")
        
        steps.append(ExecutionStep(
            id=4, type="resolve",
            text="Generated answer using RAPTOR hierarchical retrieval",
            details={"levels_used": sorted(level_groups.keys()), "contexts_used": len(contexts)}
        ))
        
        return final_answer, steps
        
    except Exception as e:
        logger.error(f"RAPTOR pipeline error: {e}")
        steps.append(ExecutionStep(
            id=2, type="retrieve",
            text=f"Error in RAPTOR retrieval: {str(e)}",
            details={"error": str(e)}
        ))
        return f"Error during RAPTOR retrieval: {str(e)}", steps


async def _run_rlm_pipeline(
    prompt: str,
    model: str,
    neo4j_client,
) -> tuple[str, list[ExecutionStep]]:
    """
    Run the Recursive Language Model (RLM) pipeline:
    1. Decompose the query into sub-questions
    2. Retrieve relevant entities from Neo4j for each sub-question
    3. Synthesize a final answer using the retrieved context
    Returns (answer, trace_steps).
    """
    steps = []

    # Step 1: Decompose the query
    decompose_prompt = f"""Given the following complex research question, break it down into 2-4 simpler sub-questions that can be answered independently.
Return ONLY a JSON array of sub-questions, nothing else.

Research question: {prompt}

Output format:
["sub-question 1", "sub-question 2", "sub-question 3"]"""

    try:
        raw = await ollama_client.generate(
            prompt=decompose_prompt,
            model=model,
            system="You are a helpful assistant that breaks down complex questions.",
        )
        response_text = raw.get("response", "")

        # Try to parse sub-questions from LLM response
        sub_questions = _extract_sub_questions(response_text)
    except Exception as e:
        sub_questions = [prompt]  # Fallback: treat as single question
        steps.append(ExecutionStep(
            id=1, type="split",
            text=f"Analyzed the query (fallback to single question due to error: {e})",
            details={"error": str(e)}
        ))

    if not steps:  # If no error, add successful decomposition step
        steps.append(ExecutionStep(
            id=1, type="split",
            text=f"Analyzed the complex query into {len(sub_questions)} sub-question(s).",
            details={"sub_questions": sub_questions}
        ))

    # Step 2 & 3: For each sub-question, retrieve entities and synthesize
    all_context = []
    retrieved_entities = []

    for i, sq in enumerate(sub_questions, start=2):
        # Retrieve relevant entities from Neo4j
        try:
            graph_data = await neo4j_client.search_entities(sq)
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            if nodes:
                entity_names = [n.get("id", "") for n in nodes[:5]]  # Top 5
                retrieved_entities.extend(entity_names)

                context = f"Sub-question: {sq}\n"
                context += "Relevant entities:\n"
                for n in nodes[:5]:
                    context += f"- {n.get('id')} ({n.get('label', 'UNKNOWN')})\n"
                if edges:
                    context += "Relations:\n"
                    for e in edges[:5]:
                        context += f"- {e.get('source')} --[{e.get('relation')}]--> {e.get('target')}\n"
                all_context.append(context)

                steps.append(ExecutionStep(
                    id=i, type="retrieve",
                    text=f"Retrieved {len(nodes)} entities for: {sq[:50]}...",
                    details={"sub_question": sq, "entities": entity_names, "node_count": len(nodes)}
                ))
            else:
                # No entities found - still try to answer from general knowledge
                steps.append(ExecutionStep(
                    id=i, type="retrieve",
                    text=f"No graph entities found for: {sq[:50]}...",
                    details={"sub_question": sq, "entities": []}
                ))
        except Exception as e:
            steps.append(ExecutionStep(
                id=i, type="retrieve",
                text=f"Error retrieving for: {sq[:50]}... ({e})",
                details={"sub_question": sq, "error": str(e)}
            ))

    # Step 4: Synthesize final answer
    if all_context:
        context_text = "\n---\n".join(all_context)
        synthesize_prompt = f"""Based on the following retrieved knowledge graph context, answer the research question.

        Research question: {prompt}

        Knowledge graph context:
        {context_text}

        Provide a clear, direct answer to the research question based on the context above.
        """
    else:
        synthesize_prompt = f"""
        Answer the following research question. If you don't have specific context, provide a general answer based on your knowledge.

        Research question: {prompt}
        """

    try:
        raw = await ollama_client.generate(
            prompt=synthesize_prompt,
            model=model,
            system="You are a helpful research assistant.",
        )
        final_answer = raw.get("response", "")
    except Exception as e:
        final_answer = f"Error generating answer: {e}"

    steps.append(ExecutionStep(
        id=len(steps)+1, type="resolve",
        text="Generated final grounded answer utilizing multi-hop reasoning.",
        details={"context_used": len(all_context), "sub_questions_answered": len(sub_questions)}
    ))

    return final_answer, steps


def _extract_sub_questions(text: str) -> list[str]:
    """Extract sub-questions from LLM response."""
    import re

    # Try to find JSON array
    try:
        # Find [...] pattern
        match = re.search(r'\[([^\]]+)\]', text)
        if match:
            # Parse the array content
            content = match.group(1)
            # Extract quoted strings
            questions = re.findall(r'"([^"]+)"', content)
            if questions:
                return questions
    except Exception:
        pass

    # Fallback: split by newlines or numbered list
    lines = text.split('\n')
    questions = []
    for line in lines:
        line = line.strip()
        # Remove numbering like "1.", "2.", "-", etc.
        line = re.sub(r'^[\d\.\-\*]+\s*', '', line)
        if line and len(line) > 10:  # Reasonable question length
            questions.append(line)

    # If still nothing, treat entire response as one question
    if not questions:
        questions = [text.strip()]

    return questions[:4]  # Max 4 sub-questions


@router.post("", response_model=InferenceResponse, summary="Run inference with optional RLM pipeline")
async def run_inference(body: InferenceRequest = Body(...)) -> InferenceResponse:
    """
    Sends a prompt to the requested Ollama model and returns a synthesised answer
    plus generation metrics (tokens, latency).

    For 'Recursive RLM (Decomp)' and 'Graph Traversal' strategies, uses the
    RLM pipeline to decompose query, retrieve from graph, and synthesize.
    """
    t0 = time.perf_counter()

    # Check if we should use RLM pipeline
    use_rlm = body.strategy in ("Recursive RLM (Decomp)", "Graph Traversal")

    # Import neo4j_client here to avoid circular imports
    from app.services.neo4j_client import neo4j_client

    trace = []

    if use_rlm:
        # Use RLM pipeline
        answer, trace = await _run_rlm_pipeline(
            prompt=body.prompt,
            model=body.model,
            neo4j_client=neo4j_client,
        )
        # RLM pipeline already measures its own latency internally
        # Use a rough estimate based on sub-questions
        latency = time.perf_counter() - t0
        eval_count = len(trace) * 50  # Rough estimate
    elif body.strategy == "RAPTOR (Hierarchical)":
        # Use RAPTOR hierarchical retrieval
        # Use document name from request, fallback to "default"
        doc_name = body.document or "default"
        answer, trace = await _run_raptor_pipeline(
            prompt=body.prompt,
            model=body.model,
            document_name=doc_name,
        )
        latency = time.perf_counter() - t0
        eval_count = len(trace) * 50  # Rough estimate
    else:
        # Standard inference (original behavior)
        # Apply prompt template
        formatted_prompt, auto_system = apply_template(body.prompt_template, body.prompt)
        resolved_system = body.system or auto_system

        try:
            raw = await ollama_client.generate(
                prompt=formatted_prompt,
                model=body.model,
                system=resolved_system,
            )
            answer = raw.get("response", "")
            eval_count = raw.get("eval_count")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Ollama error: {exc}") from exc

        latency = time.perf_counter() - t0

    return InferenceResponse(
        answer=answer,
        metrics=InferenceMetrics(
            model=body.model,
            strategy=body.strategy,
            eval_count=eval_count,
            eval_duration=None,
            latency_s=round(latency, 3),
        ),
        trace=trace,
    )
