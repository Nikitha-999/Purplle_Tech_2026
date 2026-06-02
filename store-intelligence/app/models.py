from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventType(str, Enum):
  ENTRY = "ENTRY"
  EXIT = "EXIT"
  ZONE_ENTER = "ZONE_ENTER"
  ZONE_EXIT = "ZONE_EXIT"
  ZONE_DWELL = "ZONE_DWELL"
  REENTRY = "REENTRY"
  BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
  BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"


class CameraId(str, Enum):
  CAM_ENTRY = "CAM_ENTRY"
  CAM_SKINCARE = "CAM_SKINCARE"
  CAM_MAKEUP = "CAM_MAKEUP"
  CAM_BILLING = "CAM_BILLING"
  CAM_BACKROOM = "CAM_BACKROOM"


class ZoneId(str, Enum):
  ENTRY_THRESHOLD = "ENTRY_THRESHOLD"
  FOH_AISLE = "FOH_AISLE"
  SKIN_TOP_WALL = "SKIN_TOP_WALL"
  MAKEUP_BOTTOM_WALL = "MAKEUP_BOTTOM_WALL"
  MAKEUP_STATION = "MAKEUP_STATION"
  BILLING_COUNTER = "BILLING_COUNTER"
  BILLING_QUEUE = "BILLING_QUEUE"
  BACKROOM = "BACKROOM"


class EventMetadata(BaseModel):
  model_config = ConfigDict(extra="allow")

  queue_depth: int | None = None
  sku_zone: str | None = None
  session_seq: int = Field(ge=1)
  track_id: int | None = None
  source: str | None = "pipeline_v1"
  prior_exit_at: str | None = None


class Event(BaseModel):
  """Challenge event schema — matches problem statement."""

  model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

  event_id: str
  store_id: str
  camera_id: str
  visitor_id: str
  event_type: EventType
  timestamp: datetime
  zone_id: str | None = None
  dwell_ms: int = Field(ge=0, default=0)
  is_staff: bool = False
  confidence: float = Field(ge=0.0, le=1.0)
  metadata: EventMetadata

  # Event IDs are opaque identifiers that may come from the camera or pipeline.
  # Do not require UUID format so test fixtures using human-friendly IDs remain valid.

  @field_validator("timestamp", mode="before")
  @classmethod
  def parse_timestamp(cls, value: Any) -> datetime:
    if isinstance(value, datetime):
      return value
    if isinstance(value, str):
      normalized = value.replace("Z", "+00:00")
      return datetime.fromisoformat(normalized)
    raise ValueError("timestamp must be ISO-8601 string or datetime")

  @field_validator("zone_id")
  @classmethod
  def zone_required_for_zone_events(cls, value: str | None, info) -> str | None:
    event_type = info.data.get("event_type")
    zone_events = {
      EventType.ZONE_ENTER,
      EventType.ZONE_EXIT,
      EventType.ZONE_DWELL,
      EventType.BILLING_QUEUE_JOIN,
      EventType.BILLING_QUEUE_ABANDON,
    }
    if event_type in zone_events and not value:
      raise ValueError(f"zone_id is required for {event_type}")
    if event_type in {EventType.ENTRY, EventType.EXIT, EventType.REENTRY} and value is not None:
      raise ValueError(f"zone_id must be null for {event_type}")
    return value


class EventIngestRequest(BaseModel):
  events: list[dict[str, Any]] = Field(max_length=500)


class EventIngestError(BaseModel):
  event_id: str | None = None
  reason: str


class EventIngestResponse(BaseModel):
  accepted: int
  duplicates: int
  rejected: int
  errors: list[EventIngestError]


class StoreHealth(BaseModel):
  store_id: str
  last_event_at: str | None = None
  lag_minutes: float | None = None
  warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
  status: str
  database: str
  version: str
  stores: list[StoreHealth] = Field(default_factory=list)
  warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
  error: str
  detail: str | None = None
  trace_id: str | None = None


class MetricsResponse(BaseModel):
  store_id: str
  date: str
  unique_visitors: int
  converted_visitors: int
  conversion_rate: float
  avg_dwell_by_zone: dict[str, float]
  current_queue_depth: int
  queue_abandonment_rate: float
  total_transactions: int
  data_as_of: str


class FunnelStage(BaseModel):
  name: str
  label: str
  count: int
  drop_off_pct: float


class HeatmapZone(BaseModel):
  zone_id: str
  visit_count: int
  avg_dwell_sec: float
  score_0_100: int


class HeatmapResponse(BaseModel):
  store_id: str
  date: str
  zones: list[HeatmapZone]
  data_confidence: str


class AnomalyItem(BaseModel):
  anomaly_type: str
  severity: str
  zone_id: str | None = None
  description: str


class AnomalyResponse(BaseModel):
  store_id: str
  date: str
  anomalies: list[AnomalyItem]


class FunnelResponse(BaseModel):
  store_id: str
  date: str
  unit: str
  stages: list[FunnelStage]
