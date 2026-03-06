#!/bin/bash
# execution-policy-common.sh - 通用拦截函数
#
# 用法:
#   source tools/execution-policy-common.sh
#   guard_completion <task_id> <message>
#
# 返回:
#   0 = ALLOW, 可以输出
#   1 = BLOCK, 必须先调用 verify-and-close

WORKSPACE="$HOME/.openclaw/workspace"
FINALIZE_RESPONSE="$WORKSPACE/tools/finalize-response"
OUTPUT_INTERCEPTOR="$WORKSPACE/tools/output-interceptor"

guard_completion() {
    local task_id="$1"
    local message="${2:-}"
    local channel="${3:-cli_summary}"
    
    if [ -z "$task_id" ]; then
        echo "ERROR: task_id required" >&2
        return 2
    fi
    
    # 调用 output-interceptor
    if [ -n "$message" ]; then
        result=$("$OUTPUT_INTERCEPTOR" \
            --task-id "$task_id" \
            --channel "$channel" \
            --message "$message" \
            --json 2>/dev/null)
    else
        result=$("$OUTPUT_INTERCEPTOR" \
            --task-id "$task_id" \
            --channel "$channel" \
            --json 2>/dev/null)
    fi
    
    action=$(echo "$result" | grep -o '"action": *"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"/\1/')
    
    if [ "$action" = "ALLOW" ]; then
        return 0
    else
        echo "❌ BLOCKED: $result" >&2
        echo "Run: verify-and-close --task-id $task_id" >&2
        return 1
    fi
}

# 快捷函数：检查 receipt 是否存在
check_receipts() {
    local task_id="$1"
    local receipt_dir="$WORKSPACE/artifacts/receipts"
    
    for rtype in contract e2e preflight final; do
        if [ ! -f "$receipt_dir/${task_id}_${rtype}_receipt.json" ]; then
            echo "Missing: $rtype receipt"
            return 1
        fi
    done
    
    return 0
}

# 快捷函数：生成 receipts
generate_receipts() {
    local task_id="$1"
    shift
    
    "$WORKSPACE/tools/verify-and-close" --task-id "$task_id" "$@"
}
