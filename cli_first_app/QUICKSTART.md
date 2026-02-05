# CLI Agent - 快速启动指南

## 🚀 5 分钟快速开始

### 1. 安装依赖（1 分钟）

**选项 A：共享依赖**（推荐）

```bash
cd cli_first_app
pip install -r ../requirements.txt
```

**选项 B：独立依赖**（最小化安装）

```bash
cd cli_first_app
pip install -r requirements-standalone.txt
```

### 2. 配置 API Key（1 分钟）

创建 `.env` 文件：

```bash
cp ../.env.example .env
```

编辑 `.env` 文件，设置你的 OpenRouter API Key：

```bash
OPENROUTER_API_KEY=your_key_here
```

> 获取 API Key: https://openrouter.ai/

### 3. 初始化数据库（1 分钟）

```bash
python scripts/init_db.py
```

你应该看到：
```
✓ Database tables created
✓ Tools registered
✓ Skills indexed to ChromaDB
Database initialization complete!
```

### 4. 启动聊天（立即开始）

```bash
python chat.py
```

### 5. 试试这些命令

**文件操作**：
```
你: 帮我读取 README.md 文件
你: 列出当前目录的所有 Python 文件
```

**任务管理**：
```
你: 帮我创建一个学习 Python 的任务
你: 搜索关于学习的任务
你: 我想记录一个想法：做一个个人博客
```

**简单对话**：
```
你: 你好
```

## 可用命令

- `/help` - 显示帮助
- `/clear` - 清除对话历史
- `/exit` - 退出

## 功能特性

✅ **本地优先**: SQLite + ChromaDB，数据完全本地存储  
✅ **Skill 系统**: 动态工具加载和智能 Skill 选择  
✅ **文件操作**: 读取、编辑、创建文件（带 diff 预览）  
✅ **任务管理**: 创建、搜索、更新任务（语义检索）  
✅ **安全操作**: 所有文件写操作需要用户确认  
✅ **语义记忆**: 对话历史向量化，支持语义检索  

## 需要帮助？

查看完整文档：`README.md`  
集成报告：`INTEGRATION_REPORT.md`

## License

MIT
