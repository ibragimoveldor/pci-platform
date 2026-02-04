"""Crack detection using YOLO."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Detection:
    """Single crack detection result."""
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class CrackDetector:
    """YOLO-based crack detector."""
    
    version = "1.0.0"
    
    CLASS_NAMES = {
        0: "longitudinal_crack",
        1: "transverse_crack",
        2: "alligator_crack",
        3: "pothole",
        4: "patch",
    }
    
    def __init__(self, model_path: str, device: str = "cuda", confidence: float = 0.5):
        """
        Initialize the detector.
        
        Args:
            model_path: Path to YOLO model weights
            device: Device to run inference on ('cuda' or 'cpu')
            confidence: Minimum confidence threshold
        """
        self.model_path = Path(model_path)
        self.device = device
        self.confidence = confidence
        self.model = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.model_path))
                self.model.to(self.device)
            except Exception as e:
                print(f"Warning: Could not load YOLO model: {e}")
                print("Using mock detector for development")
                self.model = "mock"
    
    def detect(self, image_path: Path | str) -> list[Detection]:
        """
        Run crack detection on an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of Detection objects
        """
        self._load_model()
        
        # Mock detection for development
        if self.model == "mock":
            return self._mock_detect(image_path)
        
        # Real detection
        results = self.model(str(image_path), conf=self.confidence, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = self.CLASS_NAMES.get(cls_id, f"class_{cls_id}")
                
                detections.append(Detection(
                    bbox=tuple(bbox),
                    confidence=conf,
                    class_id=cls_id,
                    class_name=cls_name,
                ))
        
        return detections
    
    def _mock_detect(self, image_path: Path | str) -> list[Detection]:
        """Mock detection for development without models."""
        import random
        
        # Generate random detections
        num_detections = random.randint(0, 5)
        detections = []
        
        for _ in range(num_detections):
            x1 = random.uniform(0, 800)
            y1 = random.uniform(0, 600)
            w = random.uniform(50, 200)
            h = random.uniform(50, 200)
            
            cls_id = random.choice(list(self.CLASS_NAMES.keys()))
            
            detections.append(Detection(
                bbox=(x1, y1, x1 + w, y1 + h),
                confidence=random.uniform(0.5, 0.99),
                class_id=cls_id,
                class_name=self.CLASS_NAMES[cls_id],
            ))
        
        return detections
