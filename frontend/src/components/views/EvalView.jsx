import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import StatCard from '../ui/StatCard';
import { PERFORMANCE_DATA } from '../../data/constants';

// ─── Summary metrics config ───────────────────────────────────────────────────
const SUMMARY_STATS = [
    { label: 'Platform Average Latency', value: '245', unit: 'ms', valueClass: 'text-white' },
    { label: 'Recursive Hallucination Rate', value: '0.8', unit: '%', valueClass: 'text-emerald-400' },
    { label: 'RLM F1 Score vs RAG', value: '+18.4', unit: '%', valueClass: 'text-white', highlight: true },
];

// Shared Tooltip style
const TOOLTIP_STYLE = {
    contentStyle: { backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#fff' },
    cursor: { fill: '#1e293b', opacity: 0.4 },
};

/**
 * EvalView — tab "Experiment Evaluation".
 * Hiển thị các số liệu tổng hợp và hai biểu đồ so sánh mô hình.
 */
const EvalView = () => (
    <div className="h-full animate-in fade-in duration-500 overflow-y-auto pb-10">

        {/* ── Summary stat cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {SUMMARY_STATS.map((stat) => (
                <StatCard key={stat.label} {...stat} />
            ))}
        </div>

        {/* ── Charts ── */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">

            {/* Bar chart: Precision vs Recall */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 h-[400px]">
                <h3 className="font-heading text-white mb-6">
                    Model Precision vs Recall (Strategy Impact)
                </h3>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={PERFORMANCE_DATA} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                        <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip {...TOOLTIP_STYLE} />
                        <Bar dataKey="precision" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="recall" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Radar chart: Inference Capabilities */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 h-[400px]">
                <h3 className="font-heading text-white mb-6">Inference Capabilities Area</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={PERFORMANCE_DATA}>
                        <PolarGrid stroke="#1e293b" />
                        <PolarAngleAxis dataKey="name" stroke="#64748b" fontSize={12} />
                        <PolarRadiusAxis stroke="#1e293b" />
                        <Radar
                            name="Latency"
                            dataKey="latency"
                            stroke="#f43f5e"
                            fill="#f43f5e"
                            fillOpacity={0.3}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </div>
    </div>
);

export default EvalView;
