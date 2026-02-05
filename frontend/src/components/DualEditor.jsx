// 双模编辑器组件 - TipTap (Visual) + CodeMirror (Source)
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Mathematics from '@tiptap/extension-mathematics';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { oneDark } from '@codemirror/theme-one-dark';
import 'katex/dist/katex.min.css';
import { EditIcon, CodeIcon } from './Icons';

export default function DualEditor({
  content = '',
  onChange,
  onAutoSave,
  projectId
}) {
  const [mode, setMode] = useState('visual'); // 'visual' or 'source'
  const [markdownContent, setMarkdownContent] = useState(content);
  const [lastSaved, setLastSaved] = useState(new Date());
  const isSyncingRef = useRef(false);

  // TipTap 编辑器
  const editor = useEditor({
    extensions: [
      StarterKit,
      Mathematics,
    ],
    content: content,
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-full p-6 bg-[#1e1e1e] text-[#d4d4d4]',
      },
    },
    onUpdate: ({ editor }) => {
      if (isSyncingRef.current) {
        return;
      }
      const html = editor.getHTML();
      const md = htmlToMarkdown(html); // 简化转换
      setMarkdownContent(md);
      onChange?.(md);
    },
  });

  // 外部内容变化时同步
  useEffect(() => {
    if (content === markdownContent) {
      return;
    }
    setMarkdownContent(content);
    if (editor && mode === 'visual') {
      isSyncingRef.current = true;
      editor.commands.setContent(markdownToHtml(content || ''));
      isSyncingRef.current = false;
    }
  }, [content, editor, mode, markdownContent]);

  // 切换模式时同步内容
  useEffect(() => {
    if (mode === 'visual' && editor && markdownContent !== content) {
      editor.commands.setContent(markdownToHtml(markdownContent));
    }
  }, [mode, editor, markdownContent]);

  // CodeMirror 内容变化
  const handleCodeMirrorChange = useCallback((value) => {
    setMarkdownContent(value);
    onChange?.(value);
  }, [onChange]);

  // 自动保存
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onAutoSave && markdownContent) {
        onAutoSave(markdownContent);
        setLastSaved(new Date());
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [markdownContent, onAutoSave]);

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* 编辑器工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-[#3e3e42]">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('visual')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm transition-colors ${mode === 'visual'
                ? 'bg-[#37373d] text-white'
                : 'text-[#cccccc] hover:text-white hover:bg-[#2a2d2e]'
              }`}
          >
            <EditIcon className="w-3 h-3" />
            Visual
          </button>
          <button
            onClick={() => setMode('source')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm transition-colors ${mode === 'source'
                ? 'bg-[#37373d] text-white'
                : 'text-[#cccccc] hover:text-white hover:bg-[#2a2d2e]'
              }`}
          >
            <CodeIcon className="w-3 h-3" />
            Source
          </button>
        </div>

        <div className="text-xs text-[#858585]">
          Last saved: {formatTime(lastSaved)}
        </div>
      </div>

      {/* 编辑器内容区 */}
      <div className="flex-1 overflow-auto">
        {mode === 'visual' ? (
          <div className="h-full">
            <EditorContent
              editor={editor}
              className="h-full"
            />
          </div>
        ) : (
          <CodeMirror
            value={markdownContent}
            height="100%"
            theme={oneDark}
            extensions={[markdown()]}
            onChange={handleCodeMirrorChange}
            className="h-full text-sm"
            basicSetup={{
              lineNumbers: true,
              highlightActiveLineGutter: true,
              highlightSpecialChars: true,
              foldGutter: true,
              drawSelection: true,
              dropCursor: true,
              allowMultipleSelections: true,
              indentOnInput: true,
              bracketMatching: true,
              closeBrackets: true,
              autocompletion: true,
              rectangularSelection: true,
              crosshairCursor: true,
              highlightActiveLine: true,
              highlightSelectionMatches: true,
              closeBracketsKeymap: true,
              searchKeymap: true,
              foldKeymap: true,
              completionKeymap: true,
              lintKeymap: true,
            }}
          />
        )}
      </div>
    </div>
  );
}

// 简单的 HTML to Markdown 转换
function htmlToMarkdown(html) {
  let md = html
    .replace(/<h1>(.*?)<\/h1>/g, '# $1\n')
    .replace(/<h2>(.*?)<\/h2>/g, '## $1\n')
    .replace(/<h3>(.*?)<\/h3>/g, '### $1\n')
    .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
    .replace(/<em>(.*?)<\/em>/g, '*$1*')
    .replace(/<code>(.*?)<\/code>/g, '`$1`')
    .replace(/<p>(.*?)<\/p>/g, '$1\n\n')
    .replace(/<br\s*\/?>/g, '\n')
    .replace(/<[^>]+>/g, '');

  return md.trim();
}

// 简单的 Markdown to HTML 转换
function markdownToHtml(md) {
  return md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gim, '<p>$1</p>');
}

function formatTime(date) {
  const now = new Date();
  const diff = now - date;

  if (diff < 5000) return 'just now';
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  return date.toLocaleTimeString();
}
