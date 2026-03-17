# Phase M-P0: Pilot Ingress Prerequisite Repair

## 问题
- default / healthcheck 当前没有真实可用 pilot 入口
- runtime="acp" 报 ACP runtime backend is not configured
- runtime="subagent" 报 agentId is not allowed

## 目标
确认并修复 pilot 入口，拿到至少一条真实成功调用证据。

## 执行步骤
1. 确认正式 pilot 主入口（ACP 或 subagent）
2. 若是 ACP：安装并启用 acpx runtime plugin
3. 若是 subagent：找到并修改 sessions_spawn allowed 配置
4. 验证调用成功
5. 修正文档口径

## 完成标准
- 至少一条真实成功调用证据
- default / healthcheck 可通过 pilot 入口调用
