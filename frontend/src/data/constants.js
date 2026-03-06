// ─── Static option lists ─────────────────────────────────────────────────────
// Each entry: { label → display name in UI, tag → Ollama model tag }
/* 
Microsoft
Google
Mistral AI
*/
export const MODELS = [
    { label: 'Phi-3 Mini', tag: 'phi3:mini' },
    { label: 'Gemma 7B', tag: 'gemma:7b' },
    { label: 'Mistral 7B v0.2', tag: 'mistral:7b-instruct-v0.2-q4_0' },
];

export const STRATEGIES = [
    'Standard RAG',
    'Graph Traversal',
    'Recursive RLM (Decomp)',
];

export const DATASETS = [
    'Medical (PubMed)',
    'Finance (SEC)',
    'General (Wiki)',
];

// ─── Knowledge graph mock data ────────────────────────────────────────────────
export const GRAPH_DATA = {
    nodes: [
        { id: '1', name: 'Machine Learning', group: 1, val: 5 },
        { id: '2', name: 'Neural Networks', group: 1, val: 3 },
        { id: '3', name: 'Transformers', group: 1, val: 4 },
        { id: '4', name: 'Knowledge Graph', group: 2, val: 5 },
        { id: '5', name: 'Entity Resolution', group: 2, val: 3 },
        { id: '6', name: 'Recursive Models', group: 3, val: 5 },
        { id: '7', name: 'RAG', group: 3, val: 4 },
    ],
    links: [
        { source: '1', target: '2' },
        { source: '2', target: '3' },
        { source: '4', target: '5' },
        { source: '6', target: '3' },
        { source: '6', target: '4' },
        { source: '7', target: '3' },
        { source: '7', target: '4' },
    ],
};

// ─── Evaluation benchmark data ────────────────────────────────────────────────
export const PERFORMANCE_DATA = [
    { name: 'Mistral (RLM)', precision: 89, recall: 90, latency: 380, cost: 0.10 },
    { name: 'Phi-3 (RAG)', precision: 75, recall: 72, latency: 150, cost: 0.04 },
    { name: 'Gemma (RAG)', precision: 78, recall: 76, latency: 180, cost: 0.05 },
];

// ─── Decomposition trace steps ────────────────────────────────────────────────
export const DECOMPOSITION_STEPS = [
    { id: 1, type: 'split', text: 'Analyze the complex query into 3 distinct sub-problems.' },
    { id: 2, type: 'retrieve', text: 'Retrieve graph nodes for Sub-problem A [Entity: Transformers].' },
    { id: 3, type: 'reason', text: 'Synthesize intermediate context from Sub-problem A & B.' },
    { id: 4, type: 'resolve', text: 'Generate final grounded answer utilizing multi-hop paths.' },
];
