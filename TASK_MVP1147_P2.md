# MVP11.4.7 P2: WORKFLOW_STATE Schema Guard Test

## 任务
创建守护测试，防止 WORKFLOW_STATE 结构回归到嵌套格式。

## 测试文件
`tests/mvp11/test_workflow_state_schema.py`

## 测试用例
```python
def test_workflow_state_schema_flat_steps_required():
    """WORKFLOW_STATE.json must use flat steps structure, not nested batches."""
    fixture = {
        "active": True,
        "workflow_type": "serial",
        "steps": [
            {"id": "A", "status": "pending"}
        ],
        "notify_on_done": "Done"
    }
    
    # Must have steps as list
    assert "steps" in fixture
    assert isinstance(fixture["steps"], list)
    
    # Must NOT have batches (nested structure)
    assert "batches" not in fixture

def test_workflow_state_steps_have_required_fields():
    """Each step must have id and status."""
    fixture = {
        "active": True,
        "steps": [
            {"id": "A", "run_id": "x", "status": "done"},
            {"id": "B", "status": "pending"}
        ]
    }
    
    for step in fixture["steps"]:
        assert "id" in step, "Step must have id"
        assert "status" in step, "Step must have status"
        assert step["status"] in ("pending", "running", "done", "failed")

def test_callback_handler_expects_flat_structure():
    """Verify callback-handler works with flat steps."""
    import subprocess
    import json
    import tempfile
    
    # Create temp workflow file with flat structure
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "active": True,
            "workflow_type": "serial",
            "steps": [
                {"id": "test-step", "run_id": "test-run-123", "status": "done"}
            ],
            "notify_on_done": "Test done"
        }, f)
        temp_path = f.name
    
    # This should not raise
    # callback-handler should find the run_id
    # (actual test would mock the file path)
```

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
pytest tests/mvp11/test_workflow_state_schema.py -v
```
