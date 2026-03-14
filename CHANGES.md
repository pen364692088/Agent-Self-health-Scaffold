# 变更日志

## 2026-03-14

### 修复
- **Telegram Bot 中断问题**
  - 原因：Gateway 配置中缺少 Telegram 配置
  - 修复：添加 `~/.openclaw/config.json` 配置
  - 状态：✅ 已修复

- **subtask-orchestrate PATH 问题**
  - 原因：Agent-Self-health-Scaffold 引入新工具但未更新 PATH
  - 修复：创建符号链接 + 建立 CLI Manifest 系统
  - 状态：✅ 已修复

### 新增
- **CLI Manifest 系统** (`tools/cli-manifest`)
  - Manifest 文件：`tools/cli-manifest.json`
  - 管理脚本：`tools/cli-manifest`
  - 文档：`docs/CLI_MANIFEST.md`
  - 已登记工具：6 个（3 required + 3 optional）

### 修改
- `~/.openclaw/config.json` - 添加 Telegram 配置
- `~/.local/bin/` - 添加符号链接
  - `subtask-orchestrate`
  - `subagent-inbox`
  - `spawn-with-callback`
  - `cli-manifest`

---

## 格式说明

### 变更类型
- `修复` - 修复 bug 或问题
- `新增` - 添加新功能
- `修改` - 修改现有功能
- `移除` - 移除功能

### 状态标记
- ✅ 已完成
- 🔄 进行中
- ⏸️ 暂停
- ❌ 已放弃
