# agents/services/multimodal_processor.py

import asyncio
import io
import logging
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytesseract
import speech_recognition as sr
from django.core.files.uploadedfile import UploadedFile
from PIL import Image

logger = logging.getLogger(__name__)


class MultiModalProcessor:
    """
    Advanced multi-modal processing system that handles text, images,
    audio, video, and documents with AI-powered analysis and transformation.
    """

    def __init__(self):
        # Default device until torch is imported in _initialize_models
        self.device = "cpu"
        logger.info(
            "MultiModalProcessor initialized (device unknown until models are loaded)"
        )

        # Initialize AI models lazily (imports heavy libs inside this method)
        self._initialize_models()

        # Initialize speech recognition
        self.speech_recognizer = sr.Recognizer()

        # Supported file formats
        self.supported_formats = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "audio": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        }

    def _initialize_models(self):
        """Initialize AI models for various processing tasks."""
        try:
            # Import heavy ML libraries lazily to avoid blocking module import time
            import importlib

            _torch = None
            try:
                _torch = importlib.import_module("torch")
            except Exception:  # noqa: BLE001
                _torch = None

            if _torch is not None:
                self.device = (
                    "cuda"
                    if getattr(_torch, "cuda", None) and _torch.cuda.is_available()
                    else "cpu"
                )
            else:
                self.device = "cpu"

            transformers = None
            try:
                transformers = importlib.import_module("transformers")
            except Exception:  # noqa: BLE001
                transformers = None

            if transformers is None:
                logger.warning(
                    "transformers not available; model pipelines will be disabled"
                )
                self.image_caption_model = None
                self.object_detection_model = None
                self.sentiment_model = None
                self.summarization_model = None
                return

            pipeline = transformers.pipeline

            # Image captioning model
            self.image_caption_model = pipeline(
                "image-to-text",
                model="Salesforce/blip-image-captioning-base",
                device=0 if self.device == "cuda" else -1,
            )

            # Object detection model (YOLO alternative using transformers)
            self.object_detection_model = pipeline(
                "object-detection",
                model="facebook/detr-resnet-50",
                device=0 if self.device == "cuda" else -1,
            )

            # Sentiment analysis model
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1,
            )

            # Text summarization model
            self.summarization_model = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if self.device == "cuda" else -1,
            )

            logger.info("AI models initialized successfully")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error initializing AI models: {e}")
            # Initialize placeholder models
            self.image_caption_model = None
            self.object_detection_model = None
            self.sentiment_model = None
            self.summarization_model = None

    async def process_multimodal_input(
        self, input_data: dict, processing_options: dict | None = None
    ) -> dict:
        """
        Process multi-modal input data and return comprehensive analysis.

        Args:
            input_data: Dictionary containing various types of input data
            processing_options: Optional processing configuration

        Returns:
            Comprehensive analysis results
        """

        processing_options = processing_options or {}
        results = {
            "processing_id": f"proc_{int(asyncio.get_event_loop().time() * 1000)}",
            "input_types": [],
            "results": {},
            "metadata": {},
            "processing_time": 0,
        }

        start_time = asyncio.get_event_loop().time()

        try:
            # Process different input types
            processing_tasks = []

            if "text" in input_data:
                results["input_types"].append("text")
                processing_tasks.append(
                    ("text", self._process_text(input_data["text"], processing_options))
                )

            if "image" in input_data:
                results["input_types"].append("image")
                processing_tasks.append(
                    (
                        "image",
                        self._process_image(input_data["image"], processing_options),
                    )
                )

            if "audio" in input_data:
                results["input_types"].append("audio")
                processing_tasks.append(
                    (
                        "audio",
                        self._process_audio(input_data["audio"], processing_options),
                    )
                )

            if "video" in input_data:
                results["input_types"].append("video")
                processing_tasks.append(
                    (
                        "video",
                        self._process_video(input_data["video"], processing_options),
                    )
                )

            if "document" in input_data:
                results["input_types"].append("document")
                processing_tasks.append(
                    (
                        "document",
                        self._process_document(
                            input_data["document"], processing_options
                        ),
                    )
                )

            # Execute processing tasks
            if processing_tasks:
                task_results = await asyncio.gather(
                    *[task for _, task in processing_tasks]
                )

                for (input_type, _), result in zip(processing_tasks, task_results):
                    results["results"][input_type] = result

            # Cross-modal analysis if multiple inputs
            if len(results["input_types"]) > 1:
                results["results"]["cross_modal"] = await self._cross_modal_analysis(
                    results["results"]
                )

            # Calculate processing time
            results["processing_time"] = asyncio.get_event_loop().time() - start_time

            logger.info(
                f"Multi-modal processing completed in {results['processing_time']:.2f}s"
            )

            return results

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in multi-modal processing: {e}")
            results["error"] = str(e)
            results["processing_time"] = asyncio.get_event_loop().time() - start_time
            return results

    async def _process_text(self, text_data: str | dict, options: dict) -> dict:
        """Process text data with various AI analysis."""

        if isinstance(text_data, dict):
            text = text_data.get("content", "")
            language = text_data.get("language", "en")
        else:
            text = str(text_data)
            language = "en"

        result = {
            "content": text,
            "language": language,
            "statistics": {},
            "analysis": {},
        }

        try:
            # Basic text statistics
            result["statistics"] = {
                "character_count": len(text),
                "word_count": len(text.split()),
                "sentence_count": len([s for s in text.split(".") if s.strip()]),
                "paragraph_count": len([p for p in text.split("\n\n") if p.strip()]),
            }

            # Sentiment analysis
            if self.sentiment_model and options.get("analyze_sentiment", True):
                try:
                    sentiment_result = self.sentiment_model(
                        text[:512]
                    )  # Limit for model
                    result["analysis"]["sentiment"] = (
                        sentiment_result[0] if sentiment_result else None
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Sentiment analysis failed: {e}")

            # Text summarization for longer texts
            if (
                self.summarization_model
                and options.get("summarize", True)
                and len(text) > 500
            ):
                try:
                    # Split long text into chunks
                    chunks = [text[i : i + 1024] for i in range(0, len(text), 1024)]
                    summaries = []

                    for chunk in chunks[:3]:  # Limit to first 3 chunks
                        summary = self.summarization_model(
                            chunk, max_length=150, min_length=50, do_sample=False
                        )
                        if summary:
                            summaries.append(summary[0]["summary_text"])

                    result["analysis"]["summary"] = (
                        " ".join(summaries) if summaries else None
                    )

                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Text summarization failed: {e}")

            # Keyword extraction (simple implementation)
            if options.get("extract_keywords", True):
                result["analysis"]["keywords"] = await self._extract_keywords(text)

            # Language detection (simple heuristic)
            if options.get("detect_language", True):
                result["analysis"]["detected_language"] = await self._detect_language(
                    text
                )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing text: {e}")
            result["error"] = str(e)

        return result

    async def _process_image(
        self, image_data: UploadedFile | str | bytes, options: dict
    ) -> dict:
        """Process image data with computer vision analysis."""

        result = {"format": None, "dimensions": {}, "analysis": {}, "metadata": {}}

        try:
            # Load image
            if isinstance(image_data, UploadedFile):
                image = Image.open(image_data)
                result["format"] = image.format or "Unknown"
            elif isinstance(image_data, str):  # File path
                image = Image.open(image_data)
                result["format"] = image.format or Path(image_data).suffix[1:].upper()
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
                result["format"] = image.format or "Unknown"
            else:
                raise TypeError("Unsupported image data type")

            # Basic image properties
            result["dimensions"] = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "channels": len(image.getbands()),
            }

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Image captioning
            if self.image_caption_model and options.get("generate_caption", True):
                try:
                    captions = self.image_caption_model(image)
                    result["analysis"]["caption"] = (
                        captions[0]["generated_text"] if captions else None
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Image captioning failed: {e}")

            # Object detection
            if self.object_detection_model and options.get("detect_objects", True):
                try:
                    objects = self.object_detection_model(image)
                    result["analysis"]["objects"] = []

                    for obj in objects:
                        result["analysis"]["objects"].append(
                            {
                                "label": obj["label"],
                                "confidence": obj["score"],
                                "bbox": obj["box"],
                            }
                        )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Object detection failed: {e}")

            # OCR text extraction
            if options.get("extract_text", True):
                try:
                    # Convert PIL image to numpy array for pytesseract
                    img_array = np.array(image)
                    extracted_text = pytesseract.image_to_string(img_array)

                    if extracted_text.strip():
                        result["analysis"]["ocr_text"] = extracted_text.strip()
                        result["analysis"]["text_confidence"] = (
                            pytesseract.image_to_data(
                                img_array, output_type=pytesseract.Output.DICT
                            )
                        )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"OCR failed: {e}")

            # Color analysis
            if options.get("analyze_colors", True):
                result["analysis"]["colors"] = await self._analyze_image_colors(image)

            # Face detection using OpenCV
            if options.get("detect_faces", True):
                result["analysis"]["faces"] = await self._detect_faces(np.array(image))

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing image: {e}")
            result["error"] = str(e)

        return result

    async def _process_audio(
        self, audio_data: UploadedFile | str | bytes, options: dict
    ) -> dict:
        """Process audio data with speech recognition and analysis."""

        result = {"format": None, "duration": 0, "analysis": {}, "metadata": {}}

        try:
            # Save audio to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                if isinstance(audio_data, UploadedFile):
                    for chunk in audio_data.chunks():
                        temp_file.write(chunk)
                    result["format"] = (
                        audio_data.name.split(".")[-1]
                        if "." in audio_data.name
                        else "unknown"
                    )
                elif isinstance(audio_data, str):  # File path
                    with open(audio_data, "rb") as f:  # noqa: ASYNC230
                        temp_file.write(f.read())
                    result["format"] = Path(audio_data).suffix[1:]
                elif isinstance(audio_data, bytes):
                    temp_file.write(audio_data)
                    result["format"] = "unknown"

                temp_path = temp_file.name

            # Speech-to-text conversion
            if options.get("speech_to_text", True):
                try:
                    with sr.AudioFile(temp_path) as source:
                        audio = self.speech_recognizer.record(source)

                    # Try different recognition engines
                    transcription_results = {}

                    # Google Speech Recognition (free tier)
                    try:
                        text = self.speech_recognizer.recognize_google(audio)
                        transcription_results["google"] = {
                            "text": text,
                            "confidence": "unknown",  # Google API doesn't return confidence
                        }
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"Google speech recognition failed: {e}")

                    # Add the best transcription to results
                    if transcription_results:
                        best_transcription = next(iter(transcription_results.values()))
                        result["analysis"]["transcription"] = best_transcription["text"]
                        result["analysis"]["transcription_confidence"] = (
                            best_transcription["confidence"]
                        )
                        result["analysis"]["all_transcriptions"] = transcription_results

                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Speech recognition failed: {e}")

            # Audio analysis (duration, frequency analysis, etc.)
            if options.get("analyze_audio", True):
                result["analysis"]["audio_properties"] = (
                    await self._analyze_audio_properties(temp_path)
                )

            # Clean up temporary file
            try:
                Path(temp_path).unlink()
            except Exception as cleanup_err:  # noqa: BLE001
                logger.warning(f"Failed to cleanup temp audio file: {cleanup_err}")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing audio: {e}")
            result["error"] = str(e)

        return result

    async def _process_video(
        self, video_data: UploadedFile | str | bytes, options: dict
    ) -> dict:
        """Process video data with frame analysis and content extraction."""

        result = {
            "format": None,
            "duration": 0,
            "frame_count": 0,
            "fps": 0,
            "resolution": {},
            "analysis": {},
        }

        try:
            # Save video to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                if isinstance(video_data, UploadedFile):
                    for chunk in video_data.chunks():
                        temp_file.write(chunk)
                    result["format"] = (
                        video_data.name.split(".")[-1]
                        if "." in video_data.name
                        else "unknown"
                    )
                elif isinstance(video_data, str):  # File path
                    with open(video_data, "rb") as f:  # noqa: ASYNC230
                        temp_file.write(f.read())
                    result["format"] = Path(video_data).suffix[1:]
                elif isinstance(video_data, bytes):
                    temp_file.write(video_data)
                    result["format"] = "unknown"

                temp_path = temp_file.name

            # Analyze video properties
            cap = cv2.VideoCapture(temp_path)

            if cap.isOpened():
                # Get video properties
                result["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                result["fps"] = cap.get(cv2.CAP_PROP_FPS)
                result["duration"] = (
                    result["frame_count"] / result["fps"] if result["fps"] > 0 else 0
                )
                result["resolution"] = {
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                }

                # Extract key frames for analysis
                if options.get("analyze_frames", True):
                    key_frames = await self._extract_key_frames(
                        cap, options.get("max_frames", 5)
                    )
                    result["analysis"]["key_frames"] = []

                    for i, frame in enumerate(key_frames):
                        # Convert frame to PIL Image for processing
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_image = Image.fromarray(frame_rgb)

                        # Analyze frame
                        frame_analysis = await self._process_image(
                            frame_image,
                            {
                                "generate_caption": True,
                                "detect_objects": True,
                                "extract_text": False,  # Skip OCR for video frames
                            },
                        )

                        result["analysis"]["key_frames"].append(
                            {"frame_index": i, **frame_analysis}
                        )

                cap.release()

            # Extract audio from video if requested
            if options.get("extract_audio", True):
                audio_result = await self._extract_video_audio(temp_path)
                result["analysis"]["audio"] = audio_result

            # Clean up temporary file
            try:
                Path(temp_path).unlink()
            except Exception as cleanup_err:  # noqa: BLE001
                logger.warning(f"Failed to cleanup temp video file: {cleanup_err}")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing video: {e}")
            result["error"] = str(e)

        return result

    async def _process_document(
        self, document_data: UploadedFile | str | bytes, options: dict
    ) -> dict:
        """Process document data with text extraction and analysis."""

        result = {"format": None, "page_count": 0, "analysis": {}, "content": {}}

        try:
            # Determine document format and extract text
            if isinstance(document_data, UploadedFile):
                filename = document_data.name
                result["format"] = (
                    filename.split(".")[-1].lower() if "." in filename else "unknown"
                )
            elif isinstance(document_data, str):
                filename = document_data
                result["format"] = Path(document_data).suffix[1:].lower()
            else:
                result["format"] = "unknown"

            # Extract text based on format
            extracted_text = ""

            if result["format"] == "pdf":
                extracted_text = await self._extract_pdf_text(document_data)
            elif result["format"] in ["doc", "docx"]:
                extracted_text = await self._extract_word_text(document_data)
            elif result["format"] == "txt":
                if isinstance(document_data, UploadedFile):
                    extracted_text = document_data.read().decode("utf-8")
                elif isinstance(document_data, str):
                    with open(  # noqa: ASYNC230
                        document_data, "r", encoding="utf-8"
                    ) as f:
                        extracted_text = f.read()
                elif isinstance(document_data, bytes):
                    extracted_text = document_data.decode("utf-8")

            result["content"]["text"] = extracted_text

            # Analyze extracted text
            if extracted_text and options.get("analyze_text", True):
                text_analysis = await self._process_text(extracted_text, options)
                result["analysis"]["text_analysis"] = text_analysis

            # Document structure analysis
            if options.get("analyze_structure", True):
                result["analysis"]["structure"] = (
                    await self._analyze_document_structure(extracted_text)
                )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing document: {e}")
            result["error"] = str(e)

        return result

    async def _cross_modal_analysis(self, modal_results: dict) -> dict:
        """Perform cross-modal analysis to find connections between different input types."""

        cross_modal = {"correlations": [], "insights": [], "combined_narrative": None}

        try:
            # Text-Image correlation
            if "text" in modal_results and "image" in modal_results:
                text_content = modal_results["text"].get("content", "")
                image_caption = (
                    modal_results["image"].get("analysis", {}).get("caption", "")
                )

                if text_content and image_caption:
                    correlation = await self._calculate_text_similarity(
                        text_content, image_caption
                    )
                    cross_modal["correlations"].append(
                        {
                            "type": "text-image",
                            "correlation_score": correlation,
                            "description": f"Text and image caption similarity: {correlation:.2f}",
                        }
                    )

            # Text-Audio correlation (transcription)
            if "text" in modal_results and "audio" in modal_results:
                text_content = modal_results["text"].get("content", "")
                audio_transcription = (
                    modal_results["audio"].get("analysis", {}).get("transcription", "")
                )

                if text_content and audio_transcription:
                    correlation = await self._calculate_text_similarity(
                        text_content, audio_transcription
                    )
                    cross_modal["correlations"].append(
                        {
                            "type": "text-audio",
                            "correlation_score": correlation,
                            "description": f"Text and audio transcription similarity: {correlation:.2f}",
                        }
                    )

            # Generate combined narrative
            cross_modal["combined_narrative"] = await self._generate_combined_narrative(
                modal_results
            )

            # Generate insights
            cross_modal["insights"] = await self._generate_cross_modal_insights(
                modal_results, cross_modal["correlations"]
            )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in cross-modal analysis: {e}")
            cross_modal["error"] = str(e)

        return cross_modal

    # Helper methods (implementations would be more detailed in production)

    async def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text using simple frequency analysis."""
        # Simplified implementation
        words = text.lower().split()
        word_freq = {}

        # Filter common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }

        for word in words:
            word = word.strip('.,!?";')
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return top 10 keywords
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    async def _detect_language(self, text: str) -> str:
        """Language detection using TextBlob."""
        try:
            from textblob import TextBlob

            b = TextBlob(text)
            if len(text) > 3:
                return b.detect_language()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Language detection failed: {e}")
        return "en"  # Default to English

    async def _analyze_image_colors(self, image: Image.Image) -> dict:
        """Analyze dominant colors in image."""
        # Convert image to RGB and get color palette
        image_rgb = image.convert("RGB")

        # Get dominant colors (simplified)
        colors = image_rgb.getcolors(maxcolors=256 * 256 * 256)
        if colors:
            dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
            return {
                "dominant_colors": [
                    {"color": color[1], "count": color[0]} for color in dominant_colors
                ],
                "total_colors": len(colors),
            }

        return {}

    async def _detect_faces(self, image_array: np.ndarray) -> list[dict]:
        """Detect faces in image using OpenCV."""
        try:
            # Load face cascade classifier
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            face_list = []
            for x, y, w, h in faces:
                face_list.append(
                    {
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "confidence": 1.0,  # OpenCV doesn't provide confidence scores
                    }
                )

            return face_list

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Face detection failed: {e}")
            return []

    async def _analyze_audio_properties(self, audio_path: str) -> dict:
        """Analyze audio properties using pydub."""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)
            return {
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "bit_depth": audio.sample_width * 8,
                "duration_seconds": len(audio) / 1000.0,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Audio properties analysis failed: {e}")
            return {"sample_rate": 44100, "channels": 2, "bit_depth": 16}

    async def _extract_key_frames(
        self, cap: cv2.VideoCapture, max_frames: int
    ) -> list[np.ndarray]:
        """Extract key frames from video."""
        frames = []
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count > 0:
            # Extract frames at regular intervals
            interval = max(frame_count // max_frames, 1)

            for i in range(0, frame_count, interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                    if len(frames) >= max_frames:
                        break

        return frames

    async def _extract_video_audio(self, video_path: str) -> dict:
        """Extract audio from video file."""
        try:
            from pydub import AudioSegment

            # pydub can extract audio from mp4 if ffmpeg is installed
            audio = AudioSegment.from_file(video_path)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio.export(tmp_file.name, format="wav")
                extracted_path = tmp_file.name

            # Process extracted audio
            audio_analysis = await self._process_audio(
                extracted_path, {"analyze_audio": True, "speech_to_text": True}
            )

            try:
                Path(extracted_path).unlink()
            except Exception:  # noqa: BLE001, S110
                pass

            return audio_analysis
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Video audio extraction failed: {e}")
            return {"error": "Could not extract audio from video"}

    async def _extract_pdf_text(self, pdf_data: UploadedFile | str | bytes) -> str:
        """Extract text from PDF document."""
        # Placeholder implementation - would use PyPDF2 or pdfplumber in production
        return "PDF text extraction not implemented in demo"

    async def _extract_word_text(self, doc_data: UploadedFile | str | bytes) -> str:
        """Extract text from Word document."""
        # Placeholder implementation - would use python-docx in production
        return "Word document text extraction not implemented in demo"

    async def _analyze_document_structure(self, text: str) -> dict:
        """Analyze document structure (headings, paragraphs, etc.)."""
        lines = text.split("\n")

        return {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "estimated_paragraphs": len(
                [line for line in lines if line.strip() and not line.startswith(" ")]
            ),
        }

    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _generate_combined_narrative(self, modal_results: dict) -> str:
        """Generate a combined narrative from all modal results."""
        narrative_parts = []

        if "text" in modal_results:
            text_content = modal_results["text"].get("content", "")[
                :200
            ]  # First 200 chars
            narrative_parts.append(f"Text content: {text_content}")

        if "image" in modal_results:
            caption = modal_results["image"].get("analysis", {}).get("caption", "")
            if caption:
                narrative_parts.append(f"Image shows: {caption}")

        if "audio" in modal_results:
            transcription = (
                modal_results["audio"].get("analysis", {}).get("transcription", "")
            )
            if transcription:
                narrative_parts.append(f"Audio contains: {transcription}")

        return ". ".join(narrative_parts)

    async def _generate_cross_modal_insights(
        self, modal_results: dict, correlations: list[dict]
    ) -> list[str]:
        """Generate insights from cross-modal analysis."""
        insights = []

        # Analyze correlations
        for correlation in correlations:
            if correlation["correlation_score"] > 0.5:
                insights.append(f"High correlation found between {correlation['type']}")
            elif correlation["correlation_score"] > 0.3:
                insights.append(
                    f"Moderate correlation found between {correlation['type']}"
                )

        # Content type insights
        if len(modal_results) > 2:
            insights.append(
                "Multi-modal input detected - rich content analysis available"
            )

        return insights
