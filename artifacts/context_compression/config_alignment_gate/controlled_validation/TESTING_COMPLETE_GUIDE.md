# Context Compression - System Testing Complete Guide

## Testing Framework Overview

### Test Categories

The compression system is tested at multiple levels:

1. **Unit Tests** - Test individual functions and components
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows
4. **Performance Tests** - Test performance characteristics
5. **Regression Tests** - Test for regressions

### Unit Test Examples

#### Token Estimation Tests

```python
def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0

def test_estimate_tokens_single_char():
    assert estimate_tokens("a") == 1

def test_estimate_tokens_sentence():
    text = "Hello, world!"
    expected = len(text) // 4
    assert estimate_tokens(text) == expected

def test_estimate_tokens_long_text():
    text = "a" * 1000
    assert estimate_tokens(text) == 250
```

#### Pressure Level Tests

```python
def test_pressure_normal():
    assert get_pressure_level(0.50) == "normal"
    assert get_pressure_level(0.70) == "normal"
    assert get_pressure_level(0.74) == "normal"

def test_pressure_light():
    assert get_pressure_level(0.75) == "light"
    assert get_pressure_level(0.80) == "light"
    assert get_pressure_level(0.84) == "light"

def test_pressure_standard():
    assert get_pressure_level(0.85) == "standard"
    assert get_pressure_level(0.90) == "standard"
    assert get_pressure_level(0.91) == "standard"

def test_pressure_strong():
    assert get_pressure_level(0.92) == "strong"
    assert get_pressure_level(0.95) == "strong"
    assert get_pressure_level(1.00) == "strong"
```

#### Threshold Detection Tests

```python
def test_threshold_none():
    assert get_threshold_hit(0.50) is None
    assert get_threshold_hit(0.74) is None

def test_threshold_light():
    assert get_threshold_hit(0.75) == "light"
    assert get_threshold_hit(0.80) == "light"

def test_threshold_standard():
    assert get_threshold_hit(0.85) == "standard"
    assert get_threshold_hit(0.90) == "standard"

def test_threshold_strong():
    assert get_threshold_hit(0.92) == "strong"
    assert get_threshold_hit(0.95) == "strong"
```

### Integration Test Examples

#### Budget Check Integration

```python
def test_budget_check_integration():
    # Create test session
    test_dir = Path(tempfile.mkdtemp())
    test_file = test_dir / "test.jsonl"
    
    # Write test data
    write_test_session(test_file, turn_count=10)
    
    # Run budget check
    result = run_budget_check(test_file, max_tokens=100000)
    
    # Verify
    assert result.estimated_tokens > 0
    assert result.ratio > 0
    assert result.pressure_level in ["normal", "light", "standard", "strong"]
    
    # Cleanup
    shutil.rmtree(test_dir)
```

#### Compression Integration

```python
def test_compression_integration():
    # Create test files
    test_dir = Path(tempfile.mkdtemp())
    test_state = test_dir / "state.json"
    test_history = test_dir / "history.jsonl"
    
    write_test_state(test_state)
    write_test_history(test_history, turn_count=100)
    
    # Run compression
    result = run_compression(
        session_id="test",
        state_path=test_state,
        history_path=test_history,
        mode="shadow"
    )
    
    # Verify
    if result.compression_triggered:
        assert result.before.ratio > result.after.ratio
        assert len(result.capsules) > 0
    
    # Cleanup
    shutil.rmtree(test_dir)
```

### End-to-End Test Examples

#### Complete Compression Cycle

```python
def test_complete_compression_cycle():
    # Setup
    session_id = "test_session"
    create_session(session_id)
    
    # Add turns to reach trigger
    add_turns(session_id, count=100)
    
    # Verify compression triggers
    budget = get_budget(session_id)
    assert budget.ratio >= 0.85
    
    # Execute compression
    compress(session_id)
    
    # Verify results
    budget = get_budget(session_id)
    assert budget.ratio < 0.75
    
    # Verify safety
    counters = get_counters()
    assert counters.real_reply_corruption_count == 0
    assert counters.active_session_pollution_count == 0
    
    # Cleanup
    delete_session(session_id)
```

### Performance Test Examples

#### Latency Test

```python
def test_compression_latency():
    # Create session
    session_id = "perf_test"
    create_session(session_id, turn_count=200)
    
    # Measure compression time
    start = time.time()
    compress(session_id)
    duration = time.time() - start
    
    # Verify latency
    assert duration < 0.5  # 500ms max
    
    # Cleanup
    delete_session(session_id)
```

#### Throughput Test

```python
def test_compression_throughput():
    # Create multiple sessions
    sessions = [f"session_{i}" for i in range(10)]
    for session_id in sessions:
        create_session(session_id, turn_count=100)
    
    # Measure throughput
    start = time.time()
    for session_id in sessions:
        compress(session_id)
    duration = time.time() - start
    
    # Calculate throughput
    throughput = len(sessions) / duration
    
    # Verify throughput
    assert throughput >= 20  # 20 compressions per second minimum
    
    # Cleanup
    for session_id in sessions:
        delete_session(session_id)
```

### Test Coverage Requirements

| Component | Required Coverage |
|-----------|-------------------|
| Budget Check | >= 95% |
| Compression | >= 90% |
| State Management | >= 95% |
| Evidence Collection | >= 90% |
| Guardrails | >= 95% |

### Test Execution

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run all integration tests
pytest tests/integration/ -v

# Run all end-to-end tests
pytest tests/e2e/ -v

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:20:00-06:00
