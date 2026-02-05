const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('paperMem', {
  apiBase: 'http://127.0.0.1:8000',

  // 项目管理
  setActiveProjectId: (projectId) =>
    ipcRenderer.invoke('set-active-project', projectId),

  // 文件上传
  uploadFile: ({ filePath, projectId }) =>
    ipcRenderer.invoke('dropzone-upload', { filePath, projectId }),

  // 文件监听
  startWatching: (projectPath) =>
    ipcRenderer.invoke('start-watching', projectPath),

  stopWatching: () =>
    ipcRenderer.invoke('stop-watching'),

  // 文件变化事件监听
  onFileChanged: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('file-changed', handler);
    return () => ipcRenderer.removeListener('file-changed', handler);
  },

  onFileAdded: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('file-added', handler);
    return () => ipcRenderer.removeListener('file-added', handler);
  },

  onFileRemoved: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('file-removed', handler);
    return () => ipcRenderer.removeListener('file-removed', handler);
  },

  getDefaultProjectPath: () =>
    ipcRenderer.invoke('get-default-project-path'),

  getDefaultDraftPath: () =>
    ipcRenderer.invoke('get-default-draft-path'),

  readTextFile: (filePath) =>
    ipcRenderer.invoke('read-text-file', filePath),

  writeTextFile: (filePath, content) =>
    ipcRenderer.invoke('write-text-file', { filePath, content }),

  // 内嵌终端
  terminalApi: {
    create: (options) => ipcRenderer.invoke('terminal-create', options),
    write: (id, data) => ipcRenderer.invoke('terminal-write', { id, data }),
    resize: (id, cols, rows) => ipcRenderer.invoke('terminal-resize', { id, cols, rows }),
    dispose: (id) => ipcRenderer.invoke('terminal-dispose', { id }),
    onData: (callback) => {
      const handler = (event, payload) => callback(payload);
      ipcRenderer.on('terminal-data', handler);
      return () => ipcRenderer.removeListener('terminal-data', handler);
    },
    onExit: (callback) => {
      const handler = (event, payload) => callback(payload);
      ipcRenderer.on('terminal-exit', handler);
      return () => ipcRenderer.removeListener('terminal-exit', handler);
    },
  },
});
