import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Loader2,
  Code,
  Terminal,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { PlotlyChart } from './PlotlyChart';

interface ChatAssistantProps {
  datasetId: string;
}

const DEFAULT_SUGGESTIONS = [
  'What is the mean MonthlyCharges for churned vs non-churned customers?',
  'Plot a box plot of tenure by Contract type.',
  'Which payment method has the highest churn rate?',
  'Run a t-test to check if monthly charges differ significantly by churn.',
];

export const ChatAssistant: React.FC<ChatAssistantProps> = ({ datasetId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedCodes, setExpandedCodes] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const toggleCode = (msgId: string) => {
    setExpandedCodes((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const historyPayload = messages.slice(-4).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.sendChatMessage(datasetId, query.trim(), historyPayload);

      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        code_executed: res.code_executed,
        stdout: res.stdout,
        figure: res.figure,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `Error executing query: ${err.response?.data?.detail || err.message}`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-5 py-3.5 rounded-full bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-xs sm:text-sm shadow-2xl shadow-indigo-600/40 border border-indigo-400/30 transition-all hover:scale-105"
        >
          <Sparkles className="w-4 h-4 text-cyan-300 animate-pulse" />
          <span>Ask Follow-Up Question</span>
        </button>
      )}

      {/* Slide-in Chat Drawer / Modal */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-full max-w-lg h-[620px] max-h-[85vh] bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl animate-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                  <span>Conversational Analytics</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                </h3>
                <p className="text-[10px] text-slate-400">
                  Ad-hoc Python code execution in isolated sandbox
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages Thread */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 font-sans text-xs">
            {messages.length === 0 ? (
              <div className="text-center py-8 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-indigo-950/60 border border-indigo-800/80 flex items-center justify-center text-indigo-400 mx-auto">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-bold text-slate-200 text-sm">Ask Anything About Your Data</h4>
                  <p className="text-xs text-slate-400 max-w-xs mx-auto">
                    Drill into specific segments, run hypothesis tests, or generate custom charts on the fly.
                  </p>
                </div>

                {/* Suggestions */}
                <div className="pt-2 flex flex-col gap-1.5 text-left">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                    Suggested queries:
                  </span>
                  {DEFAULT_SUGGESTIONS.map((sug, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(sug)}
                      className="p-2 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-slate-300 text-xs transition text-left"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col space-y-2 ${
                    m.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-md'
                        : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none shadow-md'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{m.content}</div>

                    {/* Dynamic Plotly Chart in Chat */}
                    {m.figure && (
                      <div className="mt-3 pt-3 border-t border-slate-800 w-full min-w-[280px]">
                        <PlotlyChart
                          spec={{
                            id: `chat_chart_${m.id}`,
                            title: m.figure.layout?.title?.text || 'Follow-Up Visualization',
                            chart_type: 'chart',
                            description: 'Rendered from follow-up query',
                            figure: m.figure,
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Collapsible Sandbox Code Drawer */}
                  {m.code_executed && (
                    <div className="max-w-[85%] w-full rounded-xl border border-slate-800 bg-slate-950 text-slate-400 font-mono text-[10px] overflow-hidden">
                      <button
                        onClick={() => toggleCode(m.id)}
                        className="w-full flex items-center justify-between p-2 bg-slate-900/60 hover:bg-slate-900 transition text-slate-300 font-medium"
                      >
                        <span className="flex items-center gap-1.5">
                          <Code className="w-3 h-3 text-indigo-400" />
                          Executed Sandbox Python
                        </span>
                        {expandedCodes[m.id] ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )}
                      </button>

                      {expandedCodes[m.id] && (
                        <div className="p-3 border-t border-slate-800 space-y-2 bg-slate-950">
                          <pre className="overflow-x-auto text-slate-300 leading-normal">
                            <code>{m.code_executed}</code>
                          </pre>
                          {m.stdout && (
                            <div className="pt-2 border-t border-slate-800/80">
                              <span className="text-slate-500 uppercase tracking-wider block mb-1">
                                Output:
                              </span>
                              <pre className="text-emerald-400">{m.stdout}</pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}

            {loading && (
              <div className="flex items-center gap-2 text-slate-400 p-3 bg-slate-950 rounded-2xl border border-slate-800 max-w-[70%]">
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                <span className="text-xs">Computing in sandbox worker...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
              placeholder="Ask a question or request a calculation..."
              disabled={loading}
              className="flex-1 bg-slate-900 border border-slate-800 focus:border-indigo-500 px-3.5 py-2.5 rounded-xl text-xs text-white placeholder:text-slate-500 outline-none transition"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition flex-shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
