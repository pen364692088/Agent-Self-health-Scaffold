#!/usr/bin/env python3
"""Lightweight alerting with dedupe/cooldown/escalation and failed queue."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any
import urllib.request


LEVEL_ORDER = {"INFO": 0, "WARN_SOFT": 1, "WARN": 2, "ERROR": 3}


def level_rank(level: str) -> int:
    return LEVEL_ORDER.get(level.upper(), 0)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_to_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


@dataclass
class Alert:
    level: str
    rule_id: str
    root_uri: str
    reason_signature: str
    message: str
    top_offender_doc_id: str | None = None
    details: dict[str, Any] | None = None

    def fingerprint(self) -> str:
        seed = "|".join([
            self.level,
            self.rule_id,
            self.root_uri,
            self.top_offender_doc_id or "",
            self.reason_signature,
        ])
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]

    def group_key(self) -> str:
        # for escalation/reason-change detection
        seed = "|".join([self.rule_id, self.root_uri, self.top_offender_doc_id or ""])
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


class AlertManager:
    def __init__(
        self,
        *,
        state_path: str | Path,
        failed_dir: str | Path,
        cooldown_warn_sec: int = 3600,
        cooldown_error_sec: int = 600,
        webhook_url: str | None = None,
    ):
        self.state_path = Path(state_path)
        self.failed_dir = Path(failed_dir)
        self.cooldown_warn_sec = cooldown_warn_sec
        self.cooldown_error_sec = cooldown_error_sec
        self.webhook_url = webhook_url
        self.state = {"version": "alert_state.v1", "sent": {}, "groups": {}}
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            try:
                self.state = json.loads(self.state_path.read_text())
            except Exception:
                self.state = {"version": "alert_state.v1", "sent": {}, "groups": {}}

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n")

    def _cooldown_sec(self, level: str) -> int:
        return self.cooldown_error_sec if level.upper() == "ERROR" else self.cooldown_warn_sec

    def should_send(self, alert: Alert) -> tuple[bool, str]:
        fp = alert.fingerprint()
        gk = alert.group_key()
        now = datetime.now(timezone.utc)

        sent_rec = self.state.get("sent", {}).get(fp)
        if sent_rec:
            last = iso_to_dt(sent_rec.get("last_sent_at"))
            if last:
                cooldown = timedelta(seconds=self._cooldown_sec(alert.level))
                if (now - last) < cooldown:
                    return False, "cooldown_active"

        # escalation/reason-change logic by group key
        grp = self.state.get("groups", {}).get(gk)
        if grp:
            prev_level = grp.get("last_level", "INFO")
            prev_reason = grp.get("last_reason_signature")
            if level_rank(alert.level) > level_rank(prev_level):
                return True, "escalation"
            if prev_reason != alert.reason_signature:
                return True, "reason_changed"

        return True, "normal"

    def _send_webhook(self, payload: dict) -> tuple[bool, str]:
        if not self.webhook_url:
            return False, "webhook_not_configured"

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = getattr(resp, "status", 200)
                if 200 <= code < 300:
                    return True, f"http_{code}"
                return False, f"http_{code}"
        except Exception as e:
            return False, str(e)

    def _enqueue_failed(self, alert: Alert, error: str, retry_after_sec: int = 120):
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": now_iso(),
            "next_retry_at": (datetime.now(timezone.utc) + timedelta(seconds=retry_after_sec)).isoformat(),
            "error": error,
            "alert": asdict(alert),
        }
        file = self.failed_dir / f"{alert.fingerprint()}-{int(datetime.now().timestamp())}.json"
        file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def _mark_sent(self, alert: Alert, reason: str):
        fp = alert.fingerprint()
        gk = alert.group_key()
        sent = self.state.setdefault("sent", {})
        groups = self.state.setdefault("groups", {})

        sent[fp] = {
            "last_sent_at": now_iso(),
            "level": alert.level,
            "rule_id": alert.rule_id,
            "reason_signature": alert.reason_signature,
            "message": alert.message,
            "decision_reason": reason,
        }

        groups[gk] = {
            "last_sent_at": now_iso(),
            "last_level": alert.level,
            "last_reason_signature": alert.reason_signature,
            "last_fingerprint": fp,
        }
        self._save_state()

    def send(self, alert: Alert) -> dict:
        ok_to_send, reason = self.should_send(alert)
        if not ok_to_send:
            return {"sent": False, "reason": reason, "fingerprint": alert.fingerprint()}

        payload = {
            "type": "openviking_alert",
            "at": now_iso(),
            "alert": asdict(alert),
            "fingerprint": alert.fingerprint(),
        }

        sent_ok, send_reason = self._send_webhook(payload)
        if sent_ok:
            self._mark_sent(alert, reason)
            return {"sent": True, "reason": reason, "transport": send_reason, "fingerprint": alert.fingerprint()}

        # downgrade to failed queue
        self._enqueue_failed(alert, send_reason)
        self._mark_sent(alert, reason)  # avoid spam storm; retry queue handles later delivery
        return {
            "sent": False,
            "reason": "queued_failed_delivery",
            "transport": send_reason,
            "fingerprint": alert.fingerprint(),
        }

    def retry_failed(self, max_items: int = 20) -> dict:
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(self.failed_dir.glob("*.json"))[:max_items]

        retried = 0
        delivered = 0
        kept = 0

        now = datetime.now(timezone.utc)
        for f in files:
            try:
                data = json.loads(f.read_text())
                due = iso_to_dt(data.get("next_retry_at"))
                if due and due > now:
                    kept += 1
                    continue

                retried += 1
                a = data.get("alert", {})
                alert = Alert(**a)
                payload = {
                    "type": "openviking_alert",
                    "at": now_iso(),
                    "alert": asdict(alert),
                    "fingerprint": alert.fingerprint(),
                    "retry": True,
                }
                ok, reason = self._send_webhook(payload)
                if ok:
                    delivered += 1
                    f.unlink(missing_ok=True)
                else:
                    # backoff
                    data["error"] = reason
                    data["next_retry_at"] = (now + timedelta(minutes=5)).isoformat()
                    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            except Exception:
                kept += 1

        return {"retried": retried, "delivered": delivered, "kept": kept}
