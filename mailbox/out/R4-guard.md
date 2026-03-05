R4-guard 已受理：设置自动分流规则如下。

- 若 Round3 结果为 FAIL：自动进入 Round4，并按同一流程执行（coder → verifier → audit）。
- 若 Round3 结果为 PASS：生成最终收口报告并结束流程。

执行要求：
1. 分流判断以 R3 verifier 的 Overall PASS/FAIL 与 R3 audit 结论为准。
2. Round4 若触发，继续沿用当前验收规则（可自修复 FAIL 必须清零；需用户动作项标记 BLOCKED 并附步骤）。
3. 所有结果需可追溯到对应报告文件与命令证据。