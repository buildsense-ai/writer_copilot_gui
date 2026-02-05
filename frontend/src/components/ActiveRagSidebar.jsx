// Active RAG 侧边栏 - 自动推荐相关内容
import React, { useState, useEffect } from 'react';
import { BrainIcon, SparklesIcon, LoadingIcon, MemoryIcon } from './Icons';

export default function ActiveRagSidebar({
  projectId,
  editorContent,
  onInsertContent,
  apiBase
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  const buildQuery = () => {
    const trimmed = (editorContent || '').trim();
    if (!trimmed) return '';
    return trimmed.slice(-500);
  };

  const triggerRecall = (force = false) => {
    const query = buildQuery();
    if (!query) return;
    if (!force && query === lastQuery) return;
    fetchSuggestions(query);
    setLastQuery(query);
  };

  // 监听编辑器内容变化，自动检索相关记忆
  useEffect(() => {
    // Debounce: 等待用户停止输入 2 秒后触发
    const timer = setTimeout(() => {
      const trimmed = (editorContent || '').trim();
      if (trimmed.length >= 10) {
        triggerRecall();
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [editorContent, lastQuery]);

  const fetchSuggestions = async (query) => {
    if (!projectId) return;

    setLoading(true);
    try {
      const response = await fetch(`${apiBase}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          project_id: projectId,
          top_k: 5
        })
      });

      const data = await response.json();
      setSuggestions(data.results || []);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInsert = (text) => {
    onInsertContent?.(text);
  };

  return (
    <div className="h-full flex flex-col bg-[#252526] border-l border-[#3e3e42]">
      {/* 标题栏 */}
      <div className="flex items-center gap-2 px-4 py-3 bg-[#2d2d30] border-b border-[#3e3e42] relative overflow-hidden">
        <SparklesIcon className="w-4 h-4 text-[#f9826c]" />
        <h3 className="text-sm font-medium text-[#cccccc]">Active Recall</h3>
        {loading && <LoadingIcon className="w-3 h-3 text-[#f9826c] animate-pulse" />}
        <button
          type="button"
          className="active-recall-button"
          onClick={() => triggerRecall(true)}
          disabled={loading}
        >
          Recall
        </button>
        {loading && <div className="active-recall-bar" />}
      </div>

      {/* 建议列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        {suggestions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <BrainIcon className="w-12 h-12 text-[#858585] mb-3" />
            <p className="text-sm text-[#858585] mb-1">
              Start writing...
            </p>
            <p className="text-xs text-[#6e6e6e]">
              Relevant content will appear here automatically
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <SuggestionCard
                key={index}
                suggestion={suggestion}
                onInsert={handleInsert}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SuggestionCard({ suggestion, onInsert }) {
  const [expanded, setExpanded] = useState(false);
  const { text, metadata, distance } = suggestion;

  // 计算相似度分数 (0-100)
  const similarityScore = Math.round((1 - distance) * 100);

  // 提取文本摘要 (前 100 字符)
  const summary = text.length > 100 ? text.substring(0, 100) + '...' : text;
  const full = text;

  return (
    <div className="group bg-[#2d2d30] hover:bg-[#37373d] rounded p-3 transition-colors cursor-pointer border border-transparent hover:border-[#007acc]">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <MemoryIcon className="w-3 h-3 text-[#4ec9b0] flex-shrink-0" />
          <span className="text-xs text-[#6e6e6e] truncate">
            {metadata?.source_file || 'Unknown Source'}
          </span>
        </div>
        <div className="flex-shrink-0">
          <span
            className={`text-xs px-1.5 py-0.5 rounded ${similarityScore > 80
              ? 'bg-green-900/30 text-green-400'
              : similarityScore > 60
                ? 'bg-blue-900/30 text-blue-400'
                : 'bg-gray-700/30 text-gray-400'
              }`}
          >
            {similarityScore}%
          </span>
        </div>
      </div>

      {metadata?.section && (
        <div className="text-xs text-[#858585] mb-2">
          {metadata.section}
        </div>
      )}

      <p className="text-sm text-[#cccccc] leading-relaxed">
        {expanded ? full : summary}
      </p>

      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#3e3e42]">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-xs text-[#007acc] hover:text-[#4daafc] transition-colors"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onInsert(text);
          }}
          className="ml-auto text-xs bg-[#0e639c] hover:bg-[#1177bb] text-white px-2 py-1 rounded transition-colors"
        >
          Insert
        </button>
      </div>
    </div>
  );
}
