import React from 'react';
import { Brain } from 'lucide-react';
import { Cpu, GitPullRequest, Database } from 'lucide-react';
import { Beaker, Network, Activity } from 'lucide-react';
import SelectField from '../ui/SelectField';

// ─── Navigation item config ───────────────────────────────────────────────────
const NAV_ITEMS = [
    {
        id: 'playground',
        label: 'Inference Playground',
        Icon: Beaker,
        activeClass: 'bg-blue-600/10 text-blue-400',
    },
    {
        id: 'graph',
        label: 'Knowledge Graph Space',
        Icon: Network,
        activeClass: 'bg-indigo-600/10 text-indigo-400',
    },
    {
        id: 'eval',
        label: 'Experiment Evaluation',
        Icon: Activity,
        activeClass: 'bg-emerald-600/10 text-emerald-400',
    },
];

/**
 * Sidebar — thanh điều hướng trái + cấu hình experiment.
 *
 * Props:
 *   activeTab         {string}
 *   onTabChange       {(tab: string) => void}
 *   selectedModel     {string}
 *   onModelChange     {(v: string) => void}
 *   modelOptions      {string[]}
 *   selectedStrategy  {string}
 *   onStrategyChange  {(v: string) => void}
 *   strategyOptions   {string[]}
 *   selectedDataset   {string}
 *   onDatasetChange   {(v: string) => void}
 *   datasetOptions    {string[]}
 */
const Sidebar = ({
    activeTab,
    onTabChange,
    selectedModel, onModelChange, modelOptions,
    selectedStrategy, onStrategyChange, strategyOptions,
    selectedDataset, onDatasetChange, datasetOptions,
}) => (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl flex flex-col z-10 shrink-0">

        {/* Brand / Logo */}
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg">
                <Brain size={24} />
            </div>
            <div>
                <h1 className="text-slate-100 font-heading font-semibold text-lg tracking-tight">
                    K-RLM Archictecture
                </h1>
                <p className="text-xs text-slate-500">Research Platform v0.1</p>
            </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2 flex-1">
            <div className="px-2 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Views
            </div>

            {NAV_ITEMS.map(({ id, label, Icon, activeClass }) => (
                <button
                    key={id}
                    onClick={() => onTabChange(id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                      ${activeTab === id
                            ? activeClass
                            : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200'}`}
                >
                    <Icon size={18} />
                    <span className="font-medium text-sm">{label}</span>
                </button>
            ))}

            {/* Experiment configuration section */}
            <div className="px-2 pt-6 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Experiment Config
            </div>

            <div className="space-y-4 px-1">
                <SelectField
                    label="Architecture Layer"
                    icon={Cpu}
                    value={selectedModel}
                    options={modelOptions}
                    onChange={onModelChange}
                />
                <SelectField
                    label="Reasoning Strategy"
                    icon={GitPullRequest}
                    value={selectedStrategy}
                    options={strategyOptions}
                    onChange={onStrategyChange}
                />
                <SelectField
                    label="Base Dataset"
                    icon={Database}
                    value={selectedDataset}
                    options={datasetOptions}
                    onChange={onDatasetChange}
                />
            </div>
        </nav>

        {/* Status footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/30">
            <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    Engine Online
                </span>
                <span>0 ms ping</span>
            </div>
        </div>
    </aside>
);

export default Sidebar;
