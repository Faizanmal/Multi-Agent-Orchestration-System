import logging
import os
from typing import Any

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service for processing visual content including images and videos
    """

    def __init__(self):
        self.supported_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
        self.ocr_languages = ["eng"]  # Can be extended

    def analyze_image(self, image_path: str) -> dict[str, Any]:
        """
        Comprehensive image analysis

        Args:
            image_path: Path to the image file

        Returns:
            Analysis results including objects, text, metadata
        """
        try:
            if not os.path.exists(image_path):
                return {"error": "Image file not found"}

            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Could not load image"}

            pil_image = Image.open(image_path)

            analysis = {
                "basic_info": self._get_basic_image_info(pil_image),
                "objects": self._detect_objects(image),
                "text": self._extract_text(pil_image),
                "colors": self._analyze_colors(image),
                "composition": self._analyze_composition(image),
                "quality_metrics": self._assess_image_quality(image),
            }

            return analysis

        except Exception as e:  # noqa: BLE001
            logger.error(f"Image analysis error: {e!s}")
            return {"error": str(e)}

    def _get_basic_image_info(self, image: Image.Image) -> dict[str, Any]:
        """Get basic image information"""
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_mb": len(image.tobytes()) / (1024 * 1024),
        }

    def _detect_objects(self, image: np.ndarray) -> list[dict[str, Any]]:
        """
        Detect objects in image using OpenCV
        Note: This is a basic implementation. For production,
        consider using YOLO, SSD, or other advanced models
        """
        try:
            # Convert to grayscale for basic feature detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect faces using Haar Cascades
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            objects = []

            # Add detected faces
            for x, y, w, h in faces:
                objects.append(
                    {
                        "type": "face",
                        "confidence": 0.8,  # Placeholder confidence
                        "bbox": {
                            "x": int(x),
                            "y": int(y),
                            "width": int(w),
                            "height": int(h),
                        },
                    }
                )

            # Basic edge detection for general objects
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Filter significant contours
            significant_contours = [c for c in contours if cv2.contourArea(c) > 1000]

            for contour in significant_contours[:10]:  # Limit to top 10
                x, y, w, h = cv2.boundingRect(contour)
                objects.append(
                    {
                        "type": "object",
                        "confidence": 0.6,
                        "bbox": {
                            "x": int(x),
                            "y": int(y),
                            "width": int(w),
                            "height": int(h),
                        },
                    }
                )

            return objects

        except Exception as e:  # noqa: BLE001
            logger.error(f"Object detection error: {e!s}")
            return []

    def _extract_text(self, image: Image.Image) -> dict[str, Any]:
        """Extract text using OCR"""
        try:
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)

            # Get detailed OCR data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Filter out low confidence text
            words = []
            confidences = data["conf"]
            texts = data["text"]

            for i, conf in enumerate(confidences):
                if conf > 30 and texts[i].strip():  # Confidence threshold
                    words.append(
                        {
                            "text": texts[i],
                            "confidence": conf,
                            "bbox": {
                                "x": data["left"][i],
                                "y": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                            },
                        }
                    )

            return {
                "full_text": text.strip(),
                "words": words,
                "word_count": len(text.split()),
                "languages_detected": [
                    "en"
                ],  # Could be enhanced with language detection
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"OCR error: {e!s}")
            return {"full_text": "", "words": [], "word_count": 0, "error": str(e)}

    def _analyze_colors(self, image: np.ndarray) -> dict[str, Any]:
        """Analyze color composition of image"""
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Reshape for k-means clustering
            pixels = rgb_image.reshape(-1, 3)

            # Simple dominant color detection
            unique_colors, counts = np.unique(
                pixels.reshape(-1, pixels.shape[-1]), axis=0, return_counts=True
            )

            # Get top 5 colors
            top_indices = np.argsort(counts)[-5:][::-1]
            dominant_colors = []

            for idx in top_indices:
                color = unique_colors[idx]
                percentage = (counts[idx] / len(pixels)) * 100
                dominant_colors.append(
                    {
                        "rgb": color.tolist(),
                        "hex": "#{:02x}{:02x}{:02x}".format(*color),
                        "percentage": float(percentage),
                    }
                )

            # Basic color analysis
            avg_brightness = np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))

            return {
                "dominant_colors": dominant_colors,
                "average_brightness": float(avg_brightness),
                "color_variety": len(unique_colors),
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Color analysis error: {e!s}")
            return {"error": str(e)}

    def _analyze_composition(self, image: np.ndarray) -> dict[str, Any]:
        """Analyze image composition"""
        try:
            height, width = image.shape[:2]

            # Basic composition analysis
            composition = {
                "aspect_ratio": width / height,
                "resolution_category": self._categorize_resolution(width, height),
                "orientation": (
                    "landscape"
                    if width > height
                    else "portrait" if height > width else "square"
                ),
            }

            # Rule of thirds analysis
            thirds_x = [width // 3, 2 * width // 3]
            thirds_y = [height // 3, 2 * height // 3]

            composition["rule_of_thirds"] = {
                "vertical_lines": thirds_x,
                "horizontal_lines": thirds_y,
            }

            return composition

        except Exception as e:  # noqa: BLE001
            logger.error(f"Composition analysis error: {e!s}")
            return {"error": str(e)}

    def _assess_image_quality(self, image: np.ndarray) -> dict[str, Any]:
        """Assess basic image quality metrics"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Blur detection using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Noise estimation
            noise_score = np.std(gray)

            # Contrast assessment
            contrast = gray.std()

            quality = {
                "blur_score": float(blur_score),
                "is_blurry": blur_score < 100,  # Threshold for blur detection
                "noise_level": float(noise_score),
                "contrast": float(contrast),
                "overall_quality": (
                    "high"
                    if blur_score > 300 and contrast > 50
                    else "medium" if blur_score > 100 else "low"
                ),
            }

            return quality

        except Exception as e:  # noqa: BLE001
            logger.error(f"Quality assessment error: {e!s}")
            return {"error": str(e)}

    def _categorize_resolution(self, width: int, height: int) -> str:
        """Categorize image resolution"""
        total_pixels = width * height

        if total_pixels >= 8000000:  # 8MP+
            return "high"
        elif total_pixels >= 2000000:  # 2MP+
            return "medium"
        else:
            return "low"

    def process_video_frame(
        self, video_path: str, frame_number: int = 0
    ) -> dict[str, Any]:
        """
        Process a single frame from video

        Args:
            video_path: Path to video file
            frame_number: Frame number to process (0 for first frame)

        Returns:
            Frame analysis results
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return {"error": "Could not open video file"}

            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            if not ret:
                cap.release()
                return {"error": "Could not read frame"}

            # Analyze frame as image
            analysis = {
                "frame_number": frame_number,
                "video_info": self._get_video_info(cap),
                "frame_analysis": {
                    "objects": self._detect_objects(frame),
                    "colors": self._analyze_colors(frame),
                    "composition": self._analyze_composition(frame),
                },
            }

            cap.release()
            return analysis

        except Exception as e:  # noqa: BLE001
            logger.error(f"Video frame processing error: {e!s}")
            return {"error": str(e)}

    def _get_video_info(self, cap) -> dict[str, Any]:
        """Get basic video information"""
        try:
            return {
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration_seconds": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                / cap.get(cv2.CAP_PROP_FPS),
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Video info error: {e!s}")
            return {}

    def generate_image_description(self, analysis: dict[str, Any]) -> str:
        """
        Generate natural language description of image analysis

        Args:
            analysis: Image analysis results

        Returns:
            Natural language description
        """
        description_parts = []

        # Basic info
        if "basic_info" in analysis:
            info = analysis["basic_info"]
            description_parts.append(
                f"This is a {info.get('width', 0)}x{info.get('height', 0)} pixel {info.get('format', 'image').lower()} image."
            )

        # Objects
        if analysis.get("objects"):
            object_count = len(analysis["objects"])
            face_count = len(
                [obj for obj in analysis["objects"] if obj.get("type") == "face"]
            )

            if face_count > 0:
                description_parts.append(
                    f"The image contains {face_count} detected face(s)."
                )

            if object_count > face_count:
                description_parts.append(
                    f"Additional {object_count - face_count} objects or regions of interest were detected."
                )

        # Text
        if "text" in analysis and analysis["text"].get("full_text"):
            text_content = analysis["text"]["full_text"]
            word_count = analysis["text"].get("word_count", 0)
            description_parts.append(
                f"The image contains text with approximately {word_count} words."
            )
            if len(text_content) < 200:
                description_parts.append(f"The text reads: '{text_content}'")

        # Colors
        if "colors" in analysis and "dominant_colors" in analysis["colors"]:
            dominant_colors = analysis["colors"]["dominant_colors"][:3]  # Top 3 colors
            color_names = [color["hex"] for color in dominant_colors]
            description_parts.append(
                f"The dominant colors are {', '.join(color_names)}."
            )

        # Quality
        if "quality_metrics" in analysis:
            quality = analysis["quality_metrics"].get("overall_quality", "unknown")
            description_parts.append(f"The image quality appears to be {quality}.")

        return (
            " ".join(description_parts)
            if description_parts
            else "Unable to generate image description."
        )
