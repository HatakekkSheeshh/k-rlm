import React, { useState, useEffect } from 'react';
import { Send, User, Bot, AlertTriangle, ChevronDown } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const ChatTestView = ({ selectedModel }) => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);
    const [templates, setTemplates] = useState([{ id: 'raw', label: 'Raw (No Template)' }]);
    const [selectedTemplate, setSelectedTemplate] = useState('raw');

    // Fetch template list once on mount
    useEffect(() => {
        fetch(`${API_BASE_URL}/templates`)
            .then(r => r.json())
            .then(data => {
                setTemplates(data);
            })
            .catch(() => {/* backend chưa có, giữ mặc định raw */ });
    }, []);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);
        setErrorMsg(null);

        try {
            const response = await fetch(`${API_BASE_URL}/inference`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: userMsg.content,
                    model: selectedModel,
                    strategy: 'Standard RAG',
                    prompt_template: selectedTemplate,
                })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();

            setMessages((prev) => [...prev, {
                role: 'bot',
                content: data.answer,
                time: `${data.metrics.latency_s}s`
            }]);
        } catch (error) {
            console.error(error);
            setErrorMsg(error.message || 'Lỗi kết nối tới backend.');
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="flex flex-col h-full animate-in fade-in duration-500">
            {/* Header */}
            <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                    <h2 className="text-xl font-heading text-white font-medium">SLM Chat Tester</h2>
                    <p className="text-slate-400 text-sm">
                        Chat with <strong>{selectedModel}</strong> · select a prompt template below.
                    </p>
                </div>

                {/* Template selector */}
                <div className="flex flex-col gap-1 shrink-0">
                    <label className="text-xs text-slate-500 font-medium flex items-center gap-1">
                        <ChevronDown size={12} /> Prompt Template
                    </label>
                    <select
                        value={selectedTemplate}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                        className="bg-slate-900 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5
                                   focus:ring-1 focus:ring-blue-500 outline-none cursor-pointer min-w-[220px]"
                    >
                        {templates.map(t => (
                            <option key={t.id} value={t.id}>{t.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Chat area */}
            <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">

                {/* Messages Container */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500">
                            <Bot size={48} className="mb-4 opacity-50" />
                            <p>Send a message to start testing {selectedModel}...</p>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-emerald-600'}`}>
                                    {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                                </div>
                                <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-blue-600/20 text-blue-100 rounded-tr-sm' : 'bg-slate-800 text-slate-200 rounded-tl-sm'}`}>
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                    {msg.time && (
                                        <div className="mt-2 text-xs text-slate-500 text-right font-mono">
                                            {msg.time} latency
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}

                    {isTyping && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
                                <Bot size={16} className="text-white" />
                            </div>
                            <div className="bg-slate-800 rounded-2xl p-4 rounded-tl-sm text-slate-400 flex py-5 items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" />
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-75" />
                                <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce delay-150" />
                            </div>
                        </div>
                    )}

                    {errorMsg && (
                        <div className="flex gap-4 items-center p-4 bg-red-950/50 border border-red-900 rounded-xl text-red-400">
                            <AlertTriangle size={20} />
                            <span>{errorMsg}</span>
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-slate-800 bg-slate-950/50">
                    <form onSubmit={handleSend} className="relative flex items-end">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend(e);
                                }
                            }}
                            placeholder={`Message ${selectedModel}...\n`}
                            disabled={isTyping}
                            rows={3}
                            className="w-full bg-slate-900 border border-slate-700 text-slate-200 p-4 rounded-xl pr-14 focus:ring-2 focus:ring-blue-500 outline-none transition-all disabled:opacity-50 resize-y min-h-[56px] max-h-64"
                        />
                        <button
                            type="submit"
                            disabled={isTyping || !input.trim()}
                            className="absolute right-3 bottom-3 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 disabled:bg-slate-700 transition-colors"
                        >
                            <Send size={18} />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ChatTestView;
