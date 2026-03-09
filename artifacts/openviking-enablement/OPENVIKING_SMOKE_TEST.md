# OpenViking Smoke Test

## 测试结果

| 测试项 | 状态 | 详情 |
|-------|------|------|
| Health check | ✅ PASS | {"status":"ok"} |
| Retrieval | ✅ PASS | 3 results, top score 0.662 |
| Add resource | ✅ PASS | Created viking://resources/user/test/openviking_test |
| Verify resource | ✅ PASS | Found 4 resources in test namespace |

## 样本输入输出

### 输入
```
Query: "test"
URI: viking://resources/user/test/
```

### 输出
```json
{
  "ok": true,
  "result": {
    "total": 4,
    "resources": [
      {"uri": "viking://resources/user/test/openviking_test/openviking_test.md", "score": 0.588},
      {"uri": "viking://resources/user/test/test_doc/test_doc.md", "score": 0.563}
    ]
  }
}
```

## 功能验证结论

- ✅ OpenViking 服务正常响应
- ✅ 向量检索工作正常
- ✅ 资源添加工作正常
- ✅ 新添加资源可被检索到

