# Phase L-0: 基线冻结与对象确认

**日期**: 2026-03-17
**状态**: 执行中

---

## 正式状态词典 (冻结)

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

**约束**: 不新增状态词典

---

## 对象确认

### Tier 2: manual_enable_only (5 + 1 单独)

| Agent | 风险等级 | 处理方式 |
|-------|----------|----------|
| default | 低 | 批量处理 |
| healthcheck | 低 | 批量处理 |
| acp-codex | 中 | 批量处理 |
| codex | 中 | 批量处理 |
| mvp7-coder | 中 | 批量处理 |
| cc-godmode | 高 | 单独处理 |

---

## 已配置可用 Agents (不修改)

| Agent | 状态 | 备注 |
|-------|------|------|
| main | continue_default_enabled | 主 agent，不触碰 |
| audit | continue_default_enabled | 已配置，不触碰 |
| coder | continue_default_enabled | 已配置，不触碰 |

---

## 基线检查

### 目录结构

#### default
```
total 20
drwxrwxr-x  5 moonlight moonlight 4096 Mar 16 21:56 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 10:42 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar 16 21:56 receipts
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 10:25 sessions
```

#### healthcheck
```
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Mar  2 00:30 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 00:30 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 00:24 sessions
```

#### acp-codex
```
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Feb 28 16:42 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Feb 28 16:42 agent
drwxrwxr-x  2 moonlight moonlight 4096 Feb 28 14:20 sessions
```

#### codex
```
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Mar 12 01:52 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar 12 01:52 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar 15 13:25 sessions
```

#### mvp7-coder
```
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Mar  2 10:42 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 10:42 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 08:07 sessions
```

#### cc-godmode
```
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Mar  2 00:30 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 00:30 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 22:42 sessions
```

---
**L0 状态**: ✅ 基线冻结完成
