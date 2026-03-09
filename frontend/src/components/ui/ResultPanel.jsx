import React from 'react';
import { Zap } from 'lucide-react';

const ResultPanel = ({ result }) => (
    <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-900/50 shadow-xl shadow-emerald-900/10 animate-in slide-in-from-bottom-4 fade-in duration-500 flex-1">
        <div className="flex items-center gap-2 mb-4">
            <div className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-md"><Zap size={16} /></div>
            <h3 className="text-emerald-400 font-heading font-medium">Final Synthesized Answer</h3>
        </div>
        <p className="text-slate-300 leading-relaxed font-body">{result.answer}</p>
        <div className="mt-6 pt-4 border-t border-slate-800 grid grid-cols-4 gap-4 text-center text-sm">
            {[
                { label: 'Latency', value: result.time },
                { label: 'Tokens Generated', value: result.tokens },
                { label: 'Graph Hops', value: result.hops },
                { label: 'Nodes Retrieved', value: result.nodesUsed },
            ].map(({ label, value }) => (
                <div key={label}>
                    <div className="text-slate-500 text-xs">{label}</div>
                    <div className="text-white font-mono mt-1">{value}</div>
                </div>
            ))}
        </div>
    </div>
);

export default ResultPanel;
