"""
Vision Radar - Event Engine
Shared data models: event schema (Section 11), lifecycle (Section 12).

This is the layer that turns Phase 6's raw Change stream into the
product's primary information unit: an Event. Rich evidence attachment
(frame snapshots, geometry rendering) and the rule/alert layer that acts
on events are Phase 8, per the 10-phase plan - this phase's `evidence`
field is a lightweight context dict, not yet a frame reference.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class EventState(str, Enum):
    """Exactly the lifecycle from Section 12."""
    POTENTIAL = "POTENTIAL"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"


class EventType(str, Enum):
    """
    One-to-one with Phase 6's ChangeType for instantaneous changes.
    ZONE_ENTRY is the exception: it is the *merged* span from a
    ZONE_ENTERED change to its matching ZONE_EXITED change (Section 13's
    own dedup example - one event, not one per frame), named to match
    Section 11's own worked example ("Type: Zone Entry") exactly.
    """
    APPEARED = "APPEARED"
    DISAPPEARED = "DISAPPEARED"
    MOVED = "MOVED"
    STATE_CHANGED = "STATE_CHANGED"
    DWELL = "DWELL"
    ZONE_ENTRY = "ZONE_ENTRY"


@dataclass
class EventConfig:
    # How long a RESOLVED event stays queryable before auto-archiving.
    # A placeholder default - real retention policy is a deployment
    # decision, not something this spec mandates a specific number for.
    archive_after_seconds: float = 60.0
    default_confidence: float = 0.5   # used only if no entity confidence is available


@dataclass
class Event:
    """Matches Section 11's schema field-for-field, plus `entity_type`
    (added in Phase 8) so rules can match spec examples like "Person
    enters Zone A" without a separate lookup - Phase 7's schema carried
    entity_ids but not the type, which rule matching genuinely needs."""
    event_id: str
    event_type: EventType
    entity_ids: List[str]
    entity_type: str
    zone_id: Optional[str]
    start_time: float
    end_time: Optional[float]
    confidence: float
    state: EventState
    evidence: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def duration_seconds(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @classmethod
    def new(cls, event_type: EventType, entity_ids: List[str], entity_type: str,
            start_time: float, confidence: float, zone_id: Optional[str] = None,
            evidence: dict = None) -> "Event":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            entity_ids=list(entity_ids),
            entity_type=entity_type,
            zone_id=zone_id,
            start_time=start_time,
            end_time=None,
            confidence=confidence,
            state=EventState.POTENTIAL,
            evidence=evidence or {},
        )
