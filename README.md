# PaperMem

> 面向学术写作的本地优先研究助手，体验类似 VSCode 的论文工作台

PaperMem 是一款桌面应用，将 AI 辅助与类似 VSCode 的界面结合，帮助研究者管理论文、写作与知识回溯。

## 功能

### 核心能力
- **本地优先**：数据保存在本机（SQLite + ChromaDB）
- **双模编辑器**：Visual（TipTap）与 Source（CodeMirror）切换
- **主动检索侧边栏**：写作中自动推荐相关内容
- **全局划词采集**：跨应用保存片段到项目
- **PDF 解析**：MinerU 高保真解析
- **语义检索**：Qwen Embedding 向量检索
- **AI 对话**：DeepSeek R1 推理对话
- **文件监听**：CLI 与 GUI 实时同步
- **数学公式**：KaTeX 渲染

### 使用体验
- **类似 VSCode 的布局**：侧边栏 + 编辑器 + 面板
- **轻量浮窗**：不打扰写作流
- **溯源定位**：引用直达原始 PDF
- **流式响应**：实时看到回答过程

---

## 快速开始

### 前置条件
- **Python 3.10+** 与 pip
- **Node.js 18+** 与 npm
- **MinerU API Token**（https://mineru.net/）
- **OpenRouter API Key**（https://openrouter.ai/）

### 安装

1. **克隆仓库**
   ```bash
   git clone https://github.com/Juggernaut0825/paper_app.git
   cd paper_app
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 并填入 API Key
   # OPENROUTER_API_KEY=sk-or-v1-...
   # MINERU_API_TOKEN=your_token_here
   ```

3. **安装依赖**
   ```bash
   # 根目录依赖（Electron）
   npm install

   # 前端依赖
   cd frontend
   npm install
   cd ..

   # Python 依赖（后端 + CLI）
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **启动应用**
   ```bash
   npm run dev
   ```

启动后将会：
- 启动 FastAPI 后端 `http://127.0.0.1:8000`
- 启动 Vite 前端 `http://127.0.0.1:5173`
- 启动 Electron 应用并热更新

---

## 使用指南

### 创建项目

1. **启动 PaperMem**
   - 打开后进入类似 VSCode 的界面
   - 左侧为项目与文件区

2. **新建项目**
   - 点击 `+ New Project`
   - 输入项目名（如 “My Research”）

3. **上传 PDF**
   - 点击 “Upload PDF”
   - MinerU 自动解析为 Markdown
   - 自动切片并写入 ChromaDB

4. **开始写作**
   - 切换到 Editor
   - Visual / Source 模式任选
   - 右侧主动检索推荐相关内容

5. **对话检索**
   - 切换到 Chat
   - 询问已上传资料
   - 自动检索并返回可溯源回答

### 全局划词采集

1. **开启辅助权限（macOS）**
   - 系统设置 → 隐私与安全性 → 辅助功能
   - 允许 PaperMem

2. **跨应用保存片段**
   - 在任意应用拖动选中文本（>12px）
   - 出现 “Mem” 角标
   - 点击保存到当前项目

### 文件监听（CLI 联动）

当你在终端或编辑器中修改文件时：
- PaperMem 监听项目目录
- 内容自动刷新
- 适合 Markdown 工作流

---

## 架构

### 技术栈

**前端**
- React 19 + Vite
- TipTap（富文本）+ CodeMirror（源码）
- react-pdf（PDF 预览）

**后端**
- FastAPI
- SQLAlchemy + SQLite
- ChromaDB
- OpenRouter（LLM + Embedding）

**桌面端**
- Electron 40
- uiohook-napi（全局事件）
- chokidar（文件监听）

### 数据流

```
用户输入
  ↓
全局采集 / 文件上传
  ↓
MinerU 解析（PDF → Markdown）
  ↓
切片（512 字符，10% 重叠）
  ↓
Qwen Embedding
  ↓
ChromaDB（余弦相似度）
  ↓
DeepSeek R1（检索增强）
  ↓
流式响应（带引用）
```

### 目录结构

```
paper_app/
├── backend/              # FastAPI 服务
│   ├── app/
│   │   ├── main.py       # API 入口
│   │   ├── config.py     # 配置
│   │   ├── models.py     # 数据模型
│   │   ├── vector_store.py    # ChromaDB 集成
│   │   ├── chat_service.py    # RAG 对话
│   │   └── ingest_service.py  # PDF 解析
│   └── requirements.txt
├── frontend/             # React UI
│   ├── src/
│   │   ├── components/   # 组件
│   │   ├── App.jsx       # 入口
│   │   └── App.css       # 主题
│   └── package.json
├── electron/             # Electron 主进程
│   ├── main.js           # 窗口与 IPC
│   ├── preload.js        # 预加载脚本
│   ├── overlay.html      # 角标 UI
│   └── dropzone.html     # 上传 UI
├── cli_first_app/        # CLI 助手（本地存储）
└── .env                  # API Key
```

---

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENROUTER_API_KEY` | OpenRouter API Key（必填） | - |
| `MINERU_API_TOKEN` | MinerU Token（必填） | - |
| `LLM_MODEL` | 对话模型 | `deepseek/deepseek-r1` |
| `EMBEDDING_MODEL` | 向量模型 | `qwen/qwen3-embedding-4b` |
| `SQLITE_DB_PATH` | SQLite 路径 | `~/PaperMem/papermem.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB 路径 | `~/PaperMem/chromadb` |
| `RAW_FILES_DIR` | 原始 PDF 存储 | `~/PaperMem/Raw` |
| `PARSED_FILES_DIR` | 解析结果存储 | `~/PaperMem/Parsed` |
| `PAPERMEM_BASE_DIR` | CLI 数据根目录 | `~/PaperMem` |

CLI 数据默认存放在 `${PAPERMEM_BASE_DIR}/cli`（ChromaDB + SQLite）。

### 自定义

**切换模型**
- 在 `.env` 中修改 `LLM_MODEL`
- 例如：`LLM_MODEL=anthropic/claude-3.5-sonnet`

**调整切片策略**
- 修改 `backend/app/ingest_service.py` → `chunk_by_section()`
- 默认：512 字符、重叠 50 字符

**调整主题**
- 修改 `frontend/src/App.css`

---

## 开发

### 本地运行

```bash
npm run dev
```

该命令会并行启动：
1. `npm run dev:renderer`（Vite）
2. `npm run dev:electron`（Electron）

后端使用 `uvicorn --reload` 自动热更新。

### 生产构建

```bash
# 构建前端
npm run build

# 打包 Electron
# 需要先配置 electron-builder
npm run package
```

### API 端点

**项目**
- `GET /projects`：项目列表
- `POST /projects`：创建项目
- `DELETE /projects/{id}`：删除项目
- `GET /projects/{id}/files`：文件列表

**文件**
- `POST /projects/{id}/upload`：上传与解析
- `GET /projects/{id}/messages`：聊天记录

**对话**
- `POST /chat/stream`：流式对话
- `POST /search`：语义检索

**统计**
- `GET /projects/{id}/stats`：项目统计

---

## Roadmap

- [ ] LaTeX 导出：Markdown 转 `.tex`
- [ ] 协作功能
- [ ] 插件系统
- [ ] 移动端
- [ ] Obsidian 同步
- [ ] Web 版本

---

## 常见问题

### 后端启动失败
- 确认 Python 版本：`python --version`（需 3.10+）
- 激活虚拟环境：`source .venv/bin/activate`
- 安装依赖：`pip install -r requirements.txt`

### 全局采集不可用（macOS）
- 在系统设置中授权辅助功能
- 授权后重启应用

### PDF 解析失败
- 检查 `.env` 中 `MINERU_API_TOKEN`
- 确保网络可用且 PDF 非加密

### ChromaDB 问题
- 删除 `~/Documents/PaperMem/chromadb` 后重启
- 检查磁盘空间

---

## License

MIT License，详见 [LICENSE](LICENSE)

---

## 致谢

- MinerU：高质量 PDF 解析
- DeepSeek：推理模型
- Qwen：嵌入模型
- TipTap：富文本编辑
- ChromaDB：向量存储

---

## 联系方式

- Issues：https://github.com/Juggernaut0825/paper_app/issues
- Discussions：https://github.com/Juggernaut0825/paper_app/discussions
