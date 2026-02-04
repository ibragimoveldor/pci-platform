"""Crack segmentation module."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np

from app.ml.detector import Detection


@dataclass
class Segment:
    """Crack segmentation result."""
    detection_idx: int
    mask: Any  # numpy array or encoded mask
    area_pixels: int
    severity: str  # 'low', 'medium', 'high'
    width_avg: float  # average crack width in pixels
    length: float  # crack length in pixels
    
    def to_dict(self) -> dict:
        d = asdict(self)
        # Don't include mask in serialization
        d.pop("mask", None)
        return d


class CrackSegmentor:
    """Crack segmentation model."""
    
    version = "1.0.0"
    
    # Severity thresholds based on crack width (in mm, assuming known pixel scale)
    SEVERITY_THRESHOLDS = {
        "low": (0, 3),      # < 3mm
        "medium": (3, 10),  # 3-10mm
        "high": (10, 100),  # > 10mm
    }
    
    def __init__(self, model_path: str, device: str = "cuda"):
        """
        Initialize the segmentor.
        
        Args:
            model_path: Path to segmentation model weights
            device: Device to run inference on
        """
        self.model_path = Path(model_path)
        self.device = device
        self.model = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            try:
                # Load your segmentation model here
                # Example: self.model = torch.load(self.model_path)
                print(f"Loading segmentation model from {self.model_path}")
                self.model = "mock"  # Use mock for now
            except Exception as e:
                print(f"Warning: Could not load segmentation model: {e}")
                self.model = "mock"
    
    def segment(self, image_path: Path | str, detections: list[Detection]) -> list[Segment]:
        """
        Segment cracks in an image based on detections.
        
        Args:
            image_path: Path to the image
            detections: List of Detection objects from crack detector
            
        Returns:
            List of Segment objects
        """
        self._load_model()
        
        if self.model == "mock":
            return self._mock_segment(detections)
        
        # Real segmentation implementation
        segments = []
        
        # Load image
        import cv2
        image = cv2.imread(str(image_path))
        
        for i, detection in enumerate(detections):
            # Crop detection region
            x1, y1, x2, y2 = map(int, detection.bbox)
            crop = image[y1:y2, x1:x2]
            
            # Run segmentation on crop
            # mask = self.model.predict(crop)
            
            # Calculate metrics
            # area = np.sum(mask > 0.5)
            # width, length = self._calculate_crack_dimensions(mask)
            # severity = self._classify_severity(width)
            
            # Mock values for now
            area = (x2 - x1) * (y2 - y1) * 0.3
            width = 5.0
            length = max(x2 - x1, y2 - y1)
            severity = self._classify_severity(width)
            
            segments.append(Segment(
                detection_idx=i,
                mask=None,  # Don't store full mask
                area_pixels=int(area),
                severity=severity,
                width_avg=width,
                length=length,
            ))
        
        return segments
    
    def _classify_severity(self, width: float) -> str:
        """Classify crack severity based on width."""
        for severity, (min_w, max_w) in self.SEVERITY_THRESHOLDS.items():
            if min_w <= width < max_w:
                return severity
        return "high"
    
    def _mock_segment(self, detections: list[Detection]) -> list[Segment]:
        """Mock segmentation for development."""
        import random
        
        segments = []
        for i, detection in enumerate(detections):
            x1, y1, x2, y2 = detection.bbox
            area = (x2 - x1) * (y2 - y1) * random.uniform(0.2, 0.5)
            width = random.uniform(1, 15)
            
            segments.append(Segment(
                detection_idx=i,
                mask=None,
                area_pixels=int(area),
                severity=self._classify_severity(width),
                width_avg=width,
                length=max(x2 - x1, y2 - y1),
            ))
        
        return segments
