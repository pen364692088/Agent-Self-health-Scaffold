# HANDOFF_FOR_NEXT_SESSION.md

## Current state
P0 scaffold created for v2 constrained self-healing execution kernel.

## Completed
- target architecture documented
- task spec documented
- recovery policy documented
- repair action catalog stubbed
- failure taxonomy stubbed
- out-of-band restart design documented
- transcript rebuilder design documented
- e2e matrix defined
- runtime/core/pipeline directories created
- schemas added for task/run/repair/ledger

## Next implementation slice
1. implement append-only ledger writer
2. implement run-state materializer
3. implement recovery scan loop
4. define out-of-band restart intent/executor interface
5. add schema validation tests

## Risks
- transcript truth may still be conflated with task truth in current OpenClaw integration
- restart boundary needs real integration point, not just design docs
