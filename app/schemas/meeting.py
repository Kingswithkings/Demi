from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


DEFAULT_DURATION_MINS = 30


def _parse_dt(value: str) -> datetime:
    """
    Parse ISO 8601 datetime. Accepts strings like:
    2025-12-26T18:00:00
    2025-12-26T18:00:00+00:00
    """
    try:
        # Supports 'Z' suffix as UTC
        v = value.replace("Z", "+00:00")
        return datetime.fromisoformat(v)
    except Exception as e:
        raise ValueError(f"Invalid datetime format: {value}. Use ISO 8601.") from e


class MeetingRequest(BaseModel):
    title: str = Field(default="Meeting", min_length=1)
    start_time: str
    end_time: Optional[str] = None

    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    notes: Optional[str] = None

    # --- Validators ---
    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        _parse_dt(v)
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        _parse_dt(v)
        return v

    @field_validator("attendees")
    @classmethod
    def normalize_attendees(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen = set()
        for email in v or []:
            e = (email or "").strip()
            if not e:
                continue
            e_lc = e.lower()
            if e_lc in seen:
                continue
            seen.add(e_lc)
            cleaned.append(e)
        return cleaned

    @model_validator(mode="after")
    def ensure_end_time(self) -> "MeetingRequest":
        """
        If end_time not provided, set default end_time = start_time + DEFAULT_DURATION_MINS.
        """
        if not self.end_time:
            start_dt = _parse_dt(self.start_time)
            end_dt = start_dt + timedelta(minutes=DEFAULT_DURATION_MINS)
            self.end_time = end_dt.isoformat()
        return self


class Meeting(BaseModel):
    id: str
    title: str = Field(min_length=1)
    start_time: str
    end_time: str

    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    notes: Optional[str] = None

    # Keep the same normalisation/validation rules
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_times(cls, v: str) -> str:
        _parse_dt(v)
        return v

    @field_validator("attendees")
    @classmethod
    def normalize_attendees(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen = set()
        for email in v or []:
            e = (email or "").strip()
            if not e:
                continue
            e_lc = e.lower()
            if e_lc in seen:
                continue
            seen.add(e_lc)
            cleaned.append(e)
        return cleaned
