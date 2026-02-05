/**
 * PaperMem - Electron Main Process
 * 集成：全局划词、文件上传、文件监听、CLI工具
 */

const {
  app,
  BrowserWindow,
  clipboard,
  ipcMain,
  screen,
  dialog,
  systemPreferences,
} = require('electron');
const path = require('path');
const fs = require('fs');
const { execFile, spawn, exec } = require('child_process');
const { uIOhook } = require('uiohook-napi');
const chokidar = require('chokidar');
const pty = require('node-pty');

// 环境变量
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const isDev = process.env.NODE_ENV !== 'production' || !app || !app.isPackaged;
const API_BASE = process.env.API_BASE || 'http://127.0.0.1:8000';

// 全局变量
let backendProcess = null;
let mainWindow = null;
let overlayWindow = null;
let dropzoneWindow = null;
let fileWatcher = null;
const terminalSessions = new Map();
let overlayAutoHideTimer = null;

let activeProjectId = '';
let latestSelectionText = '';
let mouseDownPoint = null;

// 常量
const OVERLAY_WIDTH = 70;
const OVERLAY_HEIGHT = 32;
const DROPZONE_IDLE_SIZE = 32;
const DROPZONE_ACTIVE_WIDTH = 300;
const DROPZONE_ACTIVE_HEIGHT = 400;
const TERMINAL_DEFAULT_COLS = 120;
const TERMINAL_DEFAULT_ROWS = 32;

// ==================== 后端启动 ====================

function startBackend() {
  if (backendProcess) return;

  const backendCwd = path.join(app.getAppPath(), 'backend');
  const pythonFromVenv = process.platform === 'win32'
    ? path.join(backendCwd, '.venv', 'Scripts', 'python.exe')
    : path.join(backendCwd, '.venv', 'bin', 'python');
  const pythonBin = fs.existsSync(pythonFromVenv) ? pythonFromVenv : 'python';

  const args = [
    '-m',
    'uvicorn',
    'app.main:app',
    '--host',
    '127.0.0.1',
    '--port',
    '8000',
  ];

  if (isDev) args.push('--reload');

  console.log('[Backend] Starting:', pythonBin, args.join(' '));

  backendProcess = spawn(pythonBin, args, {
    cwd: backendCwd,
    stdio: 'pipe',
  });

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend] ${data}`);
  });

  backendProcess.on('exit', (code) => {
    console.log(`[Backend] Exited with code ${code}`);
    backendProcess = null;
  });
}

// ==================== 窗口创建 ====================

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    backgroundColor: '#1e1e1e',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
  }
}

function createOverlayWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  overlayWindow = new BrowserWindow({
    width: OVERLAY_WIDTH,
    height: OVERLAY_HEIGHT,
    x: width - OVERLAY_WIDTH - 20,
    y: height - OVERLAY_HEIGHT - 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'overlay_preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  overlayWindow.loadFile(path.join(__dirname, 'overlay.html'));
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  overlayWindow.setAlwaysOnTop(true, 'floating');
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });
  overlayWindow.hide();
}

function createDropzoneWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  dropzoneWindow = new BrowserWindow({
    width: DROPZONE_IDLE_SIZE,
    height: DROPZONE_IDLE_SIZE,
    x: width - DROPZONE_IDLE_SIZE - 20,
    y: 100,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'dropzone_preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  dropzoneWindow.loadFile(path.join(__dirname, 'dropzone.html'));
  dropzoneWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  dropzoneWindow.setAlwaysOnTop(true, 'floating');
}

function getTerminalShell() {
  if (process.platform === 'win32') {
    return 'powershell.exe';
  }
  const candidates = [
    process.env.SHELL,
    process.platform === 'darwin' ? '/bin/zsh' : '/bin/bash',
    '/bin/sh',
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return process.platform === 'darwin' ? '/bin/zsh' : '/bin/bash';
}

function resolveShellCandidates() {
  if (process.platform === 'win32') {
    return ['powershell.exe'];
  }
  const candidates = [
    process.env.SHELL,
    process.platform === 'darwin' ? '/bin/zsh' : '/bin/bash',
    '/bin/bash',
    '/bin/zsh',
    '/bin/sh',
  ].filter(Boolean);
  const unique = [];
  for (const candidate of candidates) {
    if (unique.includes(candidate)) continue;
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      unique.push(candidate);
    } catch (error) {
      // ignore non-executable
    }
  }
  return unique.length > 0 ? unique : [getTerminalShell()];
}

function resolveTerminalCwd(preferredCwd) {
  const candidates = [
    preferredCwd,
    app.getPath('home'),
    process.env.HOME,
    app.getPath('userData'),
    '/',
  ].filter(Boolean);

  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
        return candidate;
      }
    } catch (error) {
      // ignore
    }
  }
  return app.getPath('home');
}

function getTerminalShellArgs() {
  if (process.platform === 'win32') {
    return ['-NoLogo', '-NoExit'];
  }
  return ['-l'];
}

// ==================== 全局划词功能 ====================

function sendCopyShortcut() {
  return new Promise((resolve) => {
    if (process.platform === 'darwin') {
      execFile(
        'osascript',
        ['-e', 'tell application "System Events" to keystroke "c" using command down'],
        () => resolve()
      );
    } else if (process.platform === 'win32') {
      execFile(
        'powershell',
        ['-Command', '$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys("^c")'],
        () => resolve()
      );
    } else {
      resolve();
    }
  });
}

function showOverlayAt(x, y) {
  if (!overlayWindow) return;

  const { x: dx, y: dy, width, height } = screen.getPrimaryDisplay().workArea;

  let left = Math.max(dx, Math.min(x + OVERLAY_WIDTH / 2, dx + width - OVERLAY_WIDTH));
  let top = Math.max(dy, Math.min(y - OVERLAY_HEIGHT / 2, dy + height - OVERLAY_HEIGHT));

  overlayWindow.setBounds({ x: left, y: top });
  overlayWindow.setIgnoreMouseEvents(false);
  overlayWindow.show();
  scheduleOverlayAutoHide();
}

function clearOverlayAutoHide() {
  if (overlayAutoHideTimer) {
    clearTimeout(overlayAutoHideTimer);
    overlayAutoHideTimer = null;
  }
}

function scheduleOverlayAutoHide() {
  clearOverlayAutoHide();
  overlayAutoHideTimer = setTimeout(() => {
    if (overlayWindow && overlayWindow.isVisible()) {
      overlayWindow.hide();
      overlayWindow.setIgnoreMouseEvents(true, { forward: true });
    }
  }, 5000);
}

function isPointInsideOverlay(x, y) {
  if (!overlayWindow || !overlayWindow.isVisible()) return false;
  const bounds = overlayWindow.getBounds();
  return (
    x >= bounds.x &&
    x <= bounds.x + bounds.width &&
    y >= bounds.y &&
    y <= bounds.y + bounds.height
  );
}

function handleMouseDown(event) {
  if (overlayWindow && overlayWindow.isVisible()) {
    if (!isPointInsideOverlay(event.x, event.y)) {
      overlayWindow.hide();
      overlayWindow.setIgnoreMouseEvents(true, { forward: true });
      latestSelectionText = '';
      clearOverlayAutoHide();
    } else {
      return;
    }
  }
  mouseDownPoint = { x: event.x, y: event.y };
}

function handleMouseUp(event) {
  if (!mouseDownPoint) return;

  const dx = event.x - mouseDownPoint.x;
  const dy = event.y - mouseDownPoint.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  mouseDownPoint = null;

  if (distance > 12) {
    setTimeout(async () => {
      await sendCopyShortcut();
      await new Promise((r) => setTimeout(r, 100));

      const text = clipboard.readText('selection') || clipboard.readText();
      if (text && text.length > 3) {
        latestSelectionText = text;
        showOverlayAt(event.x, event.y);
      }
    }, 50);
  }
}

function startCapture() {
  try {
    uIOhook.on('mousedown', handleMouseDown);
    uIOhook.on('mouseup', handleMouseUp);
    uIOhook.start();
    console.log('[Capture] Global text capture started');
  } catch (error) {
    console.error('[Capture] Failed to start global capture:', error.message);
    console.log('[Capture] Please grant Accessibility permissions in System Settings');
  }
}

function stopCapture() {
  try {
    uIOhook.stop();
    console.log('[Capture] Global text capture stopped');
  } catch (error) {
    console.error('[Capture] Failed to stop capture:', error.message);
  }
}

// ==================== 文件监听功能 ====================

function startFileWatcher(projectPath) {
  if (fileWatcher) {
    fileWatcher.close();
  }

  console.log(`[FileWatcher] Watching: ${projectPath}`);

  fileWatcher = chokidar.watch(projectPath, {
    ignored: /(^|[\/\\])\../, // 忽略隐藏文件
    persistent: true,
    ignoreInitial: true,
  });

  fileWatcher
    .on('change', (filePath) => {
      console.log(`[FileWatcher] File changed: ${filePath}`);
      if (mainWindow) {
        mainWindow.webContents.send('file-changed', { filePath });
      }
    })
    .on('add', (filePath) => {
      console.log(`[FileWatcher] File added: ${filePath}`);
      if (mainWindow) {
        mainWindow.webContents.send('file-added', { filePath });
      }
    })
    .on('unlink', (filePath) => {
      console.log(`[FileWatcher] File removed: ${filePath}`);
      if (mainWindow) {
        mainWindow.webContents.send('file-removed', { filePath });
      }
    });
}

// ==================== IPC 处理 ====================

ipcMain.handle('overlay-save', async (event) => {
  if (!latestSelectionText || !activeProjectId) {
    return { success: false, message: 'No text or project selected' };
  }

  console.log('[Overlay] Saving selection to memory:', latestSelectionText.substring(0, 50));

  // 调用新后端 API 添加到向量库
  try {
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: latestSelectionText,
        project_id: activeProjectId,
        save: true, // 添加标记以保存
      }),
    });

    if (response.ok) {
      console.log('[Overlay] Saved successfully');
      latestSelectionText = '';
      return { success: true };
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('[Overlay] Save failed:', error);
    latestSelectionText = '';
    return { success: false, message: error.message };
  }
});

ipcMain.handle('overlay-hide', () => {
  console.log('[Overlay] Hiding overlay window');
  overlayWindow?.hide();
  overlayWindow?.setIgnoreMouseEvents(true, { forward: true });
  latestSelectionText = '';
  clearOverlayAutoHide();
  return { success: true };
});

ipcMain.on('overlay-close', () => {
  overlayWindow?.hide();
  overlayWindow?.setIgnoreMouseEvents(true, { forward: true });
  clearOverlayAutoHide();
});

ipcMain.handle('dropzone-upload', async (event, { filePath, projectId }) => {
  console.log('[Dropzone] Uploading file:', filePath);

  try {
    // 读取文件
    const fileContent = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);

    // 上传到本地临时目录或直接传给后端
    const tempDir = app.getPath('temp');
    const tempPath = path.join(tempDir, fileName);
    fs.writeFileSync(tempPath, fileContent);

    // 调用后端 API
    const fileUrl = process.platform === 'win32'
      ? `file:///${tempPath.replace(/\\/g, '/')}`
      : `file://${tempPath}`;

    const response = await fetch(`${API_BASE}/projects/${projectId}/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_url: fileUrl,
        file_name: fileName,
      }),
    });

    const result = await response.json();
    console.log('[Dropzone] Upload result:', result);

    return result;
  } catch (error) {
    console.error('[Dropzone] Upload failed:', error);
    throw error;
  }
});

ipcMain.handle('dropzone-resize', (event, { width, height }) => {
  if (dropzoneWindow) {
    const bounds = dropzoneWindow.getBounds();
    const rightEdge = bounds.x + bounds.width;
    const nextX = Math.max(0, rightEdge - width);
    dropzoneWindow.setBounds({ x: nextX, y: bounds.y, width, height });
  }
});

ipcMain.handle('terminal-create', (event, options = {}) => {
  const args = getTerminalShellArgs();
  const cols = Number(options.cols || TERMINAL_DEFAULT_COLS);
  const rows = Number(options.rows || TERMINAL_DEFAULT_ROWS);
  const cwd = resolveTerminalCwd(options.cwd);
  const id = options.id || `term_${Date.now()}_${Math.random().toString(16).slice(2)}`;

  if (terminalSessions.has(id)) {
    return { ok: true, id };
  }

  let term = null;
  const shellCandidates = resolveShellCandidates();
  const argCandidates = process.platform === 'win32' ? [args] : [args, []];
  let lastError = null;

  for (const shell of shellCandidates) {
    for (const shellArgs of argCandidates) {
      try {
        term = pty.spawn(shell, shellArgs, {
          name: 'xterm-256color',
          cols,
          rows,
          cwd,
          env: {
            ...process.env,
            TERM: 'xterm-256color',
            SHELL: shell,
          },
        });
        lastError = null;
        break;
      } catch (error) {
        lastError = error;
      }
    }
    if (term) break;
  }

  if (!term) {
    console.error('[Terminal] Failed to spawn:', {
      shellCandidates,
      argCandidates,
      cwd,
      error: lastError?.message || lastError,
      code: lastError?.code,
      errno: lastError?.errno,
    });
    return {
      ok: false,
      error: lastError?.message || 'Failed to spawn shell',
    };
  }

  terminalSessions.set(id, term);

  const sender = event.sender;
  term.onData((data) => {
    sender.send('terminal-data', { id, data });
  });
  term.onExit(({ exitCode }) => {
    sender.send('terminal-exit', { id, exitCode });
    terminalSessions.delete(id);
  });

  return { ok: true, id };
});

ipcMain.handle('terminal-write', (event, { id, data }) => {
  const term = terminalSessions.get(id);
  if (term) {
    term.write(data);
    return { ok: true };
  }
  return { ok: false };
});

ipcMain.handle('terminal-resize', (event, { id, cols, rows }) => {
  const term = terminalSessions.get(id);
  if (term) {
    term.resize(Number(cols), Number(rows));
    return { ok: true };
  }
  return { ok: false };
});

ipcMain.handle('terminal-dispose', (event, { id }) => {
  const term = terminalSessions.get(id);
  if (term) {
    term.kill();
    terminalSessions.delete(id);
  }
  return { ok: true };
});

ipcMain.handle('dropzone-pick-files', async () => {
  const result = await dialog.showOpenDialog(dropzoneWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [{ name: 'PDF Files', extensions: ['pdf'] }],
  });

  return result.filePaths;
});

ipcMain.handle('set-active-project', (event, projectId) => {
  activeProjectId = projectId;
  console.log('[IPC] Active project set to:', projectId);
  return { success: true, projectId };
});

ipcMain.handle('dropzone-get-project', () => {
  console.log('[IPC] Getting active project:', activeProjectId);
  return activeProjectId;
});

ipcMain.handle('start-watching', (event, projectPath) => {
  startFileWatcher(projectPath);
  return { success: true };
});

ipcMain.handle('stop-watching', () => {
  if (fileWatcher) {
    fileWatcher.close();
    fileWatcher = null;
  }
  return { success: true };
});

ipcMain.handle('get-default-project-path', () => {
  return path.join(app.getPath('home'), 'PaperMem', 'Projects', 'Current');
});

ipcMain.handle('get-default-draft-path', () => {
  return path.join(app.getPath('home'), 'PaperMem', 'Projects', 'Current', 'draft.md');
});

ipcMain.handle('read-text-file', (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return { ok: true, content };
  } catch (error) {
    return { ok: false, error: error.message };
  }
});

ipcMain.handle('write-text-file', (event, { filePath, content }) => {
  try {
    const dir = path.dirname(filePath);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filePath, content ?? '', 'utf-8');
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error.message };
  }
});

// ==================== 权限请求 ====================

async function ensureAccessibilityPermissions() {
  if (process.platform === 'darwin') {
    const trusted = systemPreferences.isTrustedAccessibilityClient(false);
    if (!trusted) {
      console.log('[Permissions] Requesting accessibility permissions...');
      systemPreferences.isTrustedAccessibilityClient(true);
    }
  }
}

function remindWindowsAdminPermission() {
  if (process.platform === 'win32') {
    console.log('[Permissions] Windows: Please run as administrator for global hotkeys');
  }
}

// ==================== 应用生命周期 ====================

app.whenReady().then(async () => {
  startBackend();
  await ensureAccessibilityPermissions();
  remindWindowsAdminPermission();

  createOverlayWindow();
  createDropzoneWindow();
  startCapture();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  stopCapture();
  if (backendProcess) {
    backendProcess.kill();
  }
  if (fileWatcher) {
    fileWatcher.close();
  }
  clearOverlayAutoHide();
});
