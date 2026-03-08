#!/usr/bin/env python3
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
STATE_DIR = WORKSPACE / 'state'
LOGS_DIR = WORKSPACE / 'logs'
DEFAULT_REGISTRY_PATH = STATE_DIR / 'session_binding_registry.json'
DEFAULT_DECISION_LOG_PATH = LOGS_DIR / 'session_decision_log.jsonl'

REASON_ENUMS = {
    'reused_active_session',
    'no_active_binding',
    'idle_timeout',
    'thread_changed',
    'explicit_new_session',
    'context_limit',
    'session_closed',
    'agent_restart',
    'binding_invalid',
    'session_missing',
    'account_changed',
    'recovery_only_mode',
}

TTL_PROFILES = {
    'engineering': 24 * 3600,
    'project': 24 * 3600,
    'chat': 4 * 3600,
}


@dataclass
class BindingRecord:
    chat_id: str
    thread_id: str
    account_id: str
    last_active_session_id: str
    last_active_at: str
    session_status: str
    last_reason: str
    continuity_enabled: bool
    context_state: str
    session_file: Optional[str] = None


@dataclass
class DecisionResult:
    selected_session_id: str
    reused: bool
    reason: str
    previous_session_id: Optional[str]
    recovery_needed: bool
    ttl_seconds: int
    session_status: Optional[str]
    context_state: Optional[str]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_thread_id(thread_id: Optional[str]) -> str:
    if thread_id in (None, '', 'null'):
        return '__default__'
    return str(thread_id)


def binding_key(chat_id: str, thread_id: Optional[str], account_id: str) -> str:
    return f'{chat_id}::{normalize_thread_id(thread_id)}::{account_id}'


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    normalized = ts.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {'version': '1.0', 'bindings': {}}
    data = json.loads(path.read_text())
    data.setdefault('version', '1.0')
    data.setdefault('bindings', {})
    return data


def save_registry(data: Dict[str, Any], path: Path = DEFAULT_REGISTRY_PATH) -> None:
    ensure_parent(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def append_decision_log(entry: Dict[str, Any], path: Path = DEFAULT_DECISION_LOG_PATH) -> None:
    ensure_parent(path)
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + '\n')


def get_binding(chat_id: str, thread_id: Optional[str], account_id: str,
                registry: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    registry = registry or load_registry()
    return registry['bindings'].get(binding_key(chat_id, thread_id, account_id))


def session_reference_valid(binding: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    session_file = binding.get('session_file')
    if session_file:
        path = Path(session_file)
        if not path.exists():
            return False, 'session_missing'
        if path.is_dir():
            return False, 'binding_invalid'
    return True, None


def decide_session_for_inbound(
    *,
    chat_id: str,
    thread_id: Optional[str],
    account_id: str,
    ttl_seconds: int,
    registry: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
    explicit_new_session: bool = False,
    agent_restarted: bool = False,
    source_tool: str = 'session-route',
    new_session_id: Optional[str] = None,
) -> Dict[str, Any]:
    registry = registry or load_registry()
    now = now or datetime.now(timezone.utc)
    key = binding_key(chat_id, thread_id, account_id)
    binding = registry['bindings'].get(key)

    previous_session_id = None
    reused = False
    reason = 'no_active_binding'
    session_status = None
    context_state = None

    if explicit_new_session:
        reason = 'explicit_new_session'
    elif agent_restarted:
        reason = 'agent_restart'
    elif binding is None:
        normalized_thread = normalize_thread_id(thread_id)
        for other_key, other in registry['bindings'].items():
            if other.get('chat_id') != chat_id:
                continue
            if other.get('account_id') == account_id and other.get('thread_id') != normalized_thread:
                reason = 'thread_changed'
                break
            if other.get('thread_id') == normalized_thread and other.get('account_id') != account_id:
                reason = 'account_changed'
                break
    elif binding is not None:
        previous_session_id = binding.get('last_active_session_id')
        session_status = binding.get('session_status')
        context_state = binding.get('context_state')

        valid_ref, invalid_reason = session_reference_valid(binding)
        if not valid_ref:
            reason = invalid_reason or 'binding_invalid'
        elif session_status == 'closed':
            reason = 'session_closed'
        elif context_state == 'hard_blocked':
            reason = 'context_limit'
        else:
            last_active_at = parse_iso(binding.get('last_active_at'))
            if last_active_at is None:
                reason = 'binding_invalid'
            else:
                age = (now - last_active_at).total_seconds()
                if age > ttl_seconds:
                    reason = 'idle_timeout'
                else:
                    reused = True
                    reason = 'reused_active_session'

    selected_session_id = previous_session_id if reused and previous_session_id else (new_session_id or f'session_{uuid.uuid4().hex[:12]}')
    recovery_needed = not reused

    result = DecisionResult(
        selected_session_id=selected_session_id,
        reused=reused,
        reason=reason,
        previous_session_id=previous_session_id,
        recovery_needed=recovery_needed,
        ttl_seconds=ttl_seconds,
        session_status=session_status,
        context_state=context_state,
    )

    log_entry = {
        'ts': now.isoformat(),
        'chat_id': chat_id,
        'thread_id': normalize_thread_id(thread_id),
        'account_id': account_id,
        'previous_session_id': previous_session_id,
        'selected_session_id': selected_session_id,
        'reused': reused,
        'reason': reason,
        'ttl_seconds': ttl_seconds,
        'session_status': session_status,
        'context_state': context_state,
        'recovery_needed': recovery_needed,
        'source_tool': source_tool,
    }

    return {
        'binding_key': key,
        'decision': asdict(result),
        'decision_log_entry': log_entry,
    }


def update_binding_after_decision(
    *,
    chat_id: str,
    thread_id: Optional[str],
    account_id: str,
    decision: Dict[str, Any],
    session_status: str = 'active',
    continuity_enabled: bool = True,
    context_state: str = 'normal',
    registry: Optional[Dict[str, Any]] = None,
    session_file: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    registry = registry or load_registry()
    now = now or datetime.now(timezone.utc)
    key = binding_key(chat_id, thread_id, account_id)
    previous = registry['bindings'].get(key)

    if previous and previous.get('last_active_session_id') != decision['selected_session_id']:
        previous['session_status'] = 'paused'

    updated = BindingRecord(
        chat_id=chat_id,
        thread_id=normalize_thread_id(thread_id),
        account_id=account_id,
        last_active_session_id=decision['selected_session_id'],
        last_active_at=now.isoformat(),
        session_status=session_status,
        last_reason=decision['reason'],
        continuity_enabled=continuity_enabled,
        context_state=context_state,
        session_file=session_file or (previous or {}).get('session_file'),
    )
    registry['bindings'][key] = asdict(updated)
    return registry


def reason_is_valid(reason: str) -> bool:
    return reason in REASON_ENUMS


def metrics_from_decision_log(path: Path = DEFAULT_DECISION_LOG_PATH) -> Dict[str, Any]:
    counters: Dict[str, int] = {
        'inbound_reuse_attempt_count': 0,
        'inbound_reuse_success_count': 0,
        'inbound_new_session_count': 0,
        'reuse_ttl_expired_count': 0,
        'binding_invalid_count': 0,
        'recovery_after_new_session_count': 0,
    }
    reason_counts: Dict[str, int] = {}
    if not path.exists():
        return {**counters, 'new_session_reason_count': reason_counts}

    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        counters['inbound_reuse_attempt_count'] += 1
        if row.get('reused'):
            counters['inbound_reuse_success_count'] += 1
        else:
            counters['inbound_new_session_count'] += 1
            if row.get('recovery_needed'):
                counters['recovery_after_new_session_count'] += 1
        reason = row.get('reason', 'unknown')
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if reason == 'idle_timeout':
            counters['reuse_ttl_expired_count'] += 1
        if reason in {'binding_invalid', 'session_missing'}:
            counters['binding_invalid_count'] += 1

    return {**counters, 'new_session_reason_count': reason_counts}
