# SELF_HEALING_BOUNDARIES.md

## 禁止自动修改区域

### 绝对禁区

以下文件/目录**绝对禁止**自动修复系统修改：

#### 1. 核心身份与系统提示
```
SOUL.md
IDENTITY.md
USER.md
AGENTS.md
BOOTSTRAP.md
```

**原因**：这些文件定义了系统的核心身份、价值观和行为准则。自动修改可能导致系统行为偏离设计目标。

#### 2. 安全策略
```
POLICIES/
SECURITY.md
PERMISSIONS.md
```

**原因**：安全策略是系统的防护边界，自动修改可能引入安全漏洞。

#### 3. 凭据与密钥
```
.env
.env.*
secrets/
*.key
*.pem
config/credentials*
```

**原因**：凭据信息敏感，自动修改可能导致泄露或失效。

#### 4. 主调度器核心
```
tools/subtask-orchestrate
tools/spawn-with-callback
tools/callback-worker
tools/subagent-inbox
tools/subagent-completion-handler
```

**原因**：这些是子代理编排的核心组件，修改可能导致整个编排系统失效。

#### 5. Gate 验证器
```
tools/verify-and-close
tools/done-guard
tools/finalize-response
tools/safe-message
tools/output-interceptor
```

**原因**：Gate 是任务完成的最后一道防线，修改可能导致不安全的内容被放行。

#### 6. 自愈系统自身
```
SELF_HEALING_CONTRACT.md
SELF_HEALING_BOUNDARIES.md
SELF_HEALING_LEVELS.md
src/self_healing/core/
```

**原因**：自愈系统不能修改自己的边界约束，否则可能导致"自毁"。

---

## 高风险区域（需额外审批）

以下区域修改需要 L3 级别审批：

```
tools/                    # 工具脚本（非核心）
scripts/                  # 运行脚本
config/action_policy.json # 动作策略
```

---

## 允许自动修复区域

以下区域可以自动修复（仍需通过 Gate）：

```
src/                      # 业务代码
tests/                    # 测试代码
docs/                     # 文档
examples/                 # 示例
```

---

## 路径匹配规则

### 精确匹配
```yaml
blocked_exact:
  - "SOUL.md"
  - "IDENTITY.md"
  - "SELF_HEALING_CONTRACT.md"
```

### 前缀匹配
```yaml
blocked_prefix:
  - "POLICIES/"
  - "secrets/"
  - "tools/subtask-orchestrate"
  - "tools/callback-worker"
```

### 模式匹配
```yaml
blocked_patterns:
  - "*.key"
  - "*.pem"
  - ".env*"
```

---

## 运行时检查

在每次自动修复前，系统必须执行：

```python
def check_boundary(target_path: str) -> bool:
    """
    检查目标路径是否在禁区
    
    Returns:
        True: 允许修改
        False: 禁止修改
    """
    # 1. 精确匹配
    if target_path in BLOCKED_EXACT:
        return False
    
    # 2. 前缀匹配
    for prefix in BLOCKED_PREFIX:
        if target_path.startswith(prefix):
            return False
    
    # 3. 模式匹配
    for pattern in BLOCKED_PATTERNS:
        if fnmatch(target_path, pattern):
            return False
    
    return True
```

---

## 违规处理

如果检测到对禁区的修改尝试：

1. **立即拦截**：阻止修改操作
2. **记录审计**：记录到 security_audit.log
3. **升级人工**：通知管理员审查
4. **降级处理**：将自动级别降至 L0（仅观察）

---

*边界定义版本: 1.0*
*生效日期: 2026-03-14*
