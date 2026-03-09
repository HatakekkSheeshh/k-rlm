import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import TopHeader from './components/layout/TopHeader';
import PlaygroundView from './components/views/PlaygroundView';
import GraphView from './components/views/GraphView';
import EvalView from './components/views/EvalView';
import ChatTestView from './components/views/ChatTestView';
import { STRATEGIES, DATASETS, fetchModels } from './data/constants';

export default function App() {
  const [activeTab, setActiveTab] = useState('playground');
  const [modelsList, setModelsList] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState(STRATEGIES[1]);
  const [selectedDataset, setSelectedDataset] = useState(DATASETS[0]);

  React.useEffect(() => {
    async function loadModels() {
      try {
        const models = await fetchModels();
        setModelsList(models);
        if (models && models.length > 0) {
          setSelectedModel(models[0].tag ?? models[0].label ?? models[0]);
        }
      } catch (e) {
        console.error("Failed to fetch models", e);
      }
    }
    loadModels();
  }, []);

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
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedModel={selectedModel} onModelChange={setSelectedModel} modelOptions={modelsList}
        selectedStrategy={selectedStrategy} onStrategyChange={setSelectedStrategy} strategyOptions={STRATEGIES}
        selectedDataset={selectedDataset} onDatasetChange={setSelectedDataset} datasetOptions={DATASETS}
      />
      <main className="flex-1 flex flex-col relative">
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
