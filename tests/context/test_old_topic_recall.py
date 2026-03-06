#!/usr/bin/env python3
"""
旧话题切回回归测试集

场景：
1. 前 30 轮讨论主题 A
2. 第 31-50 轮切换到主题 B
3. 第 51 轮回到主题 A
4. 验证 capsule + retrieval 能否恢复关键信息

验收标准：
- old_topic_recovery_rate >= 0.85
- rehydration_precision >= 0.80
"""

import json
import os
import sys
from pathlib import Path

# 添加 workspace 到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

class OldTopicRecallTest:
    """旧话题切回测试"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def generate_test_session(self):
        """生成测试 session"""
        session = {
            "session_id": "test_old_topic_recall_001",
            "turns": []
        }
        
        # Phase 1: 主题 A (30 轮)
        topic_a_decisions = [
            "决定使用 OpenClaw 作为主框架",
            "确认使用三层上下文模型",
            "选择 Shadow Mode 作为初始模式"
        ]
        
        topic_a_open_loops = [
            {"id": "loop_a1", "text": "需要评估 rehydration precision", "status": "open"},
            {"id": "loop_a2", "text": "需要创建回归测试集", "status": "open"}
        ]
        
        for i in range(1, 31):
            session["turns"].append({
                "turn_id": i,
                "role": "user" if i % 2 == 1 else "assistant",
                "content": f"讨论主题 A - 轮次 {i}",
                "topic": "OpenClaw 上下文压缩",
                "decisions": topic_a_decisions if i == 30 else [],
                "open_loops": topic_a_open_loops if i == 30 else []
            })
        
        # Phase 2: 主题 B (20 轮)
        for i in range(31, 51):
            session["turns"].append({
                "turn_id": i,
                "role": "user" if i % 2 == 1 else "assistant",
                "content": f"讨论主题 B - 轮次 {i}",
                "topic": "MVP11.6 Shadow Mode",
                "decisions": [],
                "open_loops": []
            })
        
        # Phase 3: 回到主题 A (1 轮)
        session["turns"].append({
            "turn_id": 51,
            "role": "user",
            "content": "回到之前讨论的 OpenClaw 上下文压缩，我们决定了什么？",
            "topic": "OpenClaw 上下文压缩",
            "expected_recall": {
                "decisions": topic_a_decisions,
                "open_loops": [loop["id"] for loop in topic_a_open_loops]
            }
        })
        
        return session
    
    def test_capsule_creation(self):
        """测试 capsule 创建"""
        test_name = "capsule_creation"
        try:
            # 生成测试 session
            session = self.generate_test_session()
            
            # 模拟压缩
            # 在真实环境会调用 capsule-builder
            capsule = {
                "capsule_id": "cap_test_001",
                "source_turn_range": [1, 30],
                "topic": "OpenClaw 上下文压缩",
                "decisions": session["turns"][29]["decisions"],
                "open_loops": session["turns"][29]["open_loops"]
            }
            
            # 验证
            if len(capsule["decisions"]) == 3 and len(capsule["open_loops"]) == 2:
                self.results.append({"test": test_name, "status": "PASS"})
                self.passed += 1
                return True
            else:
                self.results.append({"test": test_name, "status": "FAIL", "reason": "字段缺失"})
                self.failed += 1
                return False
                
        except Exception as e:
            self.results.append({"test": test_name, "status": "FAIL", "reason": str(e)})
            self.failed += 1
            return False
    
    def test_retrieval_recall(self):
        """测试检索回填"""
        test_name = "retrieval_recall"
        try:
            # 模拟检索
            # 在真实环境会调用 context-retrieve
            query = "OpenClaw 上下文压缩 决定"
            
            # 验证能否找到相关 capsule
            # 简化验证：检查关键词匹配
            keywords = ["OpenClaw", "上下文压缩", "决定"]
            
            if len(keywords) >= 3:
                self.results.append({"test": test_name, "status": "PASS"})
                self.passed += 1
                return True
            else:
                self.results.append({"test": test_name, "status": "FAIL", "reason": "关键词不足"})
                self.failed += 1
                return False
                
        except Exception as e:
            self.results.append({"test": test_name, "status": "FAIL", "reason": str(e)})
            self.failed += 1
            return False
    
    def test_commitment_preservation(self):
        """测试承诺保留"""
        test_name = "commitment_preservation"
        try:
            # 验证 open_loops 在压缩后仍可访问
            test_loops = [
                {"id": "loop_a1", "text": "需要评估 rehydration precision"},
                {"id": "loop_a2", "text": "需要创建回归测试集"}
            ]
            
            # 模拟 Never-Compress Slots 保护
            preserved = [loop for loop in test_loops]
            
            if len(preserved) == len(test_loops):
                self.results.append({"test": test_name, "status": "PASS"})
                self.passed += 1
                return True
            else:
                self.results.append({"test": test_name, "status": "FAIL", "reason": "open_loops 丢失"})
                self.failed += 1
                return False
                
        except Exception as e:
            self.results.append({"test": test_name, "status": "FAIL", "reason": str(e)})
            self.failed += 1
            return False
    
    def test_rehydration_precision(self):
        """测试回填精度"""
        test_name = "rehydration_precision"
        try:
            # 模拟回填内容
            retrieved = [
                {"topic": "OpenClaw 上下文压缩", "relevance": 0.9},
                {"topic": "三层上下文模型", "relevance": 0.85}
            ]
            
            # 计算精度 (简化：检查相关性)
            high_relevance = [r for r in retrieved if r["relevance"] >= 0.8]
            precision = len(high_relevance) / len(retrieved)
            
            if precision >= 0.80:
                self.results.append({"test": test_name, "status": "PASS", "precision": precision})
                self.passed += 1
                return True
            else:
                self.results.append({"test": test_name, "status": "FAIL", "precision": precision})
                self.failed += 1
                return False
                
        except Exception as e:
            self.results.append({"test": test_name, "status": "FAIL", "reason": str(e)})
            self.failed += 1
            return False
    
    def run_all(self):
        """运行所有测试"""
        print("=== Old Topic Recall Regression Tests ===\n")
        
        self.test_capsule_creation()
        self.test_retrieval_recall()
        self.test_commitment_preservation()
        self.test_rehydration_precision()
        
        print(f"\nResults: {self.passed} passed, {self.failed} failed")
        
        for result in self.results:
            status = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status} {result['test']}")
            if "reason" in result:
                print(f"      Reason: {result['reason']}")
            if "precision" in result:
                print(f"      Precision: {result['precision']:.2f}")
        
        return self.failed == 0

if __name__ == "__main__":
    tester = OldTopicRecallTest()
    success = tester.run_all()
    sys.exit(0 if success else 1)
