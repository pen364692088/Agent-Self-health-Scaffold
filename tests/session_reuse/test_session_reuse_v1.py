#!/usr/bin/env python3
import os
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', Path(__file__).parent.parent))
LIB_PATH = WORKSPACE / 'tools' / 'session_reuse_lib.py'

import sys
spec = importlib.util.spec_from_file_location('session_reuse_lib', LIB_PATH)
lib = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lib
spec.loader.exec_module(lib)


class TestSessionReuseV1:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry_path = self.temp_dir / 'session_binding_registry.json'
        self.log_path = self.temp_dir / 'session_decision_log.jsonl'

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _fresh_registry(self):
        return {'version': '1.0', 'bindings': {}}

    def _binding(self, **overrides):
        now = datetime.now(timezone.utc)
        base = {
            'chat_id': 'telegram:8420019401',
            'thread_id': '__default__',
            'account_id': 'manager',
            'last_active_session_id': 'sess_001',
            'last_active_at': now.isoformat(),
            'session_status': 'active',
            'last_reason': 'reused_active_session',
            'continuity_enabled': True,
            'context_state': 'normal',
            'session_file': None,
        }
        base.update(overrides)
        return base

    def test_1_same_thread_same_account_within_ttl_reuses(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        registry['bindings'][key] = self._binding()
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry,
        )['decision']
        assert out['reused'] is True
        assert out['reason'] == 'reused_active_session'
        assert out['selected_session_id'] == 'sess_001'

    def test_2_ttl_timeout_creates_new_session(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        old = datetime.now(timezone.utc) - timedelta(hours=30)
        registry['bindings'][key] = self._binding(last_active_at=old.isoformat())
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_002'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'idle_timeout'
        assert out['selected_session_id'] == 'sess_002'
        assert out['recovery_needed'] is True

    def test_3_thread_changed_does_not_reuse_previous_binding(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', 'thread-a', 'manager')
        registry['bindings'][key] = self._binding(thread_id='thread-a')
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id='thread-b', account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_003'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'thread_changed'
        assert out['selected_session_id'] == 'sess_003'

    def test_4_context_hard_blocked_forces_new_session(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        registry['bindings'][key] = self._binding(context_state='hard_blocked')
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_004'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'context_limit'

    def test_5_session_closed_forces_new_session(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        registry['bindings'][key] = self._binding(session_status='closed')
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_005'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'session_closed'

    def test_6_missing_session_file_marks_session_missing(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        registry['bindings'][key] = self._binding(session_file=str(self.temp_dir / 'missing.jsonl'))
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_006'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'session_missing'

    def test_7_new_session_updates_binding_and_requires_recovery(self):
        registry = self._fresh_registry()
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_007'
        )['decision']
        assert out['recovery_needed'] is True
        updated = lib.update_binding_after_decision(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            decision=out, registry=registry, context_state='normal'
        )
        binding = updated['bindings'][lib.binding_key('telegram:8420019401', None, 'manager')]
        assert binding['last_active_session_id'] == 'sess_007'
        assert binding['last_reason'] == 'no_active_binding'
        assert binding['session_status'] == 'active'

    def test_8_decision_log_integrity_and_metrics(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'manager')
        registry['bindings'][key] = self._binding()
        reuse = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry,
        )
        lib.append_decision_log(reuse['decision_log_entry'], self.log_path)

        expired = self._binding(last_active_at=(datetime.now(timezone.utc) - timedelta(hours=30)).isoformat())
        registry['bindings'][key] = expired
        new_one = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_008'
        )
        lib.append_decision_log(new_one['decision_log_entry'], self.log_path)

        rows = [json.loads(line) for line in self.log_path.read_text().splitlines()]
        assert len(rows) == 2
        assert all(lib.reason_is_valid(row['reason']) for row in rows)
        assert rows[0]['selected_session_id'] == 'sess_001'
        assert rows[1]['selected_session_id'] == 'sess_008'

        metrics = lib.metrics_from_decision_log(self.log_path)
        assert metrics['inbound_reuse_attempt_count'] == 2
        assert metrics['inbound_reuse_success_count'] == 1
        assert metrics['inbound_new_session_count'] == 1
        assert metrics['reuse_ttl_expired_count'] == 1


    def test_9_account_changed_detected(self):
        registry = self._fresh_registry()
        key = lib.binding_key('telegram:8420019401', None, 'other-account')
        registry['bindings'][key] = self._binding(account_id='other-account')
        out = lib.decide_session_for_inbound(
            chat_id='telegram:8420019401', thread_id=None, account_id='manager',
            ttl_seconds=24 * 3600, registry=registry, new_session_id='sess_009'
        )['decision']
        assert out['reused'] is False
        assert out['reason'] == 'account_changed'
