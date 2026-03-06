import React from 'react';
import { FileCode2 } from 'lucide-react';

/**
 * StepCard — hiển thị một bước trong execution trace.
 *
 * Props:
 *   step  {{ id, type, text }} — dữ liệu bước
 *   index {number}             — chỉ số 0-based (dùng cho animation delay)
 */
const StepCard = ({ step, index }) => (
    <div
        className="flex gap-4 relative animate-in fade-in slide-in-from-right-4"
        style={{ animationDelay: `${index * 400}ms`, animationFillMode: 'both' }}
    >
        {/* Step number bubble */}
        <div className="w-10 h-10 rounded-full bg-slate-900 border-2 border-slate-700
                    flex items-center justify-center text-xs font-mono shrink-0 z-10 text-slate-400">
            {index + 1}
        </div>

        {/* Step content */}
        <div className="pb-8 pt-1 flex-1">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors">
                <div className="text-xs text-blue-400 font-mono uppercase tracking-wider mb-2 flex items-center gap-2">
                    <FileCode2 size={12} />
                    OPERATION: {step.type}
                </div>
                <p className="text-slate-300 text-sm">{step.text}</p>
            </div>
        </div>
    </div>
);

export default StepCard;
