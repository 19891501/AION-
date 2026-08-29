"""Ledger append-only : World Model temporel + mecanisation des 4 lois ARCHE."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

STATUTS = ("HYPOTHESIS", "SUPPORTED", "VERIFIED", "CONFLICTED", "UNKNOWN", "OBSOLETE", "REJECTED")
STATUTS_DE_PREUVE = ("SUPPORTED", "VERIFIED")


class ArcheViolation(Exception):
    """Levee quand une operation viole une des 4 lois ARCHE."""


@dataclass(frozen=True)
class Entry:
    seq: int
    fact: str
    status: str
    time: str
    source: str
    context: str
    justification: str
    predecessor: int | None
    prev_hash: str
    hash: str = ""

    def payload(self) -> str:
        d = asdict(self)
        d.pop("hash")
        return json.dumps(d, sort_keys=True, ensure_ascii=False)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, entries: Iterable[Entry] = ()) -> None:
        self._entries: list[Entry] = list(entries)

    @property
    def entries(self) -> tuple[Entry, ...]:
        return tuple(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def head(self, fact: str) -> Entry | None:
        for e in reversed(self._entries):
            if e.fact == fact:
                return e
        return None

    def history(self, fact: str) -> list[Entry]:
        return [e for e in self._entries if e.fact == fact]

    def status_of(self, fact: str) -> str:
        e = self.head(fact)
        return e.status if e else "UNKNOWN"

    def append(
        self,
        fact: str,
        status: str,
        *,
        justification: str,
        source: str = "",
        context: str = "",
        time: str | None = None,
    ) -> Entry:
        if status not in STATUTS:
            raise ArcheViolation(f"statut inconnu: {status}")
        if not justification.strip():
            raise ArcheViolation("A3: transition sans justification")

        previous = self.head(fact)
        if status in STATUTS_DE_PREUVE and not source.strip():
            raise ArcheViolation(f"A4: passage a {status} sans source")

        prev_hash = self._entries[-1].hash if self._entries else "0" * 64
        draft = Entry(
            seq=len(self.entries),
            fact=fact,
            status=status,
            time=time or _now(),
            source=source,
            context=context,
            justification=justification,
            predecessor=previous.seq if previous else None,
            prev_hash=prev_hash,
        )
        digest = hashlib.sha256(draft.payload().encode()).hexdigest()
        entry = Entry(**{**asdict(draft), "hash": digest})
        self._entries.append(entry)
        return entry

    def revise(self, fact: str, status: str, *, justification: str, source: str = "") -> Entry:
        if self.head(fact) is None:
            raise ArcheViolation("A2: revision d'un fait sans predecesseur")
        return self.append(fact, status, justification=justification, source=source)

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for e in self._entries:
            if e.prev_hash != prev:
                return False
            if hashlib.sha256(e.payload().encode()).hexdigest() != e.hash:
                return False
            prev = e.hash
        return True

    def to_json(self) -> str:
        return json.dumps([asdict(e) for e in self._entries], ensure_ascii=False, indent=2)

    @classmethod
    def from_entries(cls, entries: Iterable[Entry]) -> Ledger:
        return cls(entries)
