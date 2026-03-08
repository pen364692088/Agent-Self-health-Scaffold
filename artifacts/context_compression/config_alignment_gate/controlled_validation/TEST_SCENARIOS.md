# Context Compression Testing Scenarios

## Comprehensive Test Scenario Documentation

### Test Scenario 1: Normal Compression Flow

**Objective**: Verify compression triggers correctly at 0.85 threshold

**Preconditions**:
- Context window: 200000 tokens
- Threshold enforced: 0.85
- Mode: light_enforced
- Kill switch: inactive

**Steps**:
1. Start with empty session (0 tokens)
2. Add turns until ratio reaches 0.80
3. Verify state transitions to candidate
4. Add turns until ratio reaches 0.85
5. Verify state transitions to pending
6. Trigger compression
7. Verify state transitions to executing
8. Wait for completion
9. Verify state transitions to completed
10. Verify post-compression ratio < 0.75

**Expected Results**:
- Compression triggers at exactly 0.85
- Pre-assemble timing is correct
- Safety counters remain at 0
- Evidence package is complete

### Test Scenario 2: Threshold Boundary

**Objective**: Verify compression does not trigger below 0.85

**Preconditions**:
- Same as Scenario 1

**Steps**:
1. Add turns until ratio is exactly 0.8499
2. Verify no compression triggered
3. Add one more turn to reach 0.85
4. Verify compression is now triggered

**Expected Results**:
- No compression below 0.85
- Compression at exactly 0.85
- Threshold precision is 4 decimal places

### Test Scenario 3: Strong Compression

**Objective**: Verify strong compression at 0.92

**Preconditions**:
- Same as Scenario 1

**Steps**:
1. Add turns until ratio reaches 0.92
2. Verify strong compression triggers
3. Verify higher eviction ratio
4. Verify post-compression ratio < 0.60

**Expected Results**:
- Strong compression at 0.92
- More aggressive eviction
- Lower post-compression ratio

### Test Scenario 4: Kill Switch Activation

**Objective**: Verify kill switch stops all compression

**Preconditions**:
- Same as Scenario 1

**Steps**:
1. Activate kill switch
2. Add turns until ratio exceeds 0.85
3. Verify no compression occurs
4. Deactivate kill switch
5. Verify compression resumes

**Expected Results**:
- No compression when kill switch active
- Context preserved without modification
- Compression resumes after deactivation

### Test Scenario 5: Compression Failure

**Objective**: Verify graceful handling of compression failure

**Preconditions**:
- Same as Scenario 1
- Force capsule generation to fail

**Steps**:
1. Add turns until ratio reaches 0.85
2. Force capsule generation failure
3. Verify state transitions to failed
4. Verify rollback occurs
5. Verify safety counters updated

**Expected Results**:
- Compression failure detected
- Automatic rollback triggered
- State restored to previous
- Rollback event logged

### Test Scenario 6: Concurrent Sessions

**Objective**: Verify multiple sessions can be compressed independently

**Preconditions**:
- Multiple active sessions

**Steps**:
1. Create 5 sessions with different ratios
2. Trigger compression on highest ratio session
3. Verify only that session is compressed
4. Verify other sessions unaffected

**Expected Results**:
- Independent compression per session
- No cross-session interference
- All evidence properly separated

### Test Scenario 7: Evidence Preservation

**Objective**: Verify complete evidence package is created

**Preconditions**:
- Same as Scenario 1

**Steps**:
1. Add turns until ratio reaches 0.85
2. Trigger compression
3. Verify all evidence files created
4. Verify evidence integrity

**Expected Results**:
- counter_before.json exists
- counter_after.json exists
- budget_before.json exists
- budget_after.json exists
- guardrail_event.json exists
- capsule_metadata.json exists
- All timestamps consistent

### Test Scenario 8: State Preservation

**Objective**: Verify critical state is preserved across compression

**Preconditions**:
- Same as Scenario 1
- Session has task_goal, open_loops, hard_constraints

**Steps**:
1. Set task_goal, open_loops, hard_constraints
2. Add turns until ratio reaches 0.85
3. Trigger compression
4. Verify protected fields unchanged

**Expected Results**:
- task_goal preserved
- open_loops preserved
- hard_constraints preserved
- response_contract preserved

### Test Scenario 9: Capsule Retrieval

**Objective**: Verify capsules can be retrieved after compression

**Preconditions**:
- Same as Scenario 1
- Compression completed

**Steps**:
1. Complete compression with capsules
2. Query for content from evicted turns
3. Verify capsules returned
4. Verify relevance scoring

**Expected Results**:
- Capsules retrieved correctly
- Relevance scores accurate
- Content matches original

### Test Scenario 10: Long Session Compression

**Objective**: Verify compression works with very long sessions

**Preconditions**:
- Session with 500+ turns

**Steps**:
1. Create session with 500 turns
2. Add more turns until ratio reaches 0.85
3. Trigger compression
4. Verify large eviction (up to 60%)
5. Verify multiple capsules created

**Expected Results**:
- Large eviction handled correctly
- Multiple capsules created
- Duration within limits (< 1 second)

### Test Scenario 11: Rapid Context Growth

**Objective**: Verify compression handles rapid context growth

**Preconditions**:
- Same as Scenario 1

**Steps**:
1. Add turns rapidly to exceed 0.92
2. Verify strong compression triggers
3. Verify immediate response

**Expected Results**:
- Strong compression triggered immediately
- Context reduced quickly
- No context overflow

### Test Scenario 12: Empty Session

**Objective**: Verify no compression on empty session

**Preconditions**:
- Empty session (0 turns)

**Steps**:
1. Run budget check on empty session
2. Verify ratio is 0
3. Verify no compression triggered

**Expected Results**:
- Ratio = 0
- No compression triggered
- No errors

### Test Scenario 13: Single Turn Session

**Objective**: Verify minimum preservation rules

**Preconditions**:
- Session with 1 turn

**Steps**:
1. Create session with 1 turn
2. Force ratio to 0.85 artificially
3. Verify no turns evicted (minimum 5)

**Expected Results**:
- No eviction
- Minimum preservation respected
- State unchanged

### Test Scenario 14: Configuration Validation

**Objective**: Verify invalid configuration is rejected

**Preconditions**:
- Invalid threshold configuration

**Steps**:
1. Set threshold > 1.0
2. Verify validation fails
3. Set threshold < 0
4. Verify validation fails

**Expected Results**:
- Invalid config rejected
- Warning logged
- Default used

### Test Scenario 15: Counter Overflow

**Objective**: Verify counter overflow handling

**Preconditions**:
- Counter near max value

**Steps**:
1. Set counter near max integer
2. Run compression
3. Verify counter doesn't overflow
4. Verify correct handling

**Expected Results**:
- No overflow
- Counter handled correctly
- No data loss

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:15:00-06:00
**Purpose**: Complete Test Scenario Documentation
