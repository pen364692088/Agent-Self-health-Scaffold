# SEND_TIMEOUT_LANE_CORRELATION

## Conclusion
`sessions_send_timeout` and lane occupation are **part of the same root cause chain**, but the timeout occurred during a different attempt than the lane-holding task.

## Evidence chain

1. **Lane was busy from ~21:33 to 21:56**
   - Multiple `lane wait exceeded` events with `queueAhead=0`
   - An embedded run was holding the lane

2. **Post-adoption manual trigger attempt at 03:33:00Z (21:33:00 CST)**
   - Result: `sessions_send_timeout`
   - This was during the period when the lane was busy

3. **sessions_send path does NOT go through lane enqueue**
   - `sessions_send` is a message sending mechanism, not a lane-enqueued task
   - However, if the **target session** is busy (lane occupied), the send may wait for the session to become responsive

4. **The timeout was likely caused by**:
   - The target session being busy with the embedded run
   - The wait for response exceeding timeout threshold
   - NOT by a lane deadlock in the sending path itself

## Relationship diagram

```
embedded_run holds session lane
         ↓
session is busy, not processing new work
         ↓
sessions_send to that session waits
         ↓
wait exceeds timeout
         ↓
sessions_send_timeout recorded
```

## Are they the same root cause?
- **Yes, indirectly**: The lane occupation by the embedded run made the session unresponsive
- **But the timeout mechanism is separate**: `sessions_send` timeout is not the same as lane release

## Cleanup status after timeout
- The embedded run eventually completed at 21:56:50 with a rate limit error
- Lane was properly released after task completion
- No evidence of missing release or stale lock
