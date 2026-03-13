# HISTORY_RISK_VERDICT.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## Verdict: 🔴 REWRITE_REQUIRED

### Reason
A real API key (Cerebras) is exposed in the git history at commit `e2eb633`. This is a credential that must be treated as compromised.

---

## Evidence

### Critical Finding
```
File: cerebras_config.json
Commit: e2eb633 Archive: MVP11.4.5-11.4.8 complete, hard gate shadow mode...
Secret: csk-txv2p9mkpe2dd86y38nr4wew3e66tmynt6hpyny8w2dxvpkd
```

### Secondary Findings
| Finding | Risk | Action |
|---------|------|--------|
| Telegram chat IDs in traces | Medium | Recommended |
| Session IDs in logs | Low | Optional |
| Local machine paths | Info | Not needed |

---

## Required Actions

### 1. IMMEDIATE (Before Any Push)
- [ ] **Rotate Cerebras API Key** at https://cloud.cerebras.ai
- [ ] Verify old key is revoked

### 2. History Rewrite Scope
```
Files to remove from history:
- cerebras_config.json (entire file)

Files to consider removing:
- integrations/openclaw/traces/telegram:*.jsonl (PII)
```

### 3. Rewrite Tool Recommendation
Use `git-filter-repo` (not BFG, as it's deprecated):

```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove cerebras_config.json from all history
git filter-repo --invert-paths --path cerebras_config.json

# Force cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 4. Post-Rewrite Actions
- [ ] Notify all collaborators to re-clone
- [ ] Update branch protection rules
- [ ] Force push with `--force-with-lease` (safer than `--force`)

---

## Impact Assessment

### Before Rewrite
- Anyone with repo access can extract the API key
- Key is valid until rotated
- GitHub search can find the key

### After Rewrite
- Key removed from all commits
- Old clones will have divergent history
- PRs may need to be re-created

---

## Alternative: Accept Risk (NOT RECOMMENDED)

If history rewrite is not feasible:
1. Rotate the API key immediately (invalidates the exposed key)
2. Accept that the key string remains in history (but is now useless)
3. Document the incident in security log
4. Add secret scanning to CI/CD

**This is NOT recommended** because:
- Secret scanners will flag the repo
- Key could be scraped by bots
- Audit/compliance issues

---

## Conclusion

**Status**: REWRITE_REQUIRED

**Next Step**: User must decide:
1. Proceed with history rewrite (recommended)
2. Accept rotated key only (not recommended)

**Awaiting user confirmation before proceeding.**
