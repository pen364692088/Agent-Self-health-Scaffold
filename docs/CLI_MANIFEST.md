# CLI Manifest 系统文档

## 概述

CLI Manifest 系统用于统一管理应暴露到 PATH 的工具，提供可审计、可回滚、可扩展的工具管理机制。

## 核心文件

| 文件 | 路径 | 说明 |
|------|------|------|
| Manifest | `tools/cli-manifest.json` | 工具登记配置 |
| 管理脚本 | `tools/cli-manifest` | 安装/检查/管理命令 |

## 快速开始

```bash
# 检查当前状态
cli-manifest check

# 安装所有 required 工具
cli-manifest install

# 列出所有登记工具
cli-manifest list
```

## 工具登记格式

```json
{
  "tools": {
    "tool-name": {
      "path": "tools/tool-path",
      "category": "orchestration",
      "description": "工具描述",
      "required": true,
      "since": "2026-03-14"
    }
  }
}
```

### 字段说明

- `path`: 工具相对于 workspace 的路径
- `category`: 工具分类（orchestration/state/misc）
- `description`: 工具用途描述
- `required`: 是否必须安装到 PATH
- `since`: 登记日期

## 添加新工具

```bash
# 方式1: 使用命令
cli-manifest add my-tool tools/my-tool.sh orchestration "My tool description" true

# 方式2: 直接编辑 manifest
vim ~/.openclaw/workspace/tools/cli-manifest.json
cli-manifest install
```

## 分类体系

| 分类 | 优先级 | 说明 |
|------|--------|------|
| orchestration | 1 | 子代理编排核心工具 |
| state | 2 | 状态管理工具 |
| misc | 3 | 其他工具 |

## 当前登记工具

### Required（必须）

| 工具 | 分类 | 说明 |
|------|------|------|
| subtask-orchestrate | orchestration | 子代理编排正式入口 |
| subagent-inbox | orchestration | 子代理邮箱管理 |
| spawn-with-callback | orchestration | 带回调的子代理启动 |

### Optional（可选）

| 工具 | 分类 | 说明 |
|------|------|------|
| subagent-completion-handler | orchestration | 子代理完成处理 |
| handle-subagent-complete | orchestration | 子代理完成推进 |
| run-state | state | 运行状态管理 |

## 故障排查

### 工具找不到
```bash
# 检查是否安装
cli-manifest check

# 重新安装
cli-manifest install
```

### 权限问题
```bash
# 确保工具可执行
chmod +x ~/.openclaw/workspace/tools/<tool-name>
```

### PATH 不生效
```bash
# 检查 ~/.local/bin 是否在 PATH
echo $PATH | grep ".local/bin"

# 如果不存在，添加到 ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 历史记录

### 2026-03-14
- 创建 CLI Manifest 系统
- 登记 6 个工具
- 修复 subtask-orchestrate PATH 问题

## 相关文档

- `TOOLS.md` - 工具使用规范
- `SOUL.md` - 执行策略
