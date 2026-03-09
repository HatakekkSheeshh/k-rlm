import React, { useState } from 'react';
import { Play, Map, Search } from 'lucide-react';
import ResultPanel from '../ui/ResultPanel';
import StepCard from '../ui/StepCard';
import { DECOMPOSITION_STEPS } from '../../data/constants';

const PlaygroundView = ({ selectedStrategy, selectedModel }) => {
    const [query, setQuery] = useState('');
    const [isInferencing, setIsInferencing] = useState(false);
    const [inferenceResult, setInferenceResult] = useState(null);
    const [traceSteps, setTraceSteps] = useState(null);
    const [errorMsg, setErrorMsg] = useState(null);

    const handleRunInference = async () => {
        if (!query) return;
        setIsInferencing(true);
        setInferenceResult(null);
        setTraceSteps(null);
        setErrorMsg(null);

        try {
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
            const response = await fetch(`${API_BASE_URL}/inference`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: query,
                    model: selectedModel,
                    strategy: selectedStrategy
                })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            const hasTrace = data.trace && data.trace.length > 0;

            let hops = 3;
            let nodesUsed = 4;
            if (hasTrace) {
                const retrieveSteps = data.trace.filter(t => t.type === 'retrieve');
                nodesUsed = retrieveSteps.reduce((sum, t) => sum + (t.details?.node_count || 0), 0);
                hops = retrieveSteps.length;
            }

            setInferenceResult({
                answer: data.answer,
                tokens: data.metrics.eval_count || 0,
                time: `${data.metrics.latency_s}s`,
                hops: hops,
                nodesUsed: nodesUsed
            });

            setTraceSteps(hasTrace ? data.trace : DECOMPOSITION_STEPS);
        } catch (error) {
            console.error(error);
            setErrorMsg(error.message || 'Failed to connect to backend.');
        } finally {
            setIsInferencing(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full animate-in fade-in duration-500">
            <div className="space-y-6 flex flex-col">
                <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl shadow-black/20 shrink-0">
                    <h2 className="text-xl font-heading text-white mb-2 font-medium">
                        Recursive Reasoning Console
                    </h2>
                    <p className="text-slate-400 text-sm mb-6">
                        Test the {selectedStrategy} algorithm using lightweight SLMs locally without cloud API latency.
                    </p>

                    <div className="relative">
                        <textarea
                            className="w-full h-32 bg-slate-950 border border-slate-800 text-slate-200 p-4
                         rounded-xl focus:ring-2 focus:ring-blue-500/50 outline-none resize-none transition-all"
                            placeholder="Enter a multi-hop research query..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button
                            onClick={handleRunInference}
                            disabled={isInferencing || !query}
                            className={`absolute bottom-4 right-4 p-2 rounded-lg flex items-center gap-2
                          text-sm font-semibold transition-all shadow-lg
                          ${isInferencing || !query
                                    ? 'bg-slate-800 text-slate-500 shadow-none'
                                    : 'bg-blue-600 text-white hover:bg-blue-500 shadow-blue-900/50 hover:-translate-y-0.5'}`}
                        >
                            {isInferencing
                                ? <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                : <Play size={16} />}
                            {isInferencing ? 'Reasoning...' : 'Execute'}
                        </button>
                    </div>
                </div>

                {errorMsg && (
                    <div className="p-4 rounded-xl bg-red-950/50 border border-red-900 text-red-400 text-sm">
                        {errorMsg}
                    </div>
                )}

                {inferenceResult && <ResultPanel result={inferenceResult} />}
            </div>

            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl shadow-black/20
                      flex flex-col h-full overflow-hidden">
                <h3 className="text-lg font-heading text-white mb-6 flex items-center gap-2 border-b border-slate-800 pb-4">
                    <Map size={18} className="text-blue-400" />
                    Trace: execution_graph
                </h3>

                {!isInferencing && !inferenceResult ? (
                    <div className="flex-1 flex flex-col items-center justify-center
                          text-slate-600 space-y-4 filter grayscale opacity-60">
                        <Search size={48} />
                        <p>Awaiting query input to trace reasoning steps...</p>
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto pr-2 space-y-0 relative mb-4
                          before:absolute before:inset-0 before:ml-[19px] before:w-px before:bg-slate-800">
                        {(traceSteps || DECOMPOSITION_STEPS).map((step, i) => (
                            <StepCard key={step.id || i} step={step} index={i} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default PlaygroundView;
