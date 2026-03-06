import React from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { GRAPH_DATA } from '../../data/constants';

// Node colour by group
const nodeColor = (node) => {
    const palette = { 1: '#3b82f6', 2: '#10b981', 3: '#f43f5e' };
    return palette[node.group] ?? '#94a3b8';
};

/**
 * GraphView — tab "Knowledge Graph Space".
 * Hiển thị đồ thị tri thức dùng physics-based force layout.
 */
const GraphView = () => (
    <div className="h-full rounded-2xl bg-slate-900/50 border border-slate-800 shadow-xl
                  overflow-hidden relative animate-in fade-in duration-500 flex flex-col">

        {/* Info overlay */}
        <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur
                    border border-slate-700 p-4 rounded-xl max-w-sm">
            <h3 className="text-white font-heading mb-1 text-sm font-semibold">Knowledge Topology</h3>
            <p className="text-xs text-slate-400">
                Interactive visualization of the retrieved logical network.
                Using physics-based force layout to map entities.
            </p>
        </div>

        {/* Force graph canvas */}
        <div className="flex-1 relative cursor-crosshair">
            <ForceGraph2D
                graphData={GRAPH_DATA}
                nodeLabel="name"
                nodeColor={nodeColor}
                nodeRelSize={6}
                linkColor={() => 'rgba(71, 85, 105, 0.4)'}
                linkWidth={1.5}
                backgroundColor="transparent"
            />
        </div>
    </div>
);

export default GraphView;
