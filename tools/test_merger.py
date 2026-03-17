#!/usr/bin/env python3
"""Test instruction rules merger"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.instruction_rules_merger import InstructionRulesMerger

def main():
    print("Testing Instruction Rules Merger\n")
    
    merger = InstructionRulesMerger(PROJECT_ROOT)
    
    for agent_id in ["implementer", "planner", "verifier"]:
        print(f"{'='*50}")
        print(f"Agent: {agent_id}")
        print(f"{'='*50}")
        
        result = merger.merge(agent_id)
        
        print(f"Hard Constraints: {result.merge_summary['hard_constraints']}")
        print(f"Workflow Rules: {result.merge_summary['workflow_rules']}")
        print(f"Memory Rules: {result.merge_summary['memory_rules']}")
        
        if result.errors:
            print(f"Errors: {result.errors}")
        else:
            print("✅ Merge successful")
        
        print()

if __name__ == "__main__":
    main()
