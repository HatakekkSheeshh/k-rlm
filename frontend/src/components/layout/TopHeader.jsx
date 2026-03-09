import React from 'react';
import { Layers, Settings2 } from 'lucide-react';

const TAB_LABELS = { playground: 'Playground', graph: 'Graph Viz', eval: 'Evaluation', 'chat-test': 'SLM Chat Test' };

const TopHeader = ({ activeTab }) => (
    <header className="h-16 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md flex items-center justify-between px-8 z-10">
        <div className="flex items-center gap-2 text-sm text-slate-400">
            <Layers size={16} /><span>Experiment #424 / {TAB_LABELS[activeTab]}</span>
        </div>
        <div className="flex gap-3">
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors">
                <Settings2 size={18} />
            </button>
            <button className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm rounded-md transition-all font-medium border border-slate-700">
                Deploy Model
            </button>
        </div>
    </header>
);

export default TopHeader;
