# 行为级 E2E 测试报告

**日期**: 2026-03-09 09:45 CST
**测试文件**: tests/test_route_rebind_guard_e2e.py
**通过率**: 4/4 (100%)

---

## 测试场景

### 1. 劫持复现 + 恢复闭环 ✅

**测试步骤**：
1. 创建主 session 并记录
2. 初始路由指向主 session
3. 创建 isolated session（模拟 cron 任务）
4. 模拟 isolated announce + user reply 导致路由被劫持
5. guard 检测到劫持
6. guard 执行恢复
7. 验证路由已恢复到主 session
8. 后续消息验证不再检测到劫持

**验证点**：
- [x] 劫持可被检测
- [x] 恢复目标正确（主 session）
- [x] 恢复后路由稳定
- [x] 审计日志记录

---

### 2. 正常 reply 不误杀 ✅

**测试步骤**：
1. 创建主 session
2. 用户正常 reply（路由不变）
3. guard 多次检查

**验证点**：
- [x] 不误报劫持
- [x] 路由保持正确
- [x] 多次检查稳定

---

### 3. 多 isolated 并发场景 ✅

**测试步骤**：
1. 创建主 session
2. 创建 3 个 isolated session（模拟多个 cron 任务）
3. 最后一个 isolated 劫持路由
4. guard 检测并恢复

**验证点**：
- [x] 正确识别主 session
- [x] 恢复到主 session，而非其他 isolated
- [x] 不在多个 isolated 之间乱恢复

---

### 4. 恢复持久性验证 ✅

**测试步骤**：
1. 创建主 session
2. 连续 3 轮劫持 + 恢复

**验证点**：
- [x] 每次都恢复到正确主 session
- [x] 主 session ID 保持不变
- [x] 恢复机制稳定可靠

---

## 结论

**所有行为级 E2E 测试通过。**

route-rebind-guard 保护层已验证：
- 可检测劫持
- 可正确恢复
- 不误杀正常流量
- 多劫持场景稳定

---

## 仍需验证

**真实环境验证**：
- 需要在真实 OpenClaw 环境中触发 isolated announce
- 需要验证实际 Telegram reply 流程

**建议**：
- 下次 cron 任务执行时，检查 heartbeat 日志
- 确认 guard 在真实劫持场景下的行为

---
Generated: 2026-03-09 09:45 CST
