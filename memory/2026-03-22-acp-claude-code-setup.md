# 会话归档：ACP + Claude Code 配置

## 日期
2026-03-22

## 主要任务
配置 OpenClaw 通过 ACP 调用本地 Claude Code，使用千帆 Coding Plan API。

## 完成项

### 1. ACP 插件配置
- 安装并启用 `acpx` 插件
- 配置 `~/.acpx/config.json`:
  ```json
  {
    "defaultAgent": "claude",
    "defaultPermissions": "approve-all",
    "agents": {
      "claude": {
        "command": "/home/moonlight/.local/bin/claude-qianfan"
      }
    }
  }
  ```

### 2. 千帆 API 包装脚本
- 创建 `~/.local/bin/claude-qianfan`
- 使用 `kimi-k2.5` 模型（唯一支持的模型）
- 环境变量：
  - `ANTHROPIC_AUTH_TOKEN`: bce-v3/ALTAKSP-...
  - `ANTHROPIC_BASE_URL`: https://qianfan.baidubce.com/anthropic/coding
  - `ANTHROPIC_MODEL`: kimi-k2.5

### 3. 项目提示词文件
创建 `.claude.md` 文件：
- `/home/moonlight/Project/Github/MyProject/EgoCore/.claude.md`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/.claude.md`
- `/home/moonlight/Project/Github/MyProject/.claude.md`（共享上下文）

### 4. 执行的任务
- 修复 `heuristic_parse()` 收窄职责
- 修复 `parser_source` 保真
- 更新测试用例

## 关键发现

### API 模型支持
- `kimi-k2.5` ✅ 支持
- `glm-5`, `glm-4.7`, `deepseek-v3.2` ❌ 不支持
- 其他模型返回 `coding_plan_model_not_supported`

### .claude.md 查找机制
- Claude Code 只自动读取当前工作目录下的 `.claude.md`
- 不会向上查找父目录
- `--add-dir` 参数不会触发额外目录的 `.claude.md` 自动加载

## 使用方式

### 命令行
```bash
cd /home/moonlight/Project/Github/MyProject/EgoCore
acpx --approve-all claude exec "任务描述"
```

### OpenClaw 调用
```
sessions_spawn(runtime="acp", agentId="claude", task="任务")
```

## 未解决问题
- JSON-RPC 通知解析警告（`usage_update` 格式不兼容）
- 不影响核心功能，但会有大量警告日志

## 文件清单
- `~/.local/bin/claude-qianfan` - 包装脚本
- `~/.acpx/config.json` - acpx 配置
- `~/.openclaw/openclaw.json` - OpenClaw ACP 配置
