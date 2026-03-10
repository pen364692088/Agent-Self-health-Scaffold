#!/usr/bin/env python3
"""
V1 vs V2 Replay Evaluation

对同一批样本分别用 V1 和 V2 生成 capsule，对比恢复效果。
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SAMPLES_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation" / "samples"
OUTPUT_DIR = WORKSPACE / "artifacts" / "context_compression" / "replay"
CAPSULE_BUILDER_V2 = WORKSPACE / "tools" / "capsule-builder-v2.py"


def load_sample(sample_path: Path) -> Dict:
    """加载样本数据"""
    with open(sample_path) as f:
        return json.load(f)


def extract_events_for_replay(sample_data: Dict) -> List[Dict]:
    """提取用于回放的事件"""
    events = sample_data.get("events", [])
    messages = []
    
    for event in events:
        # 标准化事件格式
        msg = {
            "turn": event.get("turn", len(messages) + 1),
            "role": event.get("role", ""),
            "content": event.get("content", ""),
            "tool_name": event.get("tool_name", ""),
            "status": event.get("status", "")
        }
        
        # 处理嵌套结构
        if "message" in event:
            msg["role"] = event["message"].get("role", msg["role"])
            content = event["message"].get("content", "")
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                msg["content"] = " ".join(text_parts)
            else:
                msg["content"] = str(content)
        
        if msg["content"] or msg["tool_name"]:
            messages.append(msg)
    
    return messages


def evaluate_v1_capsule(messages: List[Dict]) -> Dict:
    """V1 评估：基于实体频率和简单模式匹配"""
    entity_count = 0
    decision_patterns = ["决定", "选择", "确认", "最终"]
    open_loop_patterns = ["TODO", "TBD", "待", "尚未"]
    constraint_patterns = ["必须", "不能", "不要", "禁止"]
    
    decisions = []
    open_loops = []
    constraints = []
    entities = []
    tool_states = []
    
    combined_text = ""
    for msg in messages:
        content = msg.get("content", "")
        if content:
            combined_text += content + "\n"
            
            # 简单模式匹配
            for pattern in decision_patterns:
                if pattern in content:
                    idx = content.find(pattern)
                    decisions.append(content[max(0, idx-10):idx+50])
            
            for pattern in open_loop_patterns:
                if pattern in content:
                    idx = content.find(pattern)
                    open_loops.append(content[max(0, idx-5):idx+40])
            
            for pattern in constraint_patterns:
                if pattern in content:
                    idx = content.find(pattern)
                    constraints.append(content[max(0, idx-5):idx+40])
            
            # 工具状态
            if msg.get("tool_name"):
                tool_states.append({
                    "tool": msg["tool_name"],
                    "status": msg.get("status", "called")
                })
            
            # 实体计数
            words = content.split()
            entity_count += len(words)
    
    # 去重
    decisions = list(set(decisions))[:5]
    open_loops = list(set(open_loops))[:5]
    constraints = list(set(constraints))[:5]
    
    # V1 readiness (基于有无提取到内容)
    readiness = sum([
        0.25 if decisions else 0,
        0.25 if entities else 0,
        0.25 if tool_states else 0,
        0.25 if (constraints or open_loops) else 0
    ])
    
    return {
        "version": "v1",
        "entity_count": entity_count,
        "decisions": len(decisions),
        "open_loops": len(open_loops),
        "constraints": len(constraints),
        "tool_states": len(tool_states),
        "resume_readiness": readiness,
        "anchor_quality": "low" if entity_count < 1000 else "medium"
    }


def evaluate_v2_capsule(messages: List[Dict]) -> Dict:
    """V2 评估：基于结构化锚点"""
    import re
    
    # 多维度锚点
    decision_anchors = []
    file_path_anchors = []
    tool_state_anchors = []
    constraint_anchors = []
    open_loop_anchors = []
    
    total = len(messages)
    
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        recency = (i + 1) / total if total > 0 else 0
        
        # 决策锚点
        decision_patterns = [
            (r"决定(.+?)(?:，|。|$)", 1.0),
            (r"选择(.+?)方案", 0.9),
            (r"确认(.+?)(?:，|。|$)", 0.8)
        ]
        for pattern, weight in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if len(m.strip()) > 5:
                    decision_anchors.append({
                        "content": m.strip()[:100],
                        "score": weight * 0.95 * (0.5 + 0.5 * recency)
                    })
        
        # 文件路径锚点
        file_pattern = r"([/\w\-\.]+\.(py|js|ts|json|md|sh|yaml|yml|toml))"
        for match in re.findall(file_pattern, content):
            path = match[0] if isinstance(match, tuple) else match
            file_path_anchors.append({
                "content": path,
                "score": 0.90 * (0.5 + 0.5 * recency)
            })
        
        # 工具状态锚点
        if msg.get("tool_name"):
            tool_state_anchors.append({
                "tool": msg["tool_name"],
                "status": msg.get("status", "called"),
                "score": 0.90 * recency if msg.get("status") == "called" else 0.70 * recency
            })
        
        # 约束锚点
        constraint_patterns = [(r"必须(.+?)(?:，|。|$)", "must"), (r"不能(.+?)(?:，|。|$)", "cannot")]
        for pattern, ctype in constraint_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if len(m.strip()) > 3:
                    constraint_anchors.append({
                        "content": f"{ctype}: {m.strip()}",
                        "score": 0.85
                    })
        
        # Open Loop 锚点
        open_loop_patterns = [r"TODO[:：]?\s*(.+?)(?:，|。|$)", r"待(.+?)(?:，|。|$)"]
        for pattern in open_loop_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if len(m.strip()) > 3:
                    open_loop_anchors.append({
                        "content": m.strip()[:80],
                        "score": 0.75 * (0.5 + 0.5 * recency)
                    })
    
    # 去重并排序
    decision_anchors = sorted(decision_anchors, key=lambda x: -x["score"])[:5]
    file_path_anchors = sorted(file_path_anchors, key=lambda x: -x["score"])[:10]
    tool_state_anchors = sorted(tool_state_anchors, key=lambda x: -x["score"])[:10]
    
    # 计算 readiness
    readiness = sum([
        0.25 if decision_anchors else 0,
        0.25 if file_path_anchors else 0,
        0.25 if tool_state_anchors else 0,
        0.25 if (constraint_anchors or open_loop_anchors) else 0
    ])
    
    # 计算 anchor quality
    anchor_score = sum(
        a["score"] for a in decision_anchors + file_path_anchors + tool_state_anchors
    ) / max(1, len(decision_anchors + file_path_anchors + tool_state_anchors))
    
    anchor_quality = "high" if anchor_score > 0.8 else "medium" if anchor_score > 0.5 else "low"
    
    return {
        "version": "v2",
        "decision_anchors": len(decision_anchors),
        "file_path_anchors": len(file_path_anchors),
        "tool_state_anchors": len(tool_state_anchors),
        "constraint_anchors": len(constraint_anchors),
        "open_loop_anchors": len(open_loop_anchors),
        "resume_readiness": readiness,
        "anchor_quality": anchor_quality,
        "avg_anchor_score": round(anchor_score, 2)
    }


def determine_failure_type(v1_result: Dict, v2_result: Dict) -> Tuple[str, str]:
    """判断失败类型"""
    v1_failure = "none"
    v2_failure = "none"
    
    # V1 失败判断
    if v1_result["resume_readiness"] < 0.5:
        if v1_result["decisions"] == 0:
            v1_failure = "correct_topic_wrong_anchor"
        elif v1_result["tool_states"] == 0:
            v1_failure = "topic_recalled_but_tool_state_missing"
        else:
            v1_failure = "insufficient_anchors"
    
    # V2 失败判断
    if v2_result["resume_readiness"] < 0.5:
        if v2_result["decision_anchors"] == 0 and v2_result["file_path_anchors"] == 0:
            v2_failure = "correct_topic_wrong_anchor"
        elif v2_result["tool_state_anchors"] == 0:
            v2_failure = "topic_recalled_but_tool_state_missing"
        else:
            v2_failure = "insufficient_anchors"
    
    return v1_failure, v2_failure


def run_replay_evaluation(sample_limit: int = 50) -> Dict:
    """运行回放评估"""
    results = []
    bucket_stats = defaultdict(lambda: {"v1": [], "v2": []})
    
    sample_files = list(SAMPLES_DIR.glob("sample_*.json"))[:sample_limit]
    
    for sample_path in sample_files:
        try:
            sample_data = load_sample(sample_path)
            sample_id = sample_data.get("metadata", {}).get("sample_id", sample_path.stem)
            bucket = sample_data.get("metadata", {}).get("bucket_tags", ["unknown"])[0] if sample_data.get("metadata", {}).get("bucket_tags") else "unknown"
            
            messages = extract_events_for_replay(sample_data)
            
            # V1 评估
            v1_result = evaluate_v1_capsule(messages)
            
            # V2 评估
            v2_result = evaluate_v2_capsule(messages)
            
            # 失败类型
            v1_failure, v2_failure = determine_failure_type(v1_result, v2_result)
            
            # Delta
            readiness_delta = v2_result["resume_readiness"] - v1_result["resume_readiness"]
            
            result = {
                "sample_id": sample_id,
                "bucket": bucket,
                "v1": v1_result,
                "v2": v2_result,
                "v1_failure_type": v1_failure,
                "v2_failure_type": v2_failure,
                "readiness_delta": round(readiness_delta, 2),
                "verdict": "improved" if readiness_delta > 0 else "same" if readiness_delta == 0 else "regressed"
            }
            
            results.append(result)
            bucket_stats[bucket]["v1"].append(v1_result["resume_readiness"])
            bucket_stats[bucket]["v2"].append(v2_result["resume_readiness"])
            
        except Exception as e:
            print(f"Error processing {sample_path}: {e}", file=sys.stderr)
    
    # 汇总统计
    summary = {
        "total_samples": len(results),
        "v1_avg_readiness": sum(r["v1"]["resume_readiness"] for r in results) / len(results) if results else 0,
        "v2_avg_readiness": sum(r["v2"]["resume_readiness"] for r in results) / len(results) if results else 0,
        "improvement_count": sum(1 for r in results if r["verdict"] == "improved"),
        "regression_count": sum(1 for r in results if r["verdict"] == "regressed"),
        "bucket_breakdown": {}
    }
    
    for bucket, stats in bucket_stats.items():
        if stats["v1"] and stats["v2"]:
            summary["bucket_breakdown"][bucket] = {
                "count": len(stats["v1"]),
                "v1_avg": round(sum(stats["v1"]) / len(stats["v1"]), 2),
                "v2_avg": round(sum(stats["v2"]) / len(stats["v2"]), 2),
                "delta": round(sum(stats["v2"]) / len(stats["v2"]) - sum(stats["v1"]) / len(stats["v1"]), 2)
            }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "samples": results
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V1 vs V2 Replay Evaluation")
    parser.add_argument("--limit", type=int, default=50, help="Sample limit")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    result = run_replay_evaluation(args.limit)
    
    # 保存结果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "v1_vs_v2_replay.jsonl"
    with open(output_file, "w") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    # 输出摘要
    summary = result["summary"]
    
    if not args.json:
        print("=" * 60)
        print("V1 vs V2 Replay Evaluation Summary")
        print("=" * 60)
        print(f"\nTotal samples: {summary['total_samples']}")
        print(f"\nV1 avg readiness: {summary['v1_avg_readiness']:.2f}")
        print(f"V2 avg readiness: {summary['v2_avg_readiness']:.2f}")
        print(f"Delta: {summary['v2_avg_readiness'] - summary['v1_avg_readiness']:+.2f}")
        print(f"\nImproved: {summary['improvement_count']}")
        print(f"Regressed: {summary['regression_count']}")
        print(f"\nBucket breakdown:")
        for bucket, stats in sorted(summary["bucket_breakdown"].items()):
            print(f"  {bucket}: v1={stats['v1_avg']:.2f} → v2={stats['v2_avg']:.2f} ({stats['delta']:+.2f})")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
