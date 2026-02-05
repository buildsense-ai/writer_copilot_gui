# CLI Agent - 智能文件操作助手

基于 cli-brain-off 的 Skill 系统集成到 cli_first_app 的轻量级 AI 助手。

## 特性

- Skill 系统：动态工具加载和 Skill 选择
- 记忆驱动：对话历史和语义检索
- 文件操作：读取、编辑、创建文件（带确认）
- 本地优先：SQLite + ChromaDB，完全本地运行
- OpenRouter API：统一的 DeepSeek + Qwen 接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的 OpenRouter API Key：

```bash
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=deepseek/deepseek-r1
EMBEDDING_MODEL=qwen/qwen3-embedding-4b
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 启动聊天

```bash
python chat.py
```

## 可用命令

- `/help` - 显示帮助
- `/clear` - 清除对话历史
- `/stats` - 显示统计信息
- `/exit` - 退出

## 架构

```
cli_first_app/
├── chat.py                    # 主入口
├── scripts/
│   ├── init_db.py             # 数据库初始化
│   ├── test_agent.py          # 功能测试
│   └── verify_integration.py  # 集成验证
├── skills/                    # Skill 定义
│   ├── file_ops/
│   │   ├── config.json
│   │   └── skill.md
│   └── todo/
│       ├── config.json
│       └── skill.md
├── src/
│   ├── core/                  # 核心系统
│   │   ├── agent/            # Agent 控制器
│   │   ├── memory/           # 记忆系统
│   │   └── skills/           # Skill 管理
│   ├── infrastructure/        # 基础设施
│   │   ├── database/         # SQLite
│   │   ├── llm/              # OpenRouter 客户端
│   │   └── utils/            # CLI 工具
│   ├── skills/                # Skills 实现
│   │   ├── file_ops/         # 文件操作工具
│   │   └── todo/             # 任务管理工具
│   ├── repositories/          # 数据访问层
│   ├── services/              # 业务逻辑层
│   ├── infra.py              # 存储设置
│   ├── memory.py             # 原有记忆模块（保留）
│   ├── llm.py                # 原有 LLM 模块（保留）
│   ├── tools.py              # 原有工具模块（保留）
│   └── main.py               # 原有 Typer CLI（保留）
├── requirements.txt           # 引用根目录依赖
├── requirements-standalone.txt # 独立依赖列表
└── .gitignore                 # 已完善
```

## 技术栈

- LLM: DeepSeek R1 (via OpenRouter)
- Embeddings: Qwen 3 Embedding 4B (via OpenRouter)
- Vector DB: ChromaDB (本地)
- Database: SQLite (本地)
- CLI: Rich + Prompt Toolkit

## Skills

### File Operations Skill

文件操作技能，支持：
- `read_file` - 读取文件（带行号）
- `apply_edit` - 精确编辑（search & replace，带 diff 预览）
- `write_file` - 创建/覆盖文件
- `list_files` - 列出文件（支持 glob 和递归）

所有写操作都需要用户确认，确保安全。

### Todo Skill

任务管理技能，支持：
- `database_operation` - 创建、更新、删除任务
  - 创建任务（支持标题、描述、状态、优先级、标签等）
  - 更新任务状态和属性
  - 软删除任务
- `search` - 语义搜索任务
  - 按内容搜索
  - 按状态和优先级过滤
  - 向量相似度匹配

任务状态：brainstorm（想法）、inbox（待处理）、active（进行中）、waiting（等待）、someday（将来）、completed（完成）、archived（归档）

## License

MIT
