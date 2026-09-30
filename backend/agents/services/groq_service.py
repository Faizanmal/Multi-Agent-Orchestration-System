import json
import logging
import os
from collections.abc import Generator
from typing import Any

from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)


class GroqService:
    """Service for integrating with Groq API for fast inference"""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY"))
        self.default_model = settings.GROQ_CONFIG.get(
            "MODEL", "llama-3.3-70b-versatile"
        )
        self.default_temperature = settings.GROQ_CONFIG.get("TEMPERATURE", 0.7)
        self.default_max_tokens = settings.GROQ_CONFIG.get("MAX_TOKENS", 2048)

    def chat_completion(
        self, messages: list[dict], model: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Get chat completion from Groq API with enhanced performance and error handling

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            **kwargs: Additional parameters

        Returns:
            Dict containing the response
        """
        try:
            # Ensure markdown formatting system prompt
            has_system_message = any(msg.get("role") == "system" for msg in messages)
            if not has_system_message:
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": """You are a helpful AI assistant.

CRITICAL FORMATTING REQUIREMENTS:
- You MUST format ALL responses using proper Markdown syntax
- Use headers: ## Header for sections
- Use **bold text** for emphasis
- Use bullet points: - Item for lists
- Use numbered lists: 1. Item for steps
- Use `inline code` for code references
- Use ```language code blocks for code examples
- Structure your response with clear sections and formatting

EXAMPLE FORMAT:
## Introduction
Hello, I'm your AI assistant.

## What I Can Help With
- **General Questions**: Answering various topics
- **Code Support**: Helping with programming

## Getting Started
To begin, simply ask me a question!

```python
print("Hello, World!")
```

Please format ALL your responses this way. Never use plain text paragraphs.""",
                    },
                )

            # Enhanced parameters for better performance
            temperature = kwargs.get("temperature", self.default_temperature)
            max_tokens = kwargs.get("max_tokens", self.default_max_tokens)
            stream = kwargs.get("stream", False)

            # Optimize parameters based on message length for better performance
            if len(str(messages)) < 500:
                # For short messages, use faster parameters
                temperature = min(temperature, 0.5)  # Less creativity for simple tasks
                max_tokens = min(max_tokens, 512)  # Limit tokens for faster response

            response = self.client.chat.completions.create(
                messages=messages,
                model=model or self.default_model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )

            if stream:
                return self._handle_stream_response(response)

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
                "response_time": response.usage.completion_tokens
                / 1000,  # Approximate response time
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Groq API error: {e!s}")
            return {"error": str(e), "content": None}

    def stream_completion(
        self,
        messages: list[dict],
        session_id: str | None = None,
        model: str | None = None,
    ) -> Generator:
        """
        Stream chat completion from Groq API

        Args:
            messages: List of message dictionaries
            session_id: Session ID for WebSocket updates
            model: Model to use

        Yields:
            Chunks of the response
        """
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=model or self.default_model,
                temperature=self.default_temperature,
                max_tokens=self.default_max_tokens,
                stream=True,
            )

            full_content = ""

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_content += content

                    # Send to WebSocket if session_id provided
                    if session_id:
                        self._send_stream_update(session_id, content, full_content)

                    yield {
                        "content": content,
                        "full_content": full_content,
                        "done": False,
                    }

            yield {"content": "", "full_content": full_content, "done": True}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Groq streaming error: {e!s}")
            yield {"error": str(e), "content": "", "done": True}

    def _handle_stream_response(self, stream) -> dict[str, Any]:
        """Handle streaming response"""
        content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content += chunk.choices[0].delta.content

        return {"content": content, "stream": True}

    def _send_stream_update(self, session_id: str, chunk: str, full_content: str):
        """Send streaming update via WebSocket"""
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"session_{session_id}",
            {"type": "stream_update", "chunk": chunk, "full_content": full_content},
        )

    def generate_agent_response(
        self, agent_type: str, context: dict, user_input: str
    ) -> dict[str, Any]:
        """
        Generate response based on agent type and context

        Args:
            agent_type: Type of agent (orchestrator, vision, reasoning, etc.)
            context: Current context and conversation history
            user_input: User's input message

        Returns:
            Generated response
        """
        system_prompts = {
            "orchestrator": self._get_orchestrator_prompt(),
            "vision": self._get_vision_prompt(),
            "reasoning": self._get_reasoning_prompt(),
            "action": self._get_action_prompt(),
            "memory": self._get_memory_prompt(),
        }

        system_prompt = system_prompts.get(agent_type, self._get_default_prompt())

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context: {json.dumps(context)}\n\nUser Input: {user_input}",
            },
        ]

        return self.chat_completion(messages)

    def generate_response(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Compatibility helper for workflow orchestrators that expect a raw string response.
        """
        response = self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=(
                temperature if temperature is not None else self.default_temperature
            ),
            max_tokens=(
                max_tokens if max_tokens is not None else self.default_max_tokens
            ),
        )

        if response.get("error"):
            raise RuntimeError(response["error"])

        return response.get("content") or ""

    def _get_orchestrator_prompt(self) -> str:
        return """You are an Orchestrator Agent responsible for coordinating multiple specialized agents.
        Your role is to:
        1. Analyze user requests and break them down into tasks
        2. Assign tasks to appropriate specialized agents
        3. Coordinate the workflow between agents
        4. Synthesize results from multiple agents into coherent, helpful responses for the user
        5. Manage task priorities and dependencies
        
        If you are synthesizing final results for the user, directly answer their request using the information provided by the specialist agents. Do not just output task assignments if the user is asking for information (e.g. reading emails, getting data)."""

    def _get_vision_prompt(self) -> str:
        return """You are a Vision Agent specialized in processing visual information.
        Your capabilities include:
        1. Image analysis and description
        2. Object detection and recognition
        3. OCR (text extraction from images)
        4. Visual reasoning and interpretation
        5. Chart and diagram analysis
        
        Always provide detailed, accurate visual analysis with confidence scores."""

    def _get_reasoning_prompt(self) -> str:
        return """You are a Reasoning Agent specialized in logical analysis and problem-solving.
        Your capabilities include:
        1. Logical reasoning and inference
        2. Problem decomposition and analysis
        3. Decision making with evidence
        4. Pattern recognition and analysis
        5. Critical thinking and evaluation
        
        Always provide step-by-step reasoning with clear justifications."""

    def _get_action_prompt(self) -> str:
        return """You are an Action Agent responsible for executing tasks and interfacing with external systems.
        Your capabilities include:
        1. API calls and external integrations
        2. File operations and data manipulation
        3. Task execution and automation
        4. System interactions and commands
        5. Result processing and validation
        
        Always confirm actions before execution and provide detailed status updates."""

    def _get_memory_prompt(self) -> str:
        return """You are a Memory Agent responsible for managing context and knowledge retention.
        Your capabilities include:
        1. Context storage and retrieval
        2. Knowledge base management
        3. Conversation history maintenance
        4. Pattern storage and recall
        5. Importance scoring and prioritization
        
        Always maintain accurate context and provide relevant historical information."""

    def _get_default_prompt(self) -> str:
        return """You are an AI assistant that provides helpful, accurate, and contextual responses.
        Analyze the given context and user input to provide the most appropriate response."""

    def analyze_multimodal_input(
        self, content: str, file_type: str | None = None, file_path: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze multimodal input (text, image, audio, etc.)

        Args:
            content: Text content
            file_type: Type of attached file
            file_path: Path to the file

        Returns:
            Analysis results
        """
        analysis = {
            "text_analysis": None,
            "file_analysis": None,
            "combined_insights": None,
        }

        # Analyze text content
        if content:
            text_messages = [
                {
                    "role": "system",
                    "content": "Analyze the following text and provide insights, key points, and any actionable items.",
                },
                {"role": "user", "content": content},
            ]
            analysis["text_analysis"] = self.chat_completion(text_messages)

        # Analyze file if provided
        if file_path and file_type:
            file_analysis = self._analyze_file(file_path, file_type)
            analysis["file_analysis"] = file_analysis

        # Generate combined insights
        if analysis["text_analysis"] or analysis["file_analysis"]:
            combined_messages = [
                {
                    "role": "system",
                    "content": "Combine the following analyses and provide comprehensive insights.",
                },
                {
                    "role": "user",
                    "content": f"Text Analysis: {analysis['text_analysis']}\nFile Analysis: {analysis['file_analysis']}",
                },
            ]
            analysis["combined_insights"] = self.chat_completion(combined_messages)

        return analysis

    def _analyze_file(self, file_path: str, file_type: str) -> dict[str, Any]:
        """
        Analyze an uploaded file using Groq.
        - Text/CSV/JSON: read content and pass to Groq for analysis.
        - Images: describe via Groq vision prompt with base64 encoding.
        - Other binary files: summarise file metadata only.
        """
        import base64
        import os

        result: dict[str, Any] = {
            "file_type": file_type,
            "file_path": file_path,
            "analysis": None,
            "metadata": {},
        }

        if not os.path.exists(file_path):
            result["analysis"] = "File not found"
            return result

        file_size = os.path.getsize(file_path)
        result["metadata"]["file_size_bytes"] = file_size
        result["metadata"]["file_name"] = os.path.basename(file_path)

        try:
            # ── Text-based files ──────────────────────────────────────────
            text_extensions = {
                ".txt",
                ".md",
                ".csv",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".log",
                ".html",
                ".htm",
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".css",
                ".sh",
                ".env",
            }
            ext = os.path.splitext(file_path)[1].lower()

            if ext in text_extensions or file_type in ("text", "csv", "json", "xml"):
                with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read(8000)  # Limit to 8 KB to stay within token budget
                result["metadata"]["chars_read"] = len(content)

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a file analysis assistant. Analyse the provided file content "
                            "and return a concise summary covering: file purpose, key data points, "
                            "structure, and any notable observations."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f'File name: {result["metadata"]["file_name"]}\n\nContent:\n{content}',
                    },
                ]
                resp = self.chat_completion(messages)
                result["analysis"] = resp.get("content", "Analysis failed")

            # ── Image files ───────────────────────────────────────────────
            elif (
                ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
                or file_type == "image"
            ):
                if file_size <= 4 * 1024 * 1024:  # Only encode if ≤ 4 MB
                    with open(file_path, "rb") as fh:
                        b64 = base64.b64encode(fh.read()).decode()
                    mime = {
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".png": "image/png",
                        ".gif": "image/gif",
                        ".bmp": "image/bmp",
                        ".webp": "image/webp",
                    }.get(ext, "image/jpeg")

                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are a Vision Agent. Describe this image in detail: "
                                "objects, colours, text, layout, and any noteworthy features."
                            ),
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                                }
                            ],
                        },
                    ]
                    # Use llama-3.2-vision model for image analysis
                    resp = self.chat_completion(
                        messages, model="llama-3.2-11b-vision-preview"
                    )
                    result["analysis"] = resp.get("content", "Image analysis failed")
                else:
                    result["analysis"] = (
                        f"Image file too large for inline analysis ({file_size} bytes)"
                    )

            # ── Fallback: metadata only ───────────────────────────────────
            else:
                result["analysis"] = (
                    f'Binary file of type "{file_type}" ({file_size} bytes). '
                    "Content analysis is not supported for this format."
                )

        except Exception as e:  # noqa: BLE001
            logger.error(f"File analysis error for {file_path}: {e}")
            result["analysis"] = f"Analysis error: {e!s}"

        return result
