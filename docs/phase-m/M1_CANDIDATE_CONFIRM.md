# Phase M-1: pilot 候选确认

**日期**: 2026-03-17

---

## Batch M1 候选

### default

#### 目录结构
total 20
drwxrwxr-x  5 moonlight moonlight 4096 Mar 16 21:56 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 10:42 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar 16 21:56 receipts
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 10:25 sessions

#### 用途
- 通用备选 agent
- 无特殊权限需求
- 无代码执行需求

#### 风险评估
| 项目 | 评估 |
|------|------|
| 权限需求 | 低 |
| 数据访问 | 无敏感数据 |
| 外部通信 | 无 |
| 可逆性 | 高 |

---

### healthcheck

#### 目录结构
total 16
drwxrwxr-x  4 moonlight moonlight 4096 Mar  2 00:30 .
drwx------ 20 moonlight moonlight 4096 Mar 16 22:14 ..
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 00:30 agent
drwxrwxr-x  2 moonlight moonlight 4096 Mar  2 00:24 sessions

#### 用途
- 健康检查专用 agent
- 只读操作
- 无状态变更

#### 风险评估
| 项目 | 评估 |
|------|------|
| 权限需求 | 低 |
| 数据访问 | 只读状态 |
| 外部通信 | 无 |
| 可逆性 | 高 |

---

## 候选确认结论

| Agent | 目录状态 | 风险等级 | 推荐进入 pilot |
|-------|----------|----------|----------------|
| default | 完整 | 低 | ✅ |
| healthcheck | 完整 | 低 | ✅ |

---
**M1 状态**: ✅ 候选确认完成
