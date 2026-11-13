"""AuditLogger: Zero-PII structured audit trail for jury verification."""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditRecord:
    timestamp: str
    request_id: str
    segment_id: str
    target_lang: str
    tier_used: str
    masked_sha256: str
    token_count: int
    integrity_passed: bool
    verification_reason: str
    fallback_triggered: bool
    latency_ms: float


class AuditLogger:
    """In-memory ring buffer storing strictly anonymized translation telemetry (no PII)."""

    def __init__(self, maxlen: int = 200) -> None:
        self._records: deque[AuditRecord] = deque(maxlen=maxlen)

    def record(
        self,
        *,
        request_id: str,
        segment_id: str,
        target_lang: str,
        tier_used: str,
        masked_text: str,
        token_count: int,
        integrity_passed: bool,
        verification_reason: str,
        fallback_triggered: bool,
        latency_ms: float,
    ) -> AuditRecord:
        digest = hashlib.sha256(masked_text.encode("utf-8")).hexdigest()[:12]
        entry = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            segment_id=segment_id,
            target_lang=target_lang,
            tier_used=tier_used,
            masked_sha256=digest,
            token_count=token_count,
            integrity_passed=integrity_passed,
            verification_reason=verification_reason,
            fallback_triggered=fallback_triggered,
            latency_ms=round(latency_ms, 3),
        )
        self._records.appendleft(entry)
        return entry

    def recent(self, limit: int = 50) -> list[dict]:
        return [asdict(item) for item in list(self._records)[:limit]]

    def clear(self) -> None:
        self._records.clear()
