// 侧边栏 - 文件和项目管理
import React, { useState, useEffect } from 'react';
import {
  FolderIcon,
  DocumentIcon,
  PDFIcon,
  UploadIcon,
  LoadingIcon,
  CheckIcon,
  SparklesIcon
} from './Icons';

export default function Sidebar({
  projects,
  currentProject,
  onProjectChange,
  onCreateProject,
  onFileUpload,
  files,
  apiBase
}) {
  const [uploadingFiles, setUploadingFiles] = useState(new Set());
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  const handleFileSelect = async (event) => {
    const selectedFiles = Array.from(event.target.files || []);

    for (const file of selectedFiles) {
      if (!file.name.endsWith('.pdf')) {
        alert('Only PDF files are supported');
        continue;
      }

      setUploadingFiles(prev => new Set(prev).add(file.name));

      try {
        // 这里调用 Electron IPC 上传文件
        const result = await window.paperMem?.uploadFile({
          filePath: file.path,
          projectId: currentProject?.id
        });

        if (result?.status === 'completed') {
          onFileUpload?.(result);
        }
      } catch (error) {
        console.error('Upload failed:', error);
        alert(`Failed to upload ${file.name}`);
      } finally {
        setUploadingFiles(prev => {
          const newSet = new Set(prev);
          newSet.delete(file.name);
          return newSet;
        });
      }
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    try {
      const response = await fetch(`${apiBase}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newProjectName,
          type: 'research',
          description: ''
        })
      });

      const project = await response.json();
      onCreateProject?.(project);
      setShowNewProject(false);
      setNewProjectName('');
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Failed to create project');
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#252526] border-r border-[#3e3e42]">
      {/* 侧边栏标题 */}
      <div className="px-4 py-3 bg-[#2d2d30] border-b border-[#3e3e42]">
        <h2 className="text-sm font-medium text-[#cccccc] uppercase tracking-wide">
          Explorer
        </h2>
      </div>

      {/* 项目选择器 */}
      <div className="p-2 border-b border-[#3e3e42]">
        <select
          value={currentProject?.id || ''}
          onChange={(e) => {
            const project = projects.find(p => p.id === e.target.value);
            onProjectChange?.(project);
          }}
          className="w-full px-3 py-2 bg-[#3c3c3c] text-[#cccccc] rounded text-sm focus:outline-none focus:ring-1 focus:ring-[#007acc]"
        >
          <option value="">Select Project</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>

        <button
          onClick={() => setShowNewProject(!showNewProject)}
          className="w-full mt-2 px-3 py-1.5 bg-[#0e639c] hover:bg-[#1177bb] text-white rounded text-xs transition-colors"
        >
          + New Project
        </button>

        {showNewProject && (
          <div className="mt-2 space-y-2">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateProject()}
              placeholder="Project name..."
              className="w-full px-3 py-1.5 bg-[#3c3c3c] text-[#cccccc] rounded text-xs focus:outline-none focus:ring-1 focus:ring-[#007acc]"
              autoFocus
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateProject}
                className="flex-1 px-2 py-1 bg-[#0e639c] hover:bg-[#1177bb] text-white rounded text-xs"
              >
                Create
              </button>
              <button
                onClick={() => setShowNewProject(false)}
                className="px-2 py-1 bg-[#37373d] hover:bg-[#3e3e42] text-[#cccccc] rounded text-xs"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 文件列表 */}
      <div className="flex-1 overflow-y-auto">
        {currentProject ? (
          <>
            {/* 上传按钮 */}
            <div className="p-2">
              <label className="flex items-center justify-center gap-2 w-full px-3 py-2 bg-[#37373d] hover:bg-[#3e3e42] text-[#cccccc] rounded cursor-pointer transition-colors">
                <UploadIcon className="w-3 h-3" />
                <span className="text-xs">Upload PDF</span>
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>

            {/* 文件树 */}
            <div className="p-2">
              {files && files.length > 0 ? (
                <div className="space-y-1">
                  {files.map(file => (
                    <FileItem
                      key={file.id}
                      file={file}
                      isUploading={uploadingFiles.has(file.file_name)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-xs text-[#6e6e6e]">
                  No files yet. Upload a PDF to get started.
                </div>
              )}

              {/* 上传中的文件 */}
              {Array.from(uploadingFiles).map(fileName => (
                <div key={fileName} className="flex items-center gap-2 px-2 py-1.5 text-xs text-[#858585]">
                  <LoadingIcon className="w-3 h-3" />
                  <span className="truncate">{fileName}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-center p-6">
            <div className="text-xs text-[#6e6e6e]">
              Select or create a project to get started
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FileItem({ file, isUploading }) {
  const { file_name, parse_status, chunks_count } = file;

  return (
    <div className="group flex items-center gap-2 px-2 py-1.5 hover:bg-[#2a2d2e] rounded cursor-pointer transition-colors">
      <PDFIcon className="w-3 h-3 text-[#f9826c] flex-shrink-0" />

      <div className="flex-1 min-w-0">
        <div className="text-xs text-[#cccccc] truncate">{file_name}</div>
        <div className="flex items-center gap-2 mt-0.5">
          {isUploading || parse_status === 'pending' || parse_status === 'processing' ? (
            <span className="flex items-center gap-1 text-xs text-[#858585]">
              <LoadingIcon className="w-2.5 h-2.5" />
              Parsing...
            </span>
          ) : parse_status === 'completed' ? (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <CheckIcon className="w-2.5 h-2.5" />
              {chunks_count} chunks
            </span>
          ) : parse_status === 'failed' ? (
            <span className="text-xs text-red-400">Parse failed</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
