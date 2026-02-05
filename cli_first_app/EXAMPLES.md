# CLI Agent 使用示例

## 基本对话

### 简单问候（不触发 Skill）

```
你: 你好
助手: 你好！我是你的智能助手，可以帮你管理文件和任务。有什么可以帮到你的吗？
```

## File Operations Skill 示例

### 读取文件

```
你: 帮我读取 README.md 文件

助手: [调用 read_file 工具]

   1 | # CLI Agent - 智能文件操作助手
   2 | 
   3 | 基于 cli-brain-off 的 Skill 系统集成...
   ...
```

### 列出文件

```
你: 列出当前目录的所有 Python 文件

助手: [调用 list_files 工具]

Files in /path/to/project:
  chat.py (2.5 KB)
  src/main.py (3.1 KB)
  src/llm.py (4.2 KB)
  ...
```

### 编辑文件

```
你: 帮我把 README.md 第一行改为 "# My Awesome Project"

助手: 让我先读取文件内容...
[调用 read_file]

现在进行修改...
[调用 apply_edit，显示 diff 预览]

Proposed changes to: README.md
───────────────────────────────
- # CLI Agent - 智能文件操作助手
+ # My Awesome Project

Apply this change? (y/N): y

✓ Successfully applied changes
```

### 创建新文件

```
你: 帮我创建一个 hello.py 文件，内容是 print("Hello World")

助手: [调用 write_file 工具]

About to create file: hello.py
Content length: 21 characters

Proceed to create the file? (y/N): y

✓ Successfully wrote to hello.py
```

## Todo Skill 示例

### 创建任务

```
你: 帮我创建一个学习 Python 的任务

助手: [调用 database_operation 工具]

【创建任务卡："学习 Python"】
【✓ 任务已创建】

已创建任务：
- ID: abc123...
- 标题: 学习 Python
- 状态: inbox
- 创建时间: 2026-02-05 10:30:00
```

### 记录想法

```
你: 我有个想法：做一个个人博客系统

助手: [调用 database_operation 创建 brainstorm 状态任务]

【创建任务卡："做一个个人博客系统"】
【✓ 任务已创建】

已捕获你的想法！
- 标题: 做一个个人博客系统
- 状态: brainstorm（想法）
- 可以之后再细化具体计划
```

### 搜索任务

```
你: 搜索关于学习的任务

助手: [调用 search 工具]

【正在搜索 "学习"】
【找到 3 个结果】

找到以下任务：

1. 学习 Python
   - 状态: inbox
   - 优先级: medium
   - 创建于: 2026-02-05

2. 学习 React
   - 状态: active
   - 优先级: high
   - 创建于: 2026-02-03

3. 学习数据结构
   - 状态: someday
   - 优先级: low
   - 创建于: 2026-02-01
```

### 更新任务状态

```
你: 把"学习 Python"这个任务标记为进行中

助手: [调用 search 找到任务，然后 update_task]

【更新任务】
【✓ 已更新："学习 Python"】

任务已更新：
- 标题: 学习 Python
- 状态: inbox → active
- 更新时间: 2026-02-05 11:00:00
```

### 带标签创建任务

```
你: 创建任务：准备年度总结报告，优先级高，标签：工作、写作

助手: [调用 database_operation]

【创建任务卡："准备年度总结报告"】
【✓ 任务已创建】

已创建任务：
- 标题: 准备年度总结报告
- 状态: inbox
- 优先级: high
- 标签: 工作, 写作
- 创建时间: 2026-02-05 11:15:00
```

## 高级用法

### 组合多个操作

```
你: 帮我创建一个学习计划，包括 3 个子任务：学习基础语法、做练习项目、看源码

助手: [连续调用 3 次 database_operation]

【创建任务卡："学习基础语法"】
【✓ 任务已创建】

【创建任务卡："做练习项目"】
【✓ 任务已创建】

【创建任务卡："看源码"】
【✓ 任务已创建】

已为你创建学习计划的 3 个子任务！
```

### 按条件搜索

```
你: 搜索所有进行中的高优先级任务

助手: [调用 search 工具，带 status_filter 和 priority_filter]

【正在搜索 "进行中 高优先级"】
【找到 2 个结果】

找到以下任务：

1. 准备年度总结报告
   - 状态: active
   - 优先级: high
   - 标签: 工作, 写作

2. 完成项目交付
   - 状态: active
   - 优先级: urgent
   - 标签: 工作, 开发
```

## 命令参考

### CLI 命令

- `/help` - 显示帮助信息
- `/clear` - 清除当前会话的对话历史
- `/stats` - 显示会话统计（消息数量等）
- `/exit` - 退出程序

### 任务状态

- `brainstorm` - 想法、灵感（还没确定要做）
- `inbox` - 待处理（已确定要做，待安排）
- `active` - 进行中（正在执行）
- `waiting` - 等待中（阻塞，等待外部条件）
- `someday` - 将来也许（不紧急，以后再说）
- `completed` - 已完成
- `archived` - 已归档

### 任务优先级

- `urgent` - 紧急（立即处理）
- `high` - 高（重要）
- `medium` - 中（一般）
- `low` - 低（不紧急）
- `none` - 无（未设置）

## 提示和技巧

1. **Skill 自动选择**
   - 系统会根据你的输入自动选择合适的 Skill
   - 文件相关 → File Operations Skill
   - 任务相关 → Todo Skill
   - 简单对话 → 不触发 Skill

2. **语义搜索**
   - 不需要精确匹配关键词
   - 使用自然语言描述即可
   - 例如："找找我要学的东西"会匹配标题包含"学习"的任务

3. **安全确认**
   - 所有文件写操作都需要你的确认
   - 编辑操作会显示 diff 预览
   - 如果不满意可以取消

4. **标签管理**
   - 创建任务时可以添加多个标签
   - 标签会自动创建（不需要预先定义）
   - 可以通过标签组织和查找任务

## 故障排除

### API Key 错误

```
Error: OPENROUTER_API_KEY not found in environment.
```

解决：确保 `.env` 文件中设置了正确的 API Key

### 数据库错误

如果遇到数据库相关错误，尝试重新初始化：

```bash
python scripts/init_db.py
```

### Skills 未加载

运行验证脚本检查：

```bash
python scripts/verify_integration.py
```

## 更多帮助

查看完整文档：
- `README.md` - 完整使用文档
- `QUICKSTART.md` - 快速开始
- `INTEGRATION_REPORT.md` - 集成报告
