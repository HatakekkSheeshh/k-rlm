import React from 'react';
import { Brain } from 'lucide-react';
import { Cpu, GitPullRequest, Database } from 'lucide-react';
import { Beaker, Network, Activity, MessageSquare } from 'lucide-react';
import SelectField from '../ui/SelectField';

const NAV_ITEMS = [
    { id: 'playground', label: 'Inference Playground', icon: Beaker, activeClass: 'bg-blue-600/10 text-blue-400' },
    { id: 'graph', label: 'Knowledge Graph Space', icon: Network, activeClass: 'bg-indigo-600/10 text-indigo-400' },
    { id: 'eval', label: 'Experiment Evaluation', icon: Activity, activeClass: 'bg-emerald-600/10 text-emerald-400' },
    { id: 'chat-test', label: 'Chat Test (Debug)', icon: MessageSquare, activeClass: 'bg-rose-600/10 text-rose-400' }
];

const Sidebar = ({
    activeTab, onTabChange,
    selectedModel, onModelChange, modelOptions,
    selectedStrategy, onStrategyChange, strategyOptions,
    selectedDataset, onDatasetChange, datasetOptions,
}) => (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl flex flex-col z-10 shrink-0">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg">
                <Brain size={24} />
            </div>
            <div>
                <h1 className="text-slate-100 font-heading font-semibold text-lg tracking-tight">K-RLM Archictecture</h1>
                <p className="text-xs text-slate-500">Research Platform v0.1</p>
            </div>
        </div>

        <nav className="p-4 space-y-2 flex-1">
            <div className="px-2 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Views</div>
            {NAV_ITEMS.map(({ id, label, icon, activeClass }) => {
                const NavIcon = icon;
                return (
                    <button
                        key={id} onClick={() => onTabChange(id)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                        ${activeTab === id ? activeClass : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200'}`}
                    >
                        <NavIcon size={18} /><span className="font-medium text-sm">{label}</span>
                    </button>
                );
            })}

            <div className="px-2 pt-6 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Experiment Config</div>
            <div className="space-y-4 px-1">
                <SelectField label="SLM" icon={Cpu} value={selectedModel} options={modelOptions} onChange={onModelChange} />
                <SelectField label="Reasoning Strategy" icon={GitPullRequest} value={selectedStrategy} options={strategyOptions} onChange={onStrategyChange} />
                <SelectField label="Base Dataset" icon={Database} value={selectedDataset} options={datasetOptions} onChange={onDatasetChange} />
            </div>
        </nav>

        <div className="p-4 border-t border-slate-800 bg-slate-950/30">
            <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />Engine Online
                </span>
                <span>0 ms ping</span>
            </div>
        </div>
    </aside>
);

export default Sidebar;
