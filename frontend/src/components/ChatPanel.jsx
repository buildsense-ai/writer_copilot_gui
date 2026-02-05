// 聊天面板 - 支持流式响应和思维链展示
import React, { useState, useRef, useEffect } from 'react';
import { BrainIcon, LoadingIcon, MemoryIcon, SparklesIcon } from './Icons';

export default function ChatPanel({ projectId, apiBase, onOpenSource }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    try {
      const response = await fetch(`${apiBase}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          project_id: projectId,
          top_k: 5
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let assistantMessage = {
        role: 'assistant',
        content: '',
        reasoning: '',
        contexts: [],
        isStreaming: true,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));

              if (event.type === 'search') {
                assistantMessage.contexts = event.contexts || [];
              } else if (event.type === 'reasoning') {
                assistantMessage.reasoning += event.content;
              } else if (event.type === 'content_chunk') {
                assistantMessage.content += event.content;
              } else if (event.type === 'done') {
                assistantMessage.content = event.full_content || assistantMessage.content;
                assistantMessage.reasoning = event.reasoning_trace || assistantMessage.reasoning;
                assistantMessage.isStreaming = false;
              }

              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = { ...assistantMessage };
                return newMessages;
              });
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to get response. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* 聊天标题栏 */}
      <div className="flex items-center gap-2 px-4 py-3 bg-[#252526] border-b border-[#3e3e42]">
        <BrainIcon className="w-4 h-4 text-[#4ec9b0]" />
        <h3 className="text-sm font-medium text-[#cccccc]">AI Assistant</h3>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <SparklesIcon className="w-16 h-16 text-[#858585] mb-4" />
            <p className="text-sm text-[#cccccc] mb-2">Ask me anything about your papers</p>
            <p className="text-xs text-[#6e6e6e]">
              I can help you understand, summarize, and find connections
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <Message key={index} message={msg} onOpenSource={onOpenSource} />
          ))
        )}
        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-[#858585]">
            <LoadingIcon className="w-3 h-3" />
            <span>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="p-4 bg-[#252526] border-t border-[#3e3e42]">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question..."
            disabled={isStreaming}
            className="flex-1 px-3 py-2 bg-[#3c3c3c] text-[#cccccc] rounded resize-none focus:outline-none focus:ring-1 focus:ring-[#007acc] placeholder-[#6e6e6e] disabled:opacity-50"
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="px-4 py-2 bg-[#0e639c] hover:bg-[#1177bb] text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function Message({ message, onOpenSource }) {
  const [showReasoning, setShowReasoning] = useState(false);
  const { role, content, reasoning, contexts, timestamp, isStreaming } = message;

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-[#0e639c] text-white rounded-lg px-4 py-2">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
          <span className="text-xs opacity-70 mt-1 block">
            {formatTime(timestamp)}
          </span>
        </div>
      </div>
    );
  }

  if (role === 'error') {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] bg-red-900/20 border border-red-800/50 text-red-300 rounded-lg px-4 py-2">
          <p className="text-sm">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] bg-[#2d2d30] text-[#cccccc] rounded-lg px-4 py-3">
        {/* 检索上下文 */}
        {contexts && contexts.length > 0 && (
          <div className="mb-3 pb-3 border-b border-[#3e3e42]">
            <div className="flex items-center gap-2 mb-2">
              <MemoryIcon className="w-3 h-3 text-[#4ec9b0]" />
              <span className="text-xs text-[#858585]">
                Found {contexts.length} relevant sources
              </span>
            </div>
          </div>
        )}

        {/* 思维链 */}
        {reasoning && (
          <div className="mb-3">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="text-xs text-[#007acc] hover:text-[#4daafc] transition-colors"
            >
              <span className="inline-flex items-center gap-2">
                {isStreaming && <LoadingIcon className="w-3 h-3" />}
                {showReasoning ? '▼ Hide thinking' : '▶ Show thinking'}
              </span>
            </button>
            {showReasoning && (
              <div className="mt-2 p-3 bg-[#1e1e1e] rounded text-xs text-[#858585] font-mono whitespace-pre-wrap">
                {reasoning}
              </div>
            )}
          </div>
        )}

        {/* 回复内容 */}
        <div className="prose prose-sm prose-invert max-w-none">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {parseReferences(content, contexts, onOpenSource)}
          </p>
        </div>

        <span className="text-xs text-[#6e6e6e] mt-2 block">
          {formatTime(timestamp)}
        </span>
      </div>
    </div>
  );
}

// 解析引用标注 [1], [2] 等
function parseReferences(text, contexts, onOpenSource) {
  if (!text) return '';

  const parts = [];
  const pattern = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match = null;

  while ((match = pattern.exec(text)) !== null) {
    const start = match.index;
    const end = pattern.lastIndex;
    const refNumber = Number(match[1]);
    const refIndex = refNumber - 1;

    if (start > lastIndex) {
      parts.push(text.slice(lastIndex, start));
    }

    const context = contexts?.[refIndex];
    if (context && onOpenSource) {
      parts.push(
        <button
          type="button"
          key={`ref-${refNumber}-${start}`}
          onClick={() => onOpenSource(context)}
          className="text-xs text-[#4daafc] underline hover:text-[#7cbcff] ml-0.5"
        >
          [{refNumber}]
        </button>
      );
    } else {
      parts.push(`[${refNumber}]`);
    }

    lastIndex = end;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

function formatTime(date) {
  if (!date) return '';
  return new Date(date).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
}
