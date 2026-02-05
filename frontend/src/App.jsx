import React, { useCallback, useEffect, useRef, useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import DualEditor from './components/DualEditor';
import ActiveRagSidebar from './components/ActiveRagSidebar';
import ChatPanel from './components/ChatPanel';
import PDFViewer from './components/PDFViewer';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

const API_BASE = window?.paperMem?.apiBase || 'http://127.0.0.1:8000';

export default function App() {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [files, setFiles] = useState([]);
  const [activeTab, setActiveTab] = useState('editor');
  const [editorContent, setEditorContent] = useState('');
  const [currentFilePath, setCurrentFilePath] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [fileStatus, setFileStatus] = useState('idle');
  const [pdfState, setPdfState] = useState(null);
  const [showTerminal, setShowTerminal] = useState(false);
  const [openMenu, setOpenMenu] = useState('');
  const lastSavedRef = useRef('');
  const isLoadingRef = useRef(false);
  const terminalContainerRef = useRef(null);
  const terminalRef = useRef(null);
  const fitAddonRef = useRef(null);
  const terminalIdRef = useRef(null);

  const fetchProjects = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json();
      setProjects(data);
      if (data.length > 0 && !currentProject) {
        setCurrentProject(data[0]);
        window.paperMem?.setActiveProjectId(data[0].id);
      }
    } catch (error) {
      alert('Failed to fetch projects');
    }
  }, [currentProject]);

  const fetchFiles = useCallback(async (projectId) => {
    if (!projectId) return;
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/files`);
      const data = await response.json();
      setFiles(data);
    } catch (error) {
      setFiles([]);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (!currentProject?.id) return;
    fetchFiles(currentProject.id);
    window.paperMem?.setActiveProjectId(currentProject.id);
  }, [currentProject, fetchFiles]);

  const loadDraft = useCallback(async (filePath) => {
    if (!filePath) return;
    const api = window.paperMem;
    if (!api?.readTextFile) return;
    isLoadingRef.current = true;
    setFileStatus('loading');
    const result = await api.readTextFile(filePath);
    if (result?.ok) {
      const content = result.content || '';
      lastSavedRef.current = content;
      setEditorContent(content);
      setFileStatus('idle');
    } else {
      if ((result?.error || '').includes('ENOENT')) {
        lastSavedRef.current = '';
        setEditorContent('');
        setFileStatus('idle');
      } else {
        setFileStatus('error');
      }
    }
    isLoadingRef.current = false;
  }, []);

  useEffect(() => {
    let active = true;
    const init = async () => {
      const api = window.paperMem;
      if (!api?.getDefaultProjectPath || !api?.getDefaultDraftPath) {
        return;
      }
      const [nextProjectPath, nextDraftPath] = await Promise.all([
        api.getDefaultProjectPath(),
        api.getDefaultDraftPath(),
      ]);
      if (!active) return;
      setProjectPath(nextProjectPath || '');
      setCurrentFilePath(nextDraftPath || '');
      if (nextDraftPath) {
        await loadDraft(nextDraftPath);
      }
      if (nextProjectPath) {
        await api.startWatching?.(nextProjectPath);
      }
    };
    init();
    return () => {
      active = false;
      window.paperMem?.stopWatching?.();
    };
  }, [loadDraft]);

  useEffect(() => {
    if (!showTerminal || terminalRef.current || !terminalContainerRef.current) {
      return;
    }

    const terminalApi = window?.paperMem?.terminalApi;
    if (!terminalApi) {
      return;
    }

    let active = true;
    let removeDataListener = null;
    let removeExitListener = null;
    let resizeHandler = null;

    const setupTerminal = async () => {
      const term = new Terminal({
        cursorBlink: true,
        fontSize: 12,
        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        theme: {
          background: '#1e1e1e',
          foreground: '#cccccc',
          cursor: '#cccccc',
          selectionBackground: 'rgba(204, 204, 204, 0.3)',
        },
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalContainerRef.current);
      fitAddon.fit();
      term.focus();

      const createResult = await terminalApi.create({
        cols: term.cols,
        rows: term.rows,
      });

      if (!active || !createResult?.id) {
        term.dispose();
        return;
      }

      terminalRef.current = term;
      fitAddonRef.current = fitAddon;
      terminalIdRef.current = createResult.id;

      removeDataListener = terminalApi.onData((payload) => {
        if (payload?.id === terminalIdRef.current) {
          term.write(payload.data);
        }
      });

      removeExitListener = terminalApi.onExit((payload) => {
        if (payload?.id === terminalIdRef.current) {
          terminalIdRef.current = null;
        }
      });

      term.onData((data) => {
        terminalApi.write(createResult.id, data);
      });

      resizeHandler = () => {
        if (!fitAddonRef.current || !terminalIdRef.current) {
          return;
        }
        fitAddonRef.current.fit();
        terminalApi.resize(terminalIdRef.current, term.cols, term.rows);
      };

      window.addEventListener('resize', resizeHandler);
    };

    setupTerminal();

    return () => {
      active = false;
      if (resizeHandler) {
        window.removeEventListener('resize', resizeHandler);
      }
      if (removeDataListener) {
        removeDataListener();
      }
      if (removeExitListener) {
        removeExitListener();
      }
    };
  }, [showTerminal]);

  useEffect(() => {
    if (!showTerminal || !terminalRef.current || !fitAddonRef.current) {
      return;
    }
    const terminalApi = window?.paperMem?.terminalApi;
    const term = terminalRef.current;
    const fitAddon = fitAddonRef.current;
    const timer = setTimeout(() => {
      fitAddon.fit();
      term.focus();
      if (terminalIdRef.current) {
        terminalApi?.resize(terminalIdRef.current, term.cols, term.rows);
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [showTerminal]);

  useEffect(() => {
    if (!openMenu) return;
    const handler = () => setOpenMenu('');
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [openMenu]);

  useEffect(() => {
    const api = window.paperMem;
    if (!api?.onFileChanged || !currentFilePath) return;
    const removeListener = api.onFileChanged(async ({ filePath }) => {
      if (!filePath || filePath !== currentFilePath) {
        return;
      }
      if (isLoadingRef.current) {
        return;
      }
      await loadDraft(filePath);
    });
    return () => removeListener?.();
  }, [currentFilePath, loadDraft]);

  const handleAutoSave = useCallback(async (value) => {
    if (!currentFilePath) return;
    const api = window.paperMem;
    if (!api?.writeTextFile) return;
    if (value === lastSavedRef.current) return;
    setFileStatus('saving');
    const result = await api.writeTextFile(currentFilePath, value);
    if (result?.ok) {
      lastSavedRef.current = value;
      setFileStatus('saved');
    } else {
      setFileStatus('error');
    }
  }, [currentFilePath]);

  const handleSave = useCallback(async () => {
    if (!editorContent) return;
    await handleAutoSave(editorContent);
  }, [editorContent, handleAutoSave]);

  const handleSaveAs = useCallback(async () => {
    const api = window.paperMem;
    if (!api?.writeTextFile) return;
    const nextPath = prompt('Save as path', currentFilePath || '');
    if (!nextPath) return;
    const result = await api.writeTextFile(nextPath, editorContent || '');
    if (result?.ok) {
      lastSavedRef.current = editorContent || '';
      setCurrentFilePath(nextPath);
      setFileStatus('saved');
      const nextDir = nextPath.split('/').slice(0, -1).join('/');
      if (nextDir && nextDir !== projectPath) {
        setProjectPath(nextDir);
        await api.startWatching?.(nextDir);
      }
    } else {
      setFileStatus('error');
    }
  }, [currentFilePath, editorContent, projectPath]);

  const handleOpenFile = useCallback(async () => {
    const api = window.paperMem;
    if (!api?.readTextFile) return;
    const nextPath = prompt('Open file path', currentFilePath || '');
    if (!nextPath) return;
    await loadDraft(nextPath);
    setCurrentFilePath(nextPath);
    const nextDir = nextPath.split('/').slice(0, -1).join('/');
    if (nextDir && nextDir !== projectPath) {
      setProjectPath(nextDir);
      await api.startWatching?.(nextDir);
    }
  }, [currentFilePath, loadDraft, projectPath]);

  const handleExportPdf = useCallback(() => {
    window.print();
  }, []);

  const handleNewFile = useCallback(() => {
    setEditorContent('');
    lastSavedRef.current = '';
    setFileStatus('idle');
  }, []);

  const handleInsertHeading = useCallback(() => {
    setEditorContent((prev) => `${prev ? `${prev}\n\n` : ''}## `);
  }, []);

  const handleInsertTimestamp = useCallback(() => {
    const stamp = new Date().toLocaleString();
    setEditorContent((prev) => `${prev ? `${prev}\n\n` : ''}${stamp}`);
  }, []);

  const handleInsertCitation = useCallback(() => {
    setEditorContent((prev) => `${prev ? `${prev} ` : ''}[1]`);
  }, []);

  const handleInsertImage = useCallback(() => {
    const url = prompt('Image URL');
    if (!url) return;
    setEditorContent((prev) => `${prev ? `${prev}\n\n` : ''}![image](${url})`);
  }, []);

  const handleInsertContent = useCallback((text) => {
    if (!text) return;
    setEditorContent((prev) => (prev ? `${prev}\n\n${text}` : text));
  }, []);

  const handleOpenSource = useCallback((context) => {
    if (!context) return;
    const metadata = context.metadata || {};
    const fileUrl = metadata.file_path || metadata.file_url || metadata.source_path;
    if (!fileUrl) return;
    const page =
      Number(metadata.page_num || metadata.page_number || 1) || 1;
    setPdfState({
      fileUrl,
      page,
      highlightText: context.text || null,
    });
  }, []);

  const handleProjectChange = useCallback((project) => {
    setCurrentProject(project);
    if (project?.id) {
      window.paperMem?.setActiveProjectId(project.id);
    }
  }, []);

  const handleProjectCreated = useCallback((project) => {
    if (!project) return;
    setProjects((prev) => [project, ...prev]);
    setCurrentProject(project);
    window.paperMem?.setActiveProjectId(project.id);
  }, []);

  const handleFileUpload = useCallback(() => {
    if (currentProject?.id) {
      fetchFiles(currentProject.id);
    }
  }, [currentProject, fetchFiles]);

  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e] text-[#cccccc]">
      <div className="menu-bar">
        <div className="menu-left">
          <div className="relative">
            <button
              type="button"
              className="menu-button"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenu(openMenu === 'file' ? '' : 'file');
              }}
            >
              File
            </button>
            {openMenu === 'file' && (
              <div className="menu-dropdown" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="menu-item" onClick={handleNewFile}>
                  New
                </button>
                <button type="button" className="menu-item" onClick={handleOpenFile}>
                  Open File
                </button>
                <button type="button" className="menu-item" onClick={handleSave}>
                  Save
                </button>
                <button type="button" className="menu-item" onClick={handleSaveAs}>
                  Save As
                </button>
                <button type="button" className="menu-item" onClick={handleExportPdf}>
                  Export PDF
                </button>
              </div>
            )}
          </div>
          <div className="relative">
            <button
              type="button"
              className="menu-button"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenu(openMenu === 'insert' ? '' : 'insert');
              }}
            >
              Insert
            </button>
            {openMenu === 'insert' && (
              <div className="menu-dropdown" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="menu-item" onClick={handleInsertHeading}>
                  Heading 2
                </button>
                <button type="button" className="menu-item" onClick={handleInsertTimestamp}>
                  Timestamp
                </button>
                <button type="button" className="menu-item" onClick={handleInsertCitation}>
                  Insert Citation
                </button>
                <button type="button" className="menu-item" onClick={handleInsertImage}>
                  Insert Image
                </button>
              </div>
            )}
          </div>
          <button
            type="button"
            className="menu-button"
            onClick={() => setActiveTab('editor')}
          >
            Editor
          </button>
          <button
            type="button"
            className="menu-button"
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="menu-button"
            onClick={() => setShowTerminal((prev) => !prev)}
          >
            {showTerminal ? 'Hide Terminal' : 'Terminal'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-72">
          <Sidebar
            projects={projects}
            currentProject={currentProject}
            onProjectChange={handleProjectChange}
            onCreateProject={handleProjectCreated}
            onFileUpload={handleFileUpload}
            files={files}
            apiBase={API_BASE}
          />
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1">
            {activeTab === 'editor' ? (
              <DualEditor
                content={editorContent}
                onChange={setEditorContent}
                onAutoSave={handleAutoSave}
                projectId={currentProject?.id}
              />
            ) : (
              <ChatPanel
                projectId={currentProject?.id}
                apiBase={API_BASE}
                onOpenSource={handleOpenSource}
              />
            )}
          </div>

          {activeTab === 'editor' && (
            <div className="w-80">
              <ActiveRagSidebar
                projectId={currentProject?.id}
                editorContent={editorContent}
                onInsertContent={handleInsertContent}
                apiBase={API_BASE}
              />
            </div>
          )}
        </div>
      </div>

      <div className="h-6 px-4 bg-[#007acc] text-white text-xs flex items-center justify-between">
        <span>
          {currentProject ? `Project: ${currentProject.name}` : 'No project selected'}
        </span>
        <span>
          {currentFilePath ? `File: ${currentFilePath}` : 'No file'}
        </span>
        <span>
          {fileStatus === 'saving'
            ? 'Saving...'
            : fileStatus === 'saved'
              ? 'Saved'
              : fileStatus === 'loading'
                ? 'Loading...'
                : fileStatus === 'error'
                  ? 'Error'
                  : 'Ready'}
        </span>
      </div>

      {showTerminal && (
        <div className="terminal-panel">
          <div className="terminal-header">
            <span>Terminal</span>
            <button
              type="button"
              className="terminal-toggle"
              onClick={() => setShowTerminal(false)}
            >
              Hide
            </button>
          </div>
          <div
            className="terminal-body"
            ref={terminalContainerRef}
            onClick={() => terminalRef.current?.focus()}
          />
        </div>
      )}

      {pdfState && (
        <div className="pdf-modal">
          <div className="pdf-modal-backdrop" onClick={() => setPdfState(null)} />
          <div className="pdf-modal-content">
            <PDFViewer
              fileUrl={pdfState.fileUrl}
              initialPage={pdfState.page}
              highlightText={pdfState.highlightText}
              onClose={() => setPdfState(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
