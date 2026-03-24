import React, { useState, useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Upload, Loader2, FileCheck2, AlertCircle, Database, Users, Layers } from 'lucide-react';

const EMPTY_GRAPH = { nodes: [], links: [] };

const nodeColor = (node) => {
    const palette = {
        'PERSON': '#f43f5e',
        'ORGANIZATION': '#3b82f6',
        'LOCATION': '#10b981',
        'CONCEPT': '#8b5cf6',
        'DATE': '#eab308'
    };
    return palette[node.label?.toUpperCase()] ?? '#94a3b8';
};

const GraphView = () => {
    const [graphData, setGraphData] = useState(EMPTY_GRAPH);
    const [communities, setCommunities] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isBuildingRaptor, setIsBuildingRaptor] = useState(false);
    const [raptorStats, setRaptorStats] = useState(null);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState('');
    const [documentName, setDocumentName] = useState('');
    const [lastUploadedFile, setLastUploadedFile] = useState(null);
    const [isFetchingQdrant, setIsFetchingQdrant] = useState(false);
    const [maxBatches, setMaxBatches] = useState(0);
    const [enableSummarization, setEnableSummarization] = useState(false);
    const fileInputRef = useRef(null);
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

    const buildRaptorForFile = async (file, options = { updateSuccessMessage: true }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', 'phi3:mini');
        formData.append('chunk_size', 400);
        formData.append('max_levels', 3);

        const response = await fetch(`${API_BASE_URL}/graph/raptor/build`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `RAPTOR build failed: ${response.statusText}`);
        }

        const data = await response.json();
        setRaptorStats(data.stats);
        localStorage.setItem('krlm_raptor_ready_document', file.name);

        if (options.updateSuccessMessage) {
            setSuccessMsg(`✓ RAPTOR ready for ${file.name}: ${data.stats.levels} levels, ${data.stats.total_nodes} nodes`);
        }

        return data;
    };

    useEffect(() => {
        const loadGraphData = async () => {
            setIsLoading(true);
            try {
                const response = await fetch(`${API_BASE_URL}/graph/data`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.nodes && data.nodes.length > 0) {
                        const validNodeIds = new Set(data.nodes.map((n) => n.id));
                        setGraphData({
                            nodes: data.nodes.map((n) => ({ ...n, name: n.id })),
                            links: data.edges
                                .filter((e) => validNodeIds.has(e.source) && validNodeIds.has(e.target))
                                .map((e) => ({ ...e, source: e.source, target: e.target, name: e.relation })),
                        });
                    }
                }
            } catch (e) {
                console.error('Failed to load initial graph data', e);
            } finally {
                setIsLoading(false);
            }
        };

        loadGraphData();
        const lastDoc = localStorage.getItem('krlm_last_document');
        if (lastDoc) {
            setDocumentName(lastDoc);
        }
    }, [API_BASE_URL]);

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Store file for later RAPTOR building
        setLastUploadedFile(file);
        
        setDocumentName(file.name);
        localStorage.setItem('krlm_last_document', file.name);
        setIsUploading(true);
        setUploadProgress('');
        setError(null);
        setSuccessMsg('');
        setRaptorStats(null);
        localStorage.removeItem('krlm_raptor_ready_document');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', 'phi3:mini');
        formData.append('summarize', enableSummarization ? 'true' : 'false');
        formData.append('max_batches', maxBatches === '' ? 0 : maxBatches);

        try {
            setUploadProgress('📖 Extracting text from document...');
            
            const response = await fetch('http://localhost:8000/api/v1/graph/extract', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            setUploadProgress('🔍 Building knowledge graph...');
            const data = await response.json();
            
            if (data.graph && data.graph.nodes && data.graph.nodes.length > 0) {
                // Safely filter out hallucinated edges where source or target do not exist
                const validNodeIds = new Set(data.graph.nodes.map(n => n.id));
                const mappedData = {
                    nodes: data.graph.nodes.map(n => ({ ...n, name: n.id })), 
                    links: data.graph.edges
                        .filter(e => validNodeIds.has(e.source) && validNodeIds.has(e.target))
                        .map(e => ({ ...e, source: e.source, target: e.target, name: e.relation }))
                };
                setGraphData(mappedData);
                
                const msg = `✓ Extracted ${mappedData.nodes.length} entities and ${mappedData.links.length} relations from ${file.name}`;
                setSuccessMsg(enableSummarization ? `${msg} (Summarizing communities...)` : msg);
                
                if (data.community_summaries) {
                    setCommunities(data.community_summaries);
                } else {
                    setCommunities([]);
                }

                setUploadProgress('🌳 Building RAPTOR tree...');
                setIsBuildingRaptor(true);
                await buildRaptorForFile(file, { updateSuccessMessage: false });

                setSuccessMsg(`✓ Upload complete. RAPTOR tree is ready for ${file.name}. Go to Playground and query.`);
            } else {
                setGraphData(EMPTY_GRAPH);
                setError('No graph entities found in the document.');
            }
        } catch (err) {
            setGraphData(EMPTY_GRAPH);
            setError(err.message);
        } finally {
            setIsUploading(false);
            setIsBuildingRaptor(false);
            setUploadProgress('');
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleFetchQdrant = async () => {
        if (!documentName) {
            setError('Please upload a document first to fetch its communities.');
            return;
        }

        setIsFetchingQdrant(true);
        try {
            const response = await fetch(`${API_BASE_URL}/graph/communities?document=${encodeURIComponent(documentName)}`);
            if (!response.ok) {
                throw new Error('Failed to fetch Qdrant summaries');
            }
            const data = await response.json();
            if (data.communities) {
                setCommunities(data.communities);
                setSuccessMsg(`Fetched ${data.communities.length} community summaries from Qdrant.`);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsFetchingQdrant(false);
        }
    };

    const handleBuildRaptor = async () => {
        if (!lastUploadedFile) {
            setError('No document loaded. Please upload a file first.');
            return;
        }

        setIsBuildingRaptor(true);
        setError(null);

        try {
            await buildRaptorForFile(lastUploadedFile);
        } catch (err) {
            setError(`RAPTOR build failed: ${err.message}`);
        } finally {
            setIsBuildingRaptor(false);
        }
    };

    const hasData = graphData.nodes.length > 0;

    return (
        <div className="h-full flex flex-col gap-5 animate-in fade-in duration-500">
            
            {/* Top Bar: Controls */}
            <div className="flex items-center justify-between shrink-0 bg-slate-900/50 border border-slate-800 p-4 rounded-xl shadow-sm">
                <div className="flex flex-col">
                    <h3 className="text-white font-heading text-lg font-semibold flex items-center gap-2">
                        <Database className="w-5 h-5 text-blue-400" />
                        Knowledge Topology
                    </h3>
                    <p className="text-xs text-slate-400">Upload a document to extract and map its entities dynamically over the SLM.</p>
                </div>
                
                <div className="flex items-center gap-4">
                    {/* Feedback Messages & Progress */}
                    {isUploading && uploadProgress && (
                        <div className="text-xs text-blue-400 bg-blue-950/30 px-3 py-1.5 rounded-md border border-blue-900/50 flex items-center gap-2">
                            <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
                            <span>{uploadProgress}</span>
                        </div>
                    )}
                    {error && (
                        <div className="text-xs text-red-400 bg-red-950/30 px-3 py-1.5 rounded-md border border-red-900/50 flex items-center gap-2">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}
                    {successMsg && !error && (
                        <div className="text-xs text-emerald-400 bg-emerald-950/30 px-3 py-1.5 rounded-md border border-emerald-900/50 flex items-center gap-2">
                            <FileCheck2 className="w-3.5 h-3.5 shrink-0" />
                            <span>{successMsg}</span>
                        </div>
                    )}

                    <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*,.pdf,.doc,.docx,.txt" />
                    <button 
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 
                                  disabled:bg-blue-900/50 disabled:text-slate-500 text-white text-sm font-medium rounded-lg transition-colors ring-1 ring-inset ring-blue-500/20"
                    >
                        {isUploading ? (
                            <><Loader2 className="w-4 h-4 animate-spin shrink-0" /> Processing...</>
                        ) : (
                            <><Upload className="w-4 h-4 shrink-0" /> Upload Document</>
                        )}
                    </button>

                    {/* Options Group */}
                    <div className="flex items-center gap-3 pl-3 border-l border-slate-700">
                        {/* Summarization Toggle */}
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={enableSummarization}
                                onChange={(e) => setEnableSummarization(e.target.checked)}
                                disabled={isUploading}
                                className="w-4 h-4 rounded border-slate-600 text-blue-500 focus:ring-blue-500"
                            />
                            <span className="text-xs text-slate-400 whitespace-nowrap">
                                {enableSummarization ? '✓ Summarize' : 'Skip Summary'}
                            </span>
                        </label>

                        {/* Max Batches Limit */}
                        <div className="flex items-center gap-2">
                            <label className="text-xs text-slate-400">Max:</label>
                            <input
                                type="number"
                                min="0"
                                max="100000"
                                value={maxBatches}
                                onFocus={(e) => e.target.select()}
                                onChange={(e) => setMaxBatches(e.target.value === '' ? '' : Math.max(0, parseInt(e.target.value, 10) || 0))}
                                className="w-20 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white"
                            />
                            <span className="text-xs text-slate-500">(0 = all)</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content: Graph & Communities */}
            <div className="flex-1 flex gap-5 min-h-0">
                
                {/* Graph Canvas */}
                <div className="flex-1 rounded-2xl bg-slate-900/30 border border-slate-800 shadow-xl overflow-hidden relative flex flex-col">
                    {!hasData && !isUploading && !isLoading && (
                        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center text-slate-500 bg-slate-900/20 backdrop-blur-[2px]">
                            <Database className="w-12 h-12 mb-3 text-slate-700/50" />
                            <p className="text-sm font-medium">No knowledge graph extracted yet.</p>
                            <p className="text-xs text-slate-600 mt-1">Please upload a document to begin analysis.</p>
                        </div>
                    )}
                    {(isUploading || isLoading) && !hasData && (
                        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center text-slate-500 bg-slate-900/20 backdrop-blur-[2px]">
                            <Loader2 className="w-12 h-12 mb-3 text-blue-500/80 animate-spin" />
                            <p className="text-sm font-medium">Loading Topology Space...</p>
                        </div>
                    )}

                    <div className="flex-1 relative cursor-grab active:cursor-grabbing z-0">
                        <ForceGraph2D
                            graphData={graphData}
                            nodeLabel={(node) => node.label ? `${node.id} (${node.label})` : node.name}
                            nodeColor={nodeColor}
                            nodeRelSize={7}
                            linkColor={() => 'rgba(94, 114, 138, 0.5)'}
                            linkWidth={1.5}
                            backgroundColor="transparent"
                            onNodeDragEnd={node => { node.fx = node.x; node.fy = node.y; }}
                            onBackgroundClick={() => {
                                setGraphData(prev => {
                                    const newNodes = prev.nodes.map(n => ({ ...n, fx: null, fy: null }));
                                    return { ...prev, nodes: newNodes };
                                });
                            }}
                        />
                    </div>
                </div>

                {/* Right Bar: Qdrant Summarization & RAPTOR Tree */}
                <div className="w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl flex flex-col shrink-0 overflow-hidden">
                    {/* RAPTOR Tree Section */}
                    <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                        <h3 className="text-white font-heading text-base font-semibold flex items-center gap-2 shrink-0 mb-3">
                            <Layers className="w-4 h-4 text-purple-400" />
                            RAPTOR Hierarchy
                        </h3>
                        <button
                            onClick={handleBuildRaptor}
                            disabled={isBuildingRaptor || !documentName}
                            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 
                                       text-white text-xs font-semibold rounded-lg transition-colors border border-purple-500/30
                                       disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-purple-900/50 disabled:text-slate-400"
                        >
                            {isBuildingRaptor ? (
                                <><Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" /> Building Tree...</>
                            ) : raptorStats ? (
                                <><FileCheck2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" /> Tree Built</>
                            ) : (
                                <><Layers className="w-3.5 h-3.5 shrink-0" /> Build RAPTOR Tree</>
                            )}
                        </button>
                        {raptorStats && (
                            <div className="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-300 border border-slate-700/50 space-y-1">
                                <div>📊 Levels: <span className="text-purple-300 font-semibold">{raptorStats.levels}</span></div>
                                <div>🔗 Nodes: <span className="text-purple-300 font-semibold">{raptorStats.total_nodes}</span></div>
                            </div>
                        )}
                    </div>

                    {/* Qdrant Communities Section */}
                    <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex flex-col gap-3">
                        <h3 className="text-white font-heading text-base font-semibold flex items-center gap-2 shrink-0">
                            <Users className="w-4 h-4 text-emerald-400" />
                            Qdrant Communities
                        </h3>
                        <button
                            onClick={handleFetchQdrant}
                            disabled={isFetchingQdrant || !documentName}
                            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 
                                       text-slate-200 text-xs font-semibold rounded-lg transition-colors border border-slate-700
                                       disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isFetchingQdrant ? (
                                <><Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" /> Fetching from Qdrant...</>
                            ) : (
                                <><Database className="w-3.5 h-3.5 shrink-0" /> Pull Summaries</>
                            )}
                        </button>
                    </div>
                    
                    
                    {communities && communities.length > 0 ? (
                        <div className="flex-1 overflow-y-auto space-y-3 p-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                            {communities.map((c, idx) => (
                                <div key={idx} className="bg-slate-800/80 rounded-lg p-3.5 border border-slate-700/50 hover:border-slate-600 transition-colors">
                                    <div className="flex items-center justify-between mb-2.5">
                                        <span className="text-xs font-bold text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-900/60">
                                            ID: {c.community_id}
                                        </span>
                                        <span className="text-[10px] text-slate-400 font-medium">
                                            {c.node_count} nodes, {c.edge_count} edges
                                        </span>
                                    </div>
                                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                                        {c.summary || c.context || 'No summary available.'}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="flex-1 p-4 flex flex-col items-center justify-center text-center text-slate-500">
                            <Users className="w-8 h-8 opacity-20 mb-2" />
                            <p className="text-xs uppercase tracking-wider font-semibold">No Communities</p>
                            <p className="text-[11px] mt-1 leading-relaxed opacity-70">
                                Upload a document or fetch to load data.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GraphView;
