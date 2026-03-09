import React from 'react';
import { Search, Brain, CheckCircle } from 'lucide-react';

const stepTypeConfig = {
    split: { color: 'text-purple-400', border: 'border-purple-900/30', icon: Brain },
    retrieve: { color: 'text-blue-400', border: 'border-blue-900/30', icon: Search },
    reason: { color: 'text-amber-400', border: 'border-amber-900/30', icon: Brain },
    resolve: { color: 'text-emerald-400', border: 'border-emerald-900/30', icon: CheckCircle },
};

const StepCard = ({ step, index }) => {
    const config = stepTypeConfig[step.type] || stepTypeConfig.split;
    const IconComponent = config.icon;

    return (
        <div className="flex gap-4 relative animate-in fade-in slide-in-from-right-4" style={{ animationDelay: `${index * 400}ms`, animationFillMode: 'both' }}>
            <div className={`w-10 h-10 rounded-full bg-slate-900 border-2 ${config.border} flex items-center justify-center text-xs font-mono shrink-0 z-10 ${config.color}`}>
                {index + 1}
            </div>
            <div className="pb-8 pt-1 flex-1">
                <div className={`p-4 rounded-xl bg-slate-950 border ${config.border} hover:${config.border} transition-colors`}>
                    <div className={`text-xs ${config.color} font-mono uppercase tracking-wider mb-2 flex items-center gap-2`}>
                        <IconComponent size={12} />OPERATION: {step.type}
                    </div>
                    <p className="text-slate-300 text-sm">{step.text}</p>
                    {step.details && Object.keys(step.details).length > 0 && (
                        <details className="mt-2 text-xs text-slate-500">
                            <summary className="cursor-pointer hover:text-slate-400">Details</summary>
                            <pre className="mt-1 p-2 bg-slate-900 rounded overflow-x-auto">{JSON.stringify(step.details, null, 2)}</pre>
                        </details>
                    )}
                </div>
            </div>
        </div>
    );
};

export default StepCard;
