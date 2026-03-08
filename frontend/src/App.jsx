import React, { useState } from 'react';

// ── Layout components ──────────────────────────────────────────────────────────
import Sidebar from './components/layout/Sidebar';
import TopHeader from './components/layout/TopHeader';

// ── View components ────────────────────────────────────────────────────────────
import PlaygroundView from './components/views/PlaygroundView';
import GraphView from './components/views/GraphView';
import EvalView from './components/views/EvalView';
import ChatTestView from './components/views/ChatTestView';

// ── Static data ────────────────────────────────────────────────────────────────
import { MODELS, STRATEGIES, DATASETS } from './data/constants';

/**
 * App — root component.
 *
 * Trách nhiệm duy nhất:
 *   - Quản lý tab đang hiển thị và experiment config (model / strategy / dataset)
 *   - Kết hợp Sidebar + TopHeader + View tương ứng
 *
 * Mọi UI detail đều được ủy thác xuống các component con.
 */
export default function App() {
  // ── Navigation state ────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState('playground');

  // ── Experiment config state ──────────────────────────────────────────────────
  const [selectedModel, setSelectedModel] = useState(MODELS[0].tag ?? MODELS[0]);
  const [selectedStrategy, setSelectedStrategy] = useState(STRATEGIES[2]);
  const [selectedDataset, setSelectedDataset] = useState(DATASETS[0]);

  // ── View router ──────────────────────────────────────────────────────────────
  const renderView = () => {
    switch (activeTab) {
      case 'playground': return <PlaygroundView selectedStrategy={selectedStrategy} selectedModel={selectedModel} />;
      case 'graph': return <GraphView />;
      case 'eval': return <EvalView />;
      case 'chat-test': return <ChatTestView selectedModel={selectedModel} />;
      default: return null;
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 font-body overflow-hidden selection:bg-blue-500/30">

      {/* ── Left: sidebar navigation + config ── */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedModel={selectedModel} onModelChange={setSelectedModel} modelOptions={MODELS}
        selectedStrategy={selectedStrategy} onStrategyChange={setSelectedStrategy} strategyOptions={STRATEGIES}
        selectedDataset={selectedDataset} onDatasetChange={setSelectedDataset} datasetOptions={DATASETS}
      />

      {/* ── Right: main content ── */}
      <main className="flex-1 flex flex-col relative">
        {/* Subtle background gradient */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(37,99,235,0.05),transparent_40%)] pointer-events-none" />

        <TopHeader activeTab={activeTab} />

        <div className="flex-1 overflow-y-auto p-8 z-10">
          <div className="max-w-6xl mx-auto h-full">
            {renderView()}
          </div>
        </div>
      </main>
    </div>
  );
}
