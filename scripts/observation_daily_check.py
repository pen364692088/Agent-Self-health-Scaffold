#!/usr/bin/env python3
"""
Self-Health 观察窗口每日检查脚本

每日运行，收集以下指标：
- recurrence_rate_by_signature
- auto_remediation_success_rate
- false_fix_rate
- rollback_count
- prevention_hit_rate
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import subprocess


class ObservationDailyCheck:
    """观察窗口每日检查"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.memory_dir = workspace / "memory" / "evolution"
        self.logs_dir = workspace / "artifacts" / "observation_window" / "daily_logs"
        self.config_path = workspace / "artifacts" / "observation_window" / "observation_config.json"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """加载观察配置"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {"observation_window": {"id": "obs_v1_20260315"}}
    
    def load_success_records(self) -> List[Dict]:
        """加载成功修复记录"""
        records = []
        success_db = self.memory_dir / "successes.jsonl"
        if success_db.exists():
            with open(success_db) as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        return records
    
    def load_prevention_rules(self) -> List[Dict]:
        """加载预防规则"""
        rules = []
        rules_db = self.memory_dir / "prevention_rules.jsonl"
        if rules_db.exists():
            with open(rules_db) as f:
                for line in f:
                    if line.strip():
                        rules.append(json.loads(line))
        return rules
    
    def check_gate_b(self) -> Dict[str, Any]:
        """运行 Gate B 测试"""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_self_healing_e2e.py", "-v", "--tb=short"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # 解析测试结果
        passed = "passed" in result.stdout
        collected = result.stdout.count("::test_")
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "collected": collected,
            "stdout_preview": result.stdout[:500] if result.stdout else ""
        }
    
    def check_gate_c(self) -> Dict[str, Any]:
        """运行 Gate C 检查"""
        result = subprocess.run(
            ["python", "scripts/tool_doctor.py"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout_preview": result.stdout[:500] if result.stdout else ""
        }
    
    def calculate_metrics(self, records: List[Dict], rules: List[Dict]) -> Dict[str, Any]:
        """计算监控指标"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # 按签名统计
        signature_stats: Dict[str, Dict] = {}
        for record in records:
            sig = record.get("signature", "unknown")
            if sig not in signature_stats:
                signature_stats[sig] = {
                    "total_success": 0,
                    "first_success": None,
                    "last_success": None,
                    "recent_success": 0
                }
            
            stats = signature_stats[sig]
            stats["total_success"] = record.get("success_count", 1)
            stats["first_success"] = record.get("first_success")
            stats["last_success"] = record.get("last_success")
            
            # 最近 24 小时的成功次数
            last_success = record.get("last_success", "")
            if last_success:
                try:
                    last_dt = datetime.fromisoformat(last_success)
                    if last_dt > yesterday:
                        stats["recent_success"] += 1
                except:
                    pass
        
        # 计算复发率 (最近24小时内同一签名重复出现)
        # 复发 = 同一签名在24小时内成功修复多次
        recent_recurring = sum(
            1 for s in signature_stats.values() 
            if s["recent_success"] > 1  # 24小时内多次成功才算复发
        )
        total_recent = sum(1 for s in signature_stats.values() if s["recent_success"] > 0)
        recurrence_rate = (
            recent_recurring / total_recent * 100 
            if total_recent > 0 else 0
        )
        
        # 计算自动修复成功率
        total_records = len(records)
        successful_records = sum(1 for r in records if r.get("success_count", 0) > 0)
        auto_remediation_success_rate = (
            successful_records / total_records * 100 
            if total_records > 0 else 100
        )
        
        # 预防规则命中率
        total_rules = len(rules)
        hit_rules = sum(1 for r in rules if r.get("hit_count", 0) > 0)
        prevention_hit_rate = (
            hit_rules / total_rules * 100 
            if total_rules > 0 else 0
        )
        
        return {
            "recurrence_rate_by_signature": round(recurrence_rate, 2),
            "auto_remediation_success_rate": round(auto_remediation_success_rate, 2),
            "false_fix_rate": 0.0,  # 需要人工标记
            "rollback_count": 0,    # 需要从日志统计
            "prevention_hit_rate": round(prevention_hit_rate, 2),
            "total_signatures": len(signature_stats),
            "recurring_signatures_24h": recent_recurring,
            "total_success_records": total_records,
            "total_prevention_rules": total_rules
        }
    
    def check_red_lines(self, metrics: Dict, day_number: int) -> List[str]:
        """检查四条红线"""
        violations = []
        
        # 红线 1: 复发率 > 30% (第1-3天允许基线建立，放宽到50%)
        recurrence_threshold = 50 if day_number <= 3 else 30
        if metrics["recurrence_rate_by_signature"] > recurrence_threshold:
            violations.append(
                f"复发率过高: {metrics['recurrence_rate_by_signature']}% > {recurrence_threshold}%"
            )
        
        # 红线 2: 自动修复成功率 < 60%
        if metrics["auto_remediation_success_rate"] < 60:
            violations.append(
                f"自动修复成功率过低: {metrics['auto_remediation_success_rate']}% < 60%"
            )
        
        # 红线 3: 误修率 > 10% (目前无法自动检测)
        if metrics["false_fix_rate"] > 10:
            violations.append(
                f"误修率过高: {metrics['false_fix_rate']}% > 10%"
            )
        
        # 红线 4: 回滚次数 > 5/周
        if metrics["rollback_count"] > 5:
            violations.append(
                f"回滚次数过多: {metrics['rollback_count']} > 5/周"
            )
        
        return violations
    
    def run_check(self) -> Dict[str, Any]:
        """运行每日检查"""
        now = datetime.now()
        config = self.load_config()
        
        print(f"=== 观察窗口每日检查 ===")
        print(f"时间: {now.isoformat()}")
        print(f"观察窗口 ID: {config['observation_window']['id']}")
        print()
        
        # 1. 加载数据
        print("[1] 加载记忆数据...")
        records = self.load_success_records()
        rules = self.load_prevention_rules()
        print(f"    成功记录: {len(records)} 条")
        print(f"    预防规则: {len(rules)} 条")
        
        # 2. 计算指标
        print("\n[2] 计算监控指标...")
        metrics = self.calculate_metrics(records, rules)
        for key, value in metrics.items():
            print(f"    {key}: {value}")
        
        # 3. 检查红线
        print("\n[3] 检查红线...")
        # 计算观察窗口天数
        start_time = datetime.fromisoformat(config["observation_window"]["start_time"])
        day_number = (now - start_time).days + 1
        violations = self.check_red_lines(metrics, day_number)
        if violations:
            print("    ⚠️  红线违规:")
            for v in violations:
                print(f"       - {v}")
        else:
            print("    ✅ 无红线违规")
        
        # 4. Gate B 检查
        print("\n[4] Gate B 测试...")
        gate_b = self.check_gate_b()
        print(f"    状态: {'✅ PASS' if gate_b['passed'] else '❌ FAIL'}")
        
        # 5. Gate C 检查
        print("\n[5] Gate C 检查...")
        gate_c = self.check_gate_c()
        print(f"    状态: {'✅ PASS' if gate_c['passed'] else '❌ FAIL'}")
        
        # 6. 生成报告
        report = {
            "timestamp": now.isoformat(),
            "observation_window_id": config["observation_window"]["id"],
            "day_number": (
                now - datetime.fromisoformat(config["observation_window"]["start_time"])
            ).days + 1,
            "metrics": metrics,
            "red_line_violations": violations,
            "gate_b": {
                "passed": gate_b["passed"],
                "exit_code": gate_b["exit_code"]
            },
            "gate_c": {
                "passed": gate_c["passed"],
                "exit_code": gate_c["exit_code"]
            },
            "status": "OK" if not violations and gate_b["passed"] and gate_c["passed"] else "ALERT"
        }
        
        # 保存报告
        report_path = self.logs_dir / f"daily_check_{now.strftime('%Y%m%d')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[6] 报告已保存: {report_path}")
        
        # 打印状态
        print(f"\n=== 检查结果: {report['status']} ===")
        
        return report


def main():
    workspace = Path(__file__).parent.parent
    checker = ObservationDailyCheck(workspace)
    report = checker.run_check()
    
    # 退出码: 0=OK, 1=ALERT
    sys.exit(0 if report["status"] == "OK" else 1)


if __name__ == "__main__":
    main()
