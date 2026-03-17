#!/usr/bin/env python3
"""
Enablement Manager CLI

管理 Agent 启用状态：
- rollout: 推进到更高层级
- rollback: 回退到更低层级
- quarantine: 隔离 Agent
- recover: 从隔离恢复
- status: 查看状态

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def cmd_status(args):
    """查看状态"""
    from runtime.enablement_state import EnablementState
    
    state = EnablementState(PROJECT_ROOT)
    
    print("\n" + "=" * 60)
    print("AGENT ENABLEMENT STATUS")
    print("=" * 60)
    
    summary = state.get_tier_summary()
    
    for tier, agents in summary.items():
        if agents:
            print(f"\n{tier.upper()}:")
            for agent_id in agents:
                print(f"  - {agent_id}")
    
    print("\n" + "=" * 60)
    
    return 0


def cmd_rollout(args):
    """推进 Agent 到更高层级"""
    from runtime.enablement_state import EnablementState, EnablementTier
    
    state = EnablementState(PROJECT_ROOT)
    
    target_tier = EnablementTier(args.tier)
    success = state.rollout(args.agent_id, target_tier, args.reason)
    
    if success:
        print(f"✅ {args.agent_id} rolled out to {args.tier}")
        print(f"   Reason: {args.reason}")
        return 0
    else:
        print(f"❌ Failed to rollout {args.agent_id} to {args.tier}")
        print(f"   Check if transition is allowed")
        return 1


def cmd_rollback(args):
    """回退 Agent 到更低层级"""
    from runtime.enablement_state import EnablementState
    
    state = EnablementState(PROJECT_ROOT)
    success = state.rollback(args.agent_id, args.reason)
    
    if success:
        current_tier = state.get_tier(args.agent_id)
        print(f"✅ {args.agent_id} rolled back to {current_tier.value}")
        print(f"   Reason: {args.reason}")
        return 0
    else:
        print(f"❌ Failed to rollback {args.agent_id}")
        print(f"   Agent may already at lowest tier")
        return 1


def cmd_quarantine(args):
    """隔离 Agent"""
    from runtime.enablement_state import EnablementState
    
    state = EnablementState(PROJECT_ROOT)
    success = state.quarantine(args.agent_id, args.reason)
    
    if success:
        print(f"✅ {args.agent_id} QUARANTINED")
        print(f"   Reason: {args.reason}")
        print(f"   Agent is now in manual mode only")
        return 0
    else:
        print(f"❌ Failed to quarantine {args.agent_id}")
        print(f"   Agent must be in default_enabled tier")
        return 1


def cmd_recover(args):
    """从隔离恢复"""
    from runtime.enablement_state import EnablementState
    
    state = EnablementState(PROJECT_ROOT)
    success = state.recover(args.agent_id, args.reason)
    
    if success:
        print(f"✅ {args.agent_id} recovered from quarantine")
        print(f"   Reason: {args.reason}")
        print(f"   Agent is now in manual_enable_only tier")
        return 0
    else:
        print(f"❌ Failed to recover {args.agent_id}")
        print(f"   Agent must be in quarantine tier")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Agent Enablement Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # status
    parser_status = subparsers.add_parser("status", help="Show enablement status")
    
    # rollout
    parser_rollout = subparsers.add_parser("rollout", help="Rollout agent to higher tier")
    parser_rollout.add_argument("--agent-id", required=True, help="Agent ID")
    parser_rollout.add_argument("--tier", required=True, 
                                choices=["pilot_enabled", "default_enabled"],
                                help="Target tier")
    parser_rollout.add_argument("--reason", required=True, help="Reason for rollout")
    
    # rollback
    parser_rollback = subparsers.add_parser("rollback", help="Rollback agent to lower tier")
    parser_rollback.add_argument("--agent-id", required=True, help="Agent ID")
    parser_rollback.add_argument("--reason", required=True, help="Reason for rollback")
    
    # quarantine
    parser_quarantine = subparsers.add_parser("quarantine", help="Quarantine agent")
    parser_quarantine.add_argument("--agent-id", required=True, help="Agent ID")
    parser_quarantine.add_argument("--reason", required=True, help="Reason for quarantine")
    
    # recover
    parser_recover = subparsers.add_parser("recover", help="Recover agent from quarantine")
    parser_recover.add_argument("--agent-id", required=True, help="Agent ID")
    parser_recover.add_argument("--reason", required=True, help="Reason for recovery")
    
    args = parser.parse_args()
    
    if args.command == "status":
        return cmd_status(args)
    elif args.command == "rollout":
        return cmd_rollout(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    elif args.command == "quarantine":
        return cmd_quarantine(args)
    elif args.command == "recover":
        return cmd_recover(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
