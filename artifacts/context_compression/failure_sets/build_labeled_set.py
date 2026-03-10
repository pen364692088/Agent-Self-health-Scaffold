#!/usr/bin/env python3
"""
构建 correct_topic_wrong_anchor 失败样本标注集

从现有样本中提取分析，标注：
- chosen_anchor: 系统选择的锚点
- expected_anchor: 应该选择的关键锚点
- anchor_error_type: 错误类型分类
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import re

SAMPLES_DIR = Path("/home/moonlight/.openclaw/workspace/artifacts/context_compression/validation/samples")
REPORTS_DIR = Path("/home/moonlight/.openclaw/workspace/artifacts/context_compression/validation/reports")
OUTPUT_DIR = Path("/home/moonlight/.openclaw/workspace/artifacts/context_compression/failure_sets")

# Anchor error taxonomy
ANCHOR_ERROR_TAXONOMY = {
    "missing_critical_decision": {
        "description": "缺少关键决策锚点（如方案选择、分支决定）",
        "impact": "恢复后无法知道走了哪条路"
    },
    "missing_file_path": {
        "description": "缺少关键文件路径锚点",
        "impact": "恢复后不知道操作的是哪个文件"
    },
    "missing_tool_result": {
        "description": "缺少工具执行结果锚点",
        "impact": "恢复后不知道工具执行到哪一步"
    },
    "missing_constraint_update": {
        "description": "缺少约束更新锚点",
        "impact": "恢复后继续用过时约束"
    },
    "missing_id_reference": {
        "description": "缺少 ID/引用锚点",
        "impact": "恢复后无法定位具体对象"
    },
    "wrong_priority_anchor": {
        "description": "选择了低优先级锚点而非高优先级",
        "impact": "背景信息太多，关键信息被淹没"
    },
    "stale_anchor": {
        "description": "选择了过时锚点",
        "impact": "恢复后用过时信息继续"
    }
}


def extract_expected_anchors_from_events(events):
    """从事件中推断期望的关键锚点"""
    expected = {
        "decisions": [],
        "file_paths": [],
        "tool_states": [],
        "ids": [],
        "constraints": [],
        "open_loops": []
    }
    
    # 关键决策模式
    decision_patterns = [
        (r"决定[是为用](.+?)(?:，|$)", "decision"),
        (r"选择(.+?)方案", "decision"),
        (r"确认使用(.+?)(?:，|$)", "decision"),
        (r"最终采用(.+?)(?:，|$)", "decision"),
        (r"we (?:will |decide to |decided to )(.+?)(?:\.|,|$)", "decision"),
    ]
    
    # 文件路径模式
    file_patterns = [
        (r"([/\w\-\.]+\.(py|js|ts|json|md|sh|yaml|yml|toml))", "file"),
        (r"文件[：:]\s*(\S+)", "file"),
        (r"修改[了]?\s*(\S+\.\w+)", "file"),
    ]
    
    # ID 模式
    id_patterns = [
        (r"ID[：:]\s*([a-f0-9\-]{8,})", "id"),
        (r"session[_\-]?id[：:]\s*([a-f0-9\-]+)", "id"),
        (r"#(\d+)", "issue_number"),
    ]
    
    # 约束模式
    constraint_patterns = [
        (r"必须(.+?)(?:，|$)", "constraint"),
        (r"不能(.+?)(?:，|$)", "constraint"),
        (r"不要(.+?)(?:，|$)", "constraint"),
        (r"禁止(.+?)(?:，|$)", "constraint"),
    ]
    
    # 工具状态模式
    tool_patterns = [
        (r"执行[了]?\s*(\w+)", "tool_call"),
        (r"运行[了]?\s*(\w+)", "tool_call"),
        (r"(\w+)\s*(?:成功|失败|完成)", "tool_result"),
    ]
    
    for event in events:
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        if not content:
            continue
            
        # 提取各类锚点
        for pattern, ptype in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if len(m.strip()) > 5:
                    expected["decisions"].append({
                        "content": m.strip(),
                        "source": "event"
                    })
        
        for pattern, ptype in file_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if len(m) > 3:
                    expected["file_paths"].append({
                        "path": m,
                        "source": "event"
                    })
        
        for pattern, ptype in id_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if len(m) > 3:
                    expected["ids"].append({
                        "id": m,
                        "type": ptype
                    })
        
        for pattern, ptype in constraint_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if len(m.strip()) > 3:
                    expected["constraints"].append({
                        "content": m.strip(),
                        "source": "event"
                    })
        
        for pattern, ptype in tool_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if len(m.strip()) > 2:
                    expected["tool_states"].append({
                        "tool": m.strip(),
                        "type": ptype
                    })
    
    # 去重
    for key in expected:
        seen = set()
        unique = []
        for item in expected[key]:
            key_val = item.get("content", item.get("path", item.get("id", item.get("tool", ""))))
            if key_val and key_val not in seen:
                seen.add(key_val)
                unique.append(item)
        expected[key] = unique
    
    return expected


def diagnose_anchor_error(sample_data, expected_anchors):
    """诊断 anchor 错误类型"""
    errors = []
    
    # 检查是否缺少关键决策
    if expected_anchors["decisions"]:
        errors.append({
            "error_type": "missing_critical_decision",
            "severity": "high",
            "count": len(expected_anchors["decisions"]),
            "examples": expected_anchors["decisions"][:3]
        })
    
    # 检查是否缺少文件路径
    if expected_anchors["file_paths"]:
        errors.append({
            "error_type": "missing_file_path",
            "severity": "high",
            "count": len(expected_anchors["file_paths"]),
            "examples": expected_anchors["file_paths"][:3]
        })
    
    # 检查是否缺少工具状态
    if expected_anchors["tool_states"]:
        errors.append({
            "error_type": "missing_tool_result",
            "severity": "medium",
            "count": len(expected_anchors["tool_states"]),
            "examples": expected_anchors["tool_states"][:3]
        })
    
    # 检查是否缺少 ID
    if expected_anchors["ids"]:
        errors.append({
            "error_type": "missing_id_reference",
            "severity": "medium",
            "count": len(expected_anchors["ids"]),
            "examples": expected_anchors["ids"][:3]
        })
    
    # 检查是否缺少约束
    if expected_anchors["constraints"]:
        errors.append({
            "error_type": "missing_constraint_update",
            "severity": "medium",
            "count": len(expected_anchors["constraints"]),
            "examples": expected_anchors["constraints"][:3]
        })
    
    return errors


def process_sample(sample_path):
    """处理单个样本"""
    with open(sample_path) as f:
        data = json.load(f)
    
    sample_id = data.get("metadata", {}).get("sample_id", sample_path.stem)
    events = data.get("events", [])
    
    # 提取期望锚点
    expected = extract_expected_anchors_from_events(events)
    
    # 诊断错误
    errors = diagnose_anchor_error(data, expected)
    
    return {
        "sample_id": sample_id,
        "session_id": data.get("metadata", {}).get("session_id", ""),
        "source_type": data.get("metadata", {}).get("source_type", ""),
        "event_count": len(events),
        "expected_anchors": expected,
        "diagnosed_errors": errors,
        "primary_error_type": errors[0]["error_type"] if errors else "unknown",
        "error_count": len(errors)
    }


def main():
    import glob
    
    # 获取所有 old_topic_recall 样本
    sample_files = list(SAMPLES_DIR.glob("sample_*_old_topic_recall_*.json"))
    
    results = []
    error_counts = defaultdict(int)
    
    for sample_path in sample_files[:30]:  # 限制 30 个
        try:
            result = process_sample(sample_path)
            results.append(result)
            
            for error in result["diagnosed_errors"]:
                error_counts[error["error_type"]] += 1
                
        except Exception as e:
            print(f"Error processing {sample_path}: {e}", file=sys.stderr)
    
    # 写入结果
    output_file = OUTPUT_DIR / "correct_topic_wrong_anchor_labeled.jsonl"
    with open(output_file, 'w') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    # 生成摘要
    print(f"✅ 已处理 {len(results)} 个样本")
    print(f"📄 输出: {output_file}")
    print("\n错误类型分布:")
    for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        print(f"  {error_type}: {count}")


if __name__ == "__main__":
    main()
