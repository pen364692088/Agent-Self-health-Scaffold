# PHASE2_PATH_COVERAGE_REPORT
## Message Ordering Conflict - Phase 2 路径覆盖报告

**评估时间**: 2026-03-11 03:50 UTC  
**评估者**: Manager (Coordinator AI)  
**状态**: ⚠️ PARTIAL (需补齐两条路径)

---

## 1. Phase 2 路径识别

### 1.1 路径清单

| 路径ID | 路径描述 | 文件 | 优先级 | 当前状态 |
|--------|----------|------|--------|----------|
| P2-01 | session-manager-init.ts (restore 后) | `src/agents/pi-embedded-runner/session-manager-init.ts` | P1.5 | ⚠️ 未覆盖 |
| P2-02 | session-file-repair.ts (持久化前) | `src/agents/session-file-repair.ts` | P2 | ⚠️ 未覆盖 |
| P2-03 | session-transcript-repair.ts (transcript 修复) | `src/agents/session-transcript-repair.ts` | P2 | ⚠️ 未覆盖 |

---

## 2. 路径分析

### 2.1 P2-01: session-manager-init.ts

**当前代码**:
```typescript
export async function prepareSessionManagerForRun(params: {
  sessionManager: unknown;
  sessionFile: string;
  hadSessionFile: boolean;
  sessionId: string;
  cwd: string;
}): Promise<void> {
  // ... 现有逻辑 ...
  
  if (params.hadSessionFile && header && !hasAssistant) {
    // Reset file so the first assistant flush includes header+user+assistant in order.
    await fs.writeFile(params.sessionFile, "", "utf-8");
    sm.fileEntries = [header];
    sm.byId?.clear?.();
    sm.labelsById?.clear?.();
    sm.leafId = null;
    sm.flushed = false;
  }
}
```

**问题分析**:
- 此函数在 session 启动时调用
- 如果 `hadSessionFile` 为 true 且没有 assistant 消息，会重置 file
- 但**没有验证消息角色顺序**
- 如果持久化文件中有损坏的角色顺序，会被重新加载

**建议修复**:
```typescript
import { normalizeMessageSequence } from "../pi-embedded-helpers/turns.js";

export async function prepareSessionManagerForRun(params: {
  // ... 现有参数 ...
}): Promise<void> {
  // ... 现有逻辑 ...
  
  // 在重置后验证消息顺序
  if (params.hadSessionFile && header && !hasAssistant) {
    // ... 现有重置逻辑 ...
    
    // 验证并修复消息角色顺序
    const messageEntries = sm.fileEntries.filter(e => e.type === "message");
    const messages = messageEntries.map(e => (e as SessionMessageEntry).message);
    const { messages: normalized, metrics } = normalizeMessageSequence(messages as AgentMessage[]);
    
    if (metrics.totalRepairs > 0) {
      // 更新 fileEntries
      let msgIdx = 0;
      sm.fileEntries = sm.fileEntries.map(e => {
        if (e.type === "message") {
          return { type: "message", message: normalized[msgIdx++] };
        }
        return e;
      });
      
      log.info(`[session-manager-init] Repaired ${metrics.totalRepairs} role ordering issues during init`);
    }
  }
}
```

---

### 2.2 P2-02: session-file-repair.ts

**当前代码**:
```typescript
export async function repairSessionFileIfNeeded(params: {
  sessionFile: string;
  warn?: (message: string) => void;
}): Promise<RepairReport> {
  // ... 读取和解析逻辑 ...
  
  // 只检查 session header 和 JSON 格式
  if (!isSessionHeader(entries[0])) {
    return { repaired: false, droppedLines, reason: "invalid session header" };
  }
  
  // 只清理格式错误的行
  if (droppedLines === 0) {
    return { repaired: false, droppedLines: 0 };
  }
  
  // 写回清理后的内容
  // ...
}
```

**问题分析**:
- 此函数修复 session 文件格式问题
- 只检查 JSON 格式和 session header
- **不验证消息角色顺序**
- 如果文件中有角色顺序问题，会被保留

**建议修复**:
```typescript
import { normalizeMessageSequence, validateMessageSequence } from "./pi-embedded-helpers/turns.js";

export async function repairSessionFileIfNeeded(params: {
  sessionFile: string;
  warn?: (message: string) => void;
}): Promise<RepairReport & { roleOrderingRepairs?: number }> {
  // ... 现有逻辑 ...
  
  // 提取消息并验证角色顺序
  const messageEntries = entries.filter(e => e.type === "message");
  const messages = messageEntries.map(e => e.message);
  
  if (!validateMessageSequence(messages as AgentMessage[])) {
    params.warn?.(`session file has role ordering issues, repairing... (${path.basename(sessionFile)})`);
    
    const { messages: normalized, metrics } = normalizeMessageSequence(messages as AgentMessage[]);
    
    // 更新 entries
    let msgIdx = 0;
    const repairedEntries = entries.map(e => {
      if (e.type === "message") {
        return { ...e, message: normalized[msgIdx++] };
      }
      return e;
    });
    
    // 写回修复后的内容
    const cleaned = `${repairedEntries.map((entry) => JSON.stringify(entry)).join("\n")}\n`;
    // ... 写入逻辑 ...
    
    return { 
      repaired: true, 
      droppedLines, 
      backupPath,
      roleOrderingRepairs: metrics.totalRepairs 
    };
  }
  
  // ... 现有返回逻辑 ...
}
```

---

### 2.3 P2-03: session-transcript-repair.ts

**当前代码**:
```typescript
export function repairToolCallInputs(
  messages: AgentMessage[],
  options?: ToolCallInputRepairOptions,
): ToolCallInputRepairReport {
  // 只修复 tool call 输入问题
  // 不验证消息角色顺序
}

export function sanitizeToolUseResultPairing(messages: AgentMessage[]): AgentMessage[] {
  // 只修复 tool_use/tool_result 配对问题
  // 不验证消息角色顺序
}
```

**问题分析**:
- 此文件处理 tool call 相关的修复
- 不直接涉及消息角色顺序
- 但可能在修复过程中破坏角色顺序

**建议**:
- 在修复后添加角色顺序验证
- 或确保修复逻辑不会破坏顺序

---

## 3. 覆盖状态

### 3.1 全链路覆盖评估

| 路径类型 | 路径数 | 已覆盖 | 覆盖率 |
|----------|--------|--------|--------|
| 热路径 (compaction/attempt) | 3 | 3 | 100% |
| Phase 2 路径 (init/repair) | 3 | 0 | 0% |
| **总计** | **6** | **3** | **50%** |

### 3.2 风险分析

| 路径 | 风险级别 | 说明 |
|------|----------|------|
| P2-01 session-manager-init | 中 | restore 可能带入旧状态 |
| P2-02 session-file-repair | 中 | 坏序列可能落盘 |
| P2-03 session-transcript-repair | 低 | 主要处理 tool call |

---

## 4. 建议行动

### 4.1 立即行动 (P1.5)

**P2-01: session-manager-init.ts**
- [ ] 添加 normalizeMessageSequence 导入
- [ ] 在重置逻辑后添加验证
- [ ] 添加日志记录
- [ ] 添加单元测试
- **预计时间**: 2-4 小时

### 4.2 短期行动 (P2)

**P2-02: session-file-repair.ts**
- [ ] 添加 normalizeMessageSequence 导入
- [ ] 添加角色顺序验证逻辑
- [ ] 更新 RepairReport 类型
- [ ] 添加单元测试
- **预计时间**: 2-4 小时

**P2-03: session-transcript-repair.ts**
- [ ] 审查现有修复逻辑
- [ ] 确保不破坏角色顺序
- [ ] 可选：添加验证步骤
- **预计时间**: 1-2 小时

---

## 5. 结论

### 5.1 当前状态

**PHASE2_PATH_COVERAGE**: ⚠️ **PARTIAL**

- ✅ 热路径 100% 覆盖
- ❌ Phase 2 路径 0% 覆盖
- ⚠️ 全链路覆盖 50%

### 5.2 关闭标准

要达到 **CLOSED** 状态，需要：

| 标准 | 要求 | 当前 |
|------|------|------|
| P2-01 修复 | session-manager-init 添加验证 | ❌ 未实施 |
| P2-02 修复 | session-file-repair 添加验证 | ❌ 未实施 |
| P2-03 审查 | session-transcript-repair 审查 | ❌ 未实施 |
| 单元测试 | 新增测试通过 | ❌ 未实施 |

### 5.3 建议

1. **短期**: 实施 P2-01 和 P2-02 修复 (4-8 小时)
2. **中期**: 添加单元测试和集成测试 (4-8 小时)
3. **长期**: 全链路验证自动化

---

**报告完成**: 2026-03-11 03:55 UTC  
**状态**: PARTIAL - 需补齐 Phase 2 路径
