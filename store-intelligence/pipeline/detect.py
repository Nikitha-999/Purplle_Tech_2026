"""YOLOv8n person detection (class 0 only)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger("store_intelligence.detect")

_MODEL = None
_DEVICE: str | None = None


@dataclass
class Detection:
    bbox: list[float]
    confidence: float

    @property
    def xyxy(self) -> tuple[float, float, float, float]:
        x1, y1, x2, y2 = self.bbox
        return x1, y1, x2, y2

    @property
    def centroid(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def is_detection_available() -> bool:
    try:
        import ultralytics  # noqa: F401

        return True
    except ImportError:
        return False


def _resolve_device(requested: str | None = None) -> str:
    global _DEVICE
    if requested and requested != "auto":
        _DEVICE = requested
        return _DEVICE
    if _DEVICE:
        return _DEVICE
    try:
        import torch

        _DEVICE = "0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        _DEVICE = "cpu"
    logger.info("detection_device device=%s", _DEVICE)
    return _DEVICE


def get_model(model_name: str = "yolov8n.pt"):
    global _MODEL
    if _MODEL is None:
        from ultralytics import YOLO

        device = _resolve_device()
        _MODEL = YOLO(model_name)
        _MODEL.to(device)
    return _MODEL


def resize_frame(frame: np.ndarray, max_width: int = 960) -> np.ndarray:
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame
    scale = max_width / width
    return cv2.resize(frame, (max_width, int(height * scale)))


def detect_persons(
    frame: np.ndarray,
    *,
    conf: float = 0.35,
    imgsz: int = 640,
    device: str | None = None,
    min_area: float = 1200.0,
    max_width: int = 960,
) -> list[Detection]:
    """
    Run YOLOv8n on a BGR frame and return person detections.

    Output shape per detection: {"bbox": [x1,y1,x2,y2], "confidence": float}
    """
    model = get_model()
    use_device = _resolve_device(device)
    infer_frame = resize_frame(frame, max_width=max_width) if max_width else frame
    scale_x = frame.shape[1] / infer_frame.shape[1]
    scale_y = frame.shape[0] / infer_frame.shape[0]
    results = model.predict(
        infer_frame,
        classes=[0],
        conf=conf,
        imgsz=imgsz,
        device=use_device,
        verbose=False,
    )
    detections: list[Detection] = []
    if not results:
        return detections
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return detections
    for box in boxes:
        xyxy = box.xyxy[0].tolist()
        score = float(box.conf[0])
        x1, y1, x2, y2 = xyxy
        bbox = [x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y]
        det = Detection(bbox=[float(v) for v in bbox], confidence=score)
        if det.area >= min_area:
            detections.append(det)
    return detections


def detections_to_supervision(detections: list[Detection]) -> Any:
    """Convert to supervision Detections for ByteTrack."""
    import supervision as sv

    if not detections:
        return sv.Detections.empty()
    xyxy = np.array([d.xyxy for d in detections], dtype=np.float32)
    confidence = np.array([d.confidence for d in detections], dtype=np.float32)
    class_id = np.zeros(len(detections), dtype=int)
    return sv.Detections(xyxy=xyxy, confidence=confidence, class_id=class_id)
