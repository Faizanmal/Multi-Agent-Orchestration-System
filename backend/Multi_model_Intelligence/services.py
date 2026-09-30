"""
Advanced Multi-Model Intelligence Service
Supports dynamic model switching and orchestration across Groq, OpenAI, and Anthropic
"""

import logging
import os
import time
from enum import Enum
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers"""
    NVIDIA = "nvidia"
    GROQ = "groq"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    

class TaskComplexity(Enum):
    """Task complexity levels for dynamic model selection"""
    SIMPLE = "simple"  # Quick queries, basic operations
    MODERATE = "moderate"  # Analysis, summaries
    COMPLEX = "complex"  # Deep reasoning, multi-step tasks
    CREATIVE = "creative"  # Content generation, creative writing


class ModelConfig:
    """Configuration for different models"""
    
    # Model capabilities and cost tiers
    MODELS = {  # noqa: RUF012
        # NVIDIA models - high-performance inference
        ModelProvider.NVIDIA: {
            "llama-3.1-70b-instruct": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "ultra_fast",
                "cost": "medium",
                "context_window": 32768,
                "strengths": ["speed", "reasoning", "general_purpose"]
            },
            "llama-3.1-8b-instruct": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "speed": "ultra_fast",
                "cost": "low",
                "context_window": 16384,
                "strengths": ["speed", "cost_effective"]
            },
            "mixtral-8x7b-instruct": {
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "fast",
                "cost": "medium",
                "context_window": 32768,
                "strengths": ["multilingual", "reasoning"]
            },
            "minimaxai/minimax-m2.7": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.CREATIVE],
                "speed": "fast",
                "cost": "medium",
                "context_window": 8192,
                "strengths": ["creative", "versatile", "long_context_generation"]
            }
        },
        # Groq models - ultra-fast inference
        ModelProvider.GROQ: {
            "llama-3.3-70b-versatile": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "ultra_fast",
                "cost": "low",
                "context_window": 32768,
                "strengths": ["speed", "reasoning", "general_purpose"]
            },
            "llama-3.3-70b-specdec": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "speed": "ultra_fast",
                "cost": "low",
                "context_window": 8192,
                "strengths": ["speed", "structured_output"]
            },
            "mixtral-8x7b-32768": {
                "complexity": [TaskComplexity.MODERATE],
                "speed": "fast",
                "cost": "low",
                "context_window": 32768,
                "strengths": ["multilingual", "reasoning"]
            }
        },
        # Google models - advanced multimodal
        ModelProvider.GOOGLE: {
            "gemini-1.5-pro": {
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.CREATIVE],
                "speed": "medium",
                "cost": "high",
                "context_window": 1048576,
                "strengths": ["multimodal", "long_context", "reasoning"]
            },
            "gemini-1.5-flash": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "fast",
                "cost": "medium",
                "context_window": 1048576,
                "strengths": ["speed", "multimodal", "long_context"]
            },
            "gemini-1.0-pro": {
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "medium",
                "cost": "medium",
                "context_window": 32768,
                "strengths": ["reasoning", "multimodal"]
            }
        },
        # OpenAI models - balanced quality
        ModelProvider.OPENAI: {
            "gpt-4": {
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.CREATIVE],
                "speed": "medium",
                "cost": "high",
                "context_window": 8192,
                "strengths": ["reasoning", "accuracy", "creative"]
            },
            "gpt-4-turbo": {
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.MODERATE],
                "speed": "fast",
                "cost": "medium",
                "context_window": 128000,
                "strengths": ["long_context", "reasoning", "vision"]
            },
            "gpt-3.5-turbo": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "speed": "fast",
                "cost": "low",
                "context_window": 16385,
                "strengths": ["speed", "cost_effective"]
            }
        },
        # Anthropic models - advanced reasoning
        ModelProvider.ANTHROPIC: {
            "claude-3-opus": {
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.CREATIVE],
                "speed": "medium",
                "cost": "high",
                "context_window": 200000,
                "strengths": ["reasoning", "long_context", "analysis"]
            },
            "claude-3-sonnet": {
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "speed": "fast",
                "cost": "medium",
                "context_window": 200000,
                "strengths": ["balanced", "long_context"]
            },
            "claude-3-haiku": {
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "speed": "ultra_fast",
                "cost": "low",
                "context_window": 200000,
                "strengths": ["speed", "cost_effective"]
            }
        }
    }


class MultiModelOrchestrator:
    """
    Orchestrates multiple AI models with intelligent routing and fallback
    """
    
    def __init__(self):
        self._init_clients()
        self.performance_history = []
        
    def _init_clients(self):
        """Initialize API clients for all providers"""
        # NVIDIA client (using OpenAI-compatible API)
        try:
            from openai import OpenAI
            self.nvidia_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=settings.NVIDIA_API_KEY or os.getenv('NVIDIA_API_KEY')
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"NVIDIA client initialization failed: {e}")
            self.nvidia_client = None
        
        # Groq client
        try:
            from groq import Groq
            self.groq_client = Groq(
                api_key=settings.GROQ_API_KEY or os.getenv('GROQ_API_KEY')
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Groq client initialization failed: {e}")
            self.groq_client = None
        
        # Google client
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY or os.getenv('GOOGLE_API_KEY'))
            self.google_client = genai
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Google client initialization failed: {e}")
            self.google_client = None
        
        # OpenAI client
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"OpenAI client initialization failed: {e}")
            self.openai_client = None
        
        # Anthropic client
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else os.getenv('ANTHROPIC_API_KEY')
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Anthropic client initialization failed: {e}")
            self.anthropic_client = None
    
    def analyze_task_complexity(self, messages: list[dict], context: dict | None = None) -> TaskComplexity:
        """
        Analyze task complexity to determine optimal model
        
        Args:
            messages: List of conversation messages
            context: Additional context about the task
            
        Returns:
            TaskComplexity enum value
        """
        # Get last user message
        user_messages = [m for m in messages if m.get('role') == 'user']
        if not user_messages:
            return TaskComplexity.SIMPLE
        
        last_message = user_messages[-1].get('content', '')
        message_length = len(last_message)
        
        # Analyze message characteristics
        complexity_indicators = {
            'creative_keywords': ['write', 'create', 'generate', 'story', 'poem', 'creative'],
            'complex_keywords': ['analyze', 'explain', 'compare', 'evaluate', 'why', 'how'],
            'simple_keywords': ['what', 'when', 'where', 'list', 'show']
        }
        
        # Check for creative task
        if any(kw in last_message.lower() for kw in complexity_indicators['creative_keywords']):
            return TaskComplexity.CREATIVE
        
        # Check for complex reasoning
        if any(kw in last_message.lower() for kw in complexity_indicators['complex_keywords']):
            if message_length > 200 or len(messages) > 5:
                return TaskComplexity.COMPLEX
            return TaskComplexity.MODERATE
        
        # Check message length and conversation depth
        if message_length > 500 or len(messages) > 10:
            return TaskComplexity.COMPLEX
        elif message_length > 100 or len(messages) > 3:
            return TaskComplexity.MODERATE
        
        return TaskComplexity.SIMPLE
    
    def select_optimal_model(
        self, 
        complexity: TaskComplexity, 
        priority: str = "balanced",
        constraints: dict | None = None
    ) -> tuple:
        """
        Select optimal model based on task complexity and priorities
        
        Args:
            complexity: Task complexity level
            priority: "speed", "cost", "quality", or "balanced"
            constraints: Additional constraints (max_cost, required_speed, etc.)
            
        Returns:
            Tuple of (provider, model_name)
        """
        constraints = constraints or {}
        candidates = []
        
        # Collect all models matching complexity
        for provider, models in ModelConfig.MODELS.items():
            for model_name, config in models.items():
                if complexity in config['complexity']:
                    score = self._score_model(config, priority, constraints)
                    # Add provider priority bonus: NVIDIA > GROQ > GOOGLE > ANTHROPIC > OPENAI
                    provider_priority = {
                        ModelProvider.NVIDIA: 1.0,
                        ModelProvider.GROQ: 0.8,
                        ModelProvider.GOOGLE: 0.6,
                        ModelProvider.ANTHROPIC: 0.5,
                        ModelProvider.OPENAI: 0.4
                    }
                    score += provider_priority.get(provider, 0.0)
                    candidates.append((score, provider, model_name, config))
        
        # Sort by score
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        if not candidates:
            # Fallback to default Groq model
            logger.warning(f"No model found for complexity {complexity}, using default")
            return ModelProvider.GROQ, "llama-3.3-70b-versatile"
        
        _, provider, model_name, _ = candidates[0]
        logger.info(f"Selected {provider.value}/{model_name} for {complexity.value} task with {priority} priority")
        
        return provider, model_name
    
    def _score_model(self, config: dict, priority: str, constraints: dict) -> float:
        """Score a model based on priority and constraints"""
        score = 0.0
        
        # Speed scoring
        speed_scores = {"ultra_fast": 1.0, "fast": 0.7, "medium": 0.4, "slow": 0.1}
        speed_score = speed_scores.get(config['speed'], 0.5)
        
        # Cost scoring (inverted - lower cost = higher score)
        cost_scores = {"low": 1.0, "medium": 0.6, "high": 0.3}
        cost_score = cost_scores.get(config['cost'], 0.5)
        
        # Apply priority weights
        if priority == "speed":
            score = speed_score * 0.7 + cost_score * 0.3
        elif priority == "cost":
            score = cost_score * 0.7 + speed_score * 0.3
        elif priority == "quality":
            # Quality inversely correlates with speed (generally)
            score = (1 - speed_score) * 0.6 + cost_score * 0.4
        else:  # balanced
            score = (speed_score + cost_score) * 0.5
        
        # Apply constraints
        if constraints.get('max_cost') == 'low' and config['cost'] != 'low':
            score *= 0.5
        if constraints.get('min_speed') == 'fast' and config['speed'] not in ['fast', 'ultra_fast']:
            score *= 0.5
        
        return score
    
    def _get_provider_models_sorted(self, provider: ModelProvider, complexity: TaskComplexity, priority: str = "balanced", constraints: dict | None = None) -> list[str]:
        """Get all models for a provider sorted by preference for the given complexity"""
        constraints = constraints or {}
        candidates = []
        
        if provider not in ModelConfig.MODELS:
            return []
        
        # Collect all models for this provider that match complexity
        for model_name, config in ModelConfig.MODELS[provider].items():
            if complexity in config['complexity']:
                score = self._score_model(config, priority, constraints)
                candidates.append((score, model_name))
        
        # Sort by score (highest first)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        return [model_name for _, model_name in candidates]
    
    def _try_provider_models(self, provider: ModelProvider, messages: list[dict], complexity: TaskComplexity, stream: bool, priority: str = "balanced", **kwargs) -> dict:
        """Try all available models for a provider in order of preference"""
        available_models = self._get_provider_models_sorted(provider, complexity, priority, kwargs.get('constraints'))
        
        if not available_models:
            raise Exception(f"No suitable models found for {provider.value} with complexity {complexity.value}")  # noqa: TRY002
        
        # Try each model for this provider
        for model in available_models:
            try:
                logger.info(f"Trying {provider.value}/{model}")
                
                if provider == ModelProvider.NVIDIA:
                    result = self._nvidia_completion(messages, model, stream, **kwargs)
                elif provider == ModelProvider.GROQ:
                    result = self._groq_completion(messages, model, stream, **kwargs)
                elif provider == ModelProvider.GOOGLE:
                    result = self._google_completion(messages, model, stream, **kwargs)
                elif provider == ModelProvider.ANTHROPIC:
                    result = self._anthropic_completion(messages, model, stream, **kwargs)
                elif provider == ModelProvider.OPENAI:
                    result = self._openai_completion(messages, model, stream, **kwargs)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
                
                logger.info(f"Successfully executed {provider.value}/{model}")
                return result
                
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Model {provider.value}/{model} failed: {e}")
                continue
        
        raise Exception(f"All models failed for provider {provider.value}")  # noqa: TRY002
    
    def chat_completion(
        self,
        messages: list[dict],
        complexity: TaskComplexity | None = None,
        provider: ModelProvider | None = None,
        model: str | None = None,
        priority: str = "balanced",
        stream: bool = False,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute chat completion with automatic model selection
        
        Args:
            messages: Conversation messages
            complexity: Task complexity (auto-detected if None)
            provider: Force specific provider (optional)
            model: Force specific model (optional)
            priority: Selection priority
            stream: Enable streaming
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary with content and metadata
        """
        start_time = time.time()
        
        # Ensure markdown formatting system prompt
        has_system_message = any(msg.get('role') == 'system' for msg in messages)
        if not has_system_message:
            messages.insert(0, {
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

Please format ALL your responses this way. Never use plain text paragraphs."""
            })
        
        # Auto-detect complexity if not provided
        if complexity is None:
            complexity = self.analyze_task_complexity(messages, kwargs.get('context'))
        
        # Select provider if not forced
        if provider is None:
            provider, _ = self.select_optimal_model(complexity, priority, kwargs.get('constraints'))
        
        # Execute with selected provider, trying all its models
        try:
            result = self._try_provider_models(provider, messages, complexity, stream, priority, **kwargs)
            
            # Track performance
            duration = time.time() - start_time
            self._track_performance(provider, result.get('model', 'unknown'), complexity, duration, result)
            
            # Add metadata
            result['metadata'] = {
                'provider': provider.value,
                'model': result.get('model', 'unknown'),
                'complexity': complexity.value,
                'duration': duration,
                'priority': priority
            }
            
            return result
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Primary provider {provider.value} failed: {e}")
            # Attempt comprehensive fallback
            return self._execute_fallback(messages, provider, complexity, stream, **kwargs)
    
    def _groq_completion(self, messages: list[dict], model: str, stream: bool, **kwargs) -> dict:
        """Execute Groq completion"""
        if not self.groq_client:
            raise Exception("Groq client not initialized")  # noqa: TRY002
        
        response = self.groq_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2048),
            stream=stream
        )
        
        if stream:
            return {'stream': response, 'provider': 'groq', 'model': model}
        
        return {
            'content': response.choices[0].message.content,
            'model': model,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'finish_reason': response.choices[0].finish_reason
        }
    
    def _nvidia_completion(self, messages: list[dict], model: str, stream: bool, **kwargs) -> dict:
        """Execute NVIDIA completion"""
        if not self.nvidia_client:
            raise Exception("NVIDIA client not initialized")  # noqa: TRY002
        
        response = self.nvidia_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2048),
            stream=stream
        )
        
        if stream:
            return {'stream': response, 'provider': 'nvidia', 'model': model}
        
        return {
            'content': response.choices[0].message.content,
            'model': model,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'finish_reason': response.choices[0].finish_reason
        }
    
    def _google_completion(self, messages: list[dict], model: str, stream: bool, **kwargs) -> dict:
        """Execute Google Gemini completion"""
        if not self.google_client:
            raise Exception("Google client not initialized")  # noqa: TRY002
        
        # Convert messages to Gemini format
        gemini_messages = []
        system_instruction = None
        
        for msg in messages:
            if msg['role'] == 'system':
                system_instruction = msg['content']
            else:
                role = 'user' if msg['role'] == 'user' else 'model'
                gemini_messages.append({
                    'role': role,
                    'parts': [{'text': msg['content']}]
                })
        
        # Create model with system instruction if present
        model_instance = self.google_client.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction
        )
        
        # Configure generation
        generation_config = self.google_client.types.GenerationConfig(
            temperature=kwargs.get('temperature', 0.7),
            max_output_tokens=kwargs.get('max_tokens', 2048),
        )
        
        response = model_instance.generate_content(
            gemini_messages,
            generation_config=generation_config,
            stream=stream
        )
        
        if stream:
            return {'stream': response, 'provider': 'google', 'model': model}
        
        return {
            'content': response.text,
            'model': model,
            'usage': {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'completion_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            },
            'finish_reason': 'stop'  # Gemini doesn't provide detailed finish reasons
        }
    
    def _openai_completion(self, messages: list[dict], model: str, stream: bool, **kwargs) -> dict:
        """Execute OpenAI completion"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")  # noqa: TRY002
        
        response = self.openai_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 2048),
            stream=stream
        )
        
        if stream:
            return {'stream': response, 'provider': 'openai', 'model': model}
        
        return {
            'content': response.choices[0].message.content,
            'model': model,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'finish_reason': response.choices[0].finish_reason
        }
    
    def _anthropic_completion(self, messages: list[dict], model: str, stream: bool, **kwargs) -> dict:
        """Execute Anthropic completion"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")  # noqa: TRY002
        
        # Convert messages format for Anthropic
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                anthropic_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=kwargs.get('max_tokens', 2048),
            temperature=kwargs.get('temperature', 0.7),
            system=system_message,
            messages=anthropic_messages,
            stream=stream
        )
        
        if stream:
            return {'stream': response, 'provider': 'anthropic', 'model': model}
        
        return {
            'content': response.content[0].text,
            'model': model,
            'usage': {
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            },
            'finish_reason': response.stop_reason
        }
    
    def _execute_fallback(
        self, 
        messages: list[dict], 
        failed_provider: ModelProvider,
        complexity: TaskComplexity,
        stream: bool,
        **kwargs
    ) -> dict:
        """Execute comprehensive fallback strategy when primary model fails"""
        logger.info(f"Executing comprehensive fallback after {failed_provider.value} failure")
        
        # Try alternative providers in order of priority: NVIDIA > GROQ > GOOGLE > ANTHROPIC > OPENAI
        fallback_providers = [
            ModelProvider.NVIDIA,
            ModelProvider.GROQ,
            ModelProvider.GOOGLE,
            ModelProvider.ANTHROPIC,
            ModelProvider.OPENAI
        ]
        
        # Remove failed provider
        fallback_providers = [p for p in fallback_providers if p != failed_provider]
        
        # Try each provider in order
        for provider in fallback_providers:
            logger.info(f"Trying fallback provider: {provider.value}")
            
            # Get all available models for this provider, sorted by preference
            available_models = self._get_provider_models_sorted(provider, complexity, "balanced", kwargs.get('constraints'))
            
            if not available_models:
                logger.warning(f"No suitable models found for {provider.value} with complexity {complexity.value}")
                continue
            
            # Try each model for this provider
            for model in available_models:
                try:
                    logger.info(f"Trying {provider.value}/{model}")
                    
                    if provider == ModelProvider.NVIDIA:
                        result = self._nvidia_completion(messages, model, stream, **kwargs)
                    elif provider == ModelProvider.GROQ:
                        result = self._groq_completion(messages, model, stream, **kwargs)
                    elif provider == ModelProvider.GOOGLE:
                        result = self._google_completion(messages, model, stream, **kwargs)
                    elif provider == ModelProvider.ANTHROPIC:
                        result = self._anthropic_completion(messages, model, stream, **kwargs)
                    elif provider == ModelProvider.OPENAI:
                        result = self._openai_completion(messages, model, stream, **kwargs)
                    else:
                        logger.warning(f"Unknown provider: {provider}")
                        continue
                    
                    logger.info(f"Successfully fell back to {provider.value}/{model}")
                    return result
                    
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Model {provider.value}/{model} failed: {e}")
                    continue
            
            logger.warning(f"All models failed for provider {provider.value}")
        
        logger.error("All fallback attempts failed")
        return {
            'error': 'All providers and models failed',
            'content': None
        }
    
    def _track_performance(
        self, 
        provider: ModelProvider, 
        model: str, 
        complexity: TaskComplexity,
        duration: float,
        result: dict
    ):
        """Track model performance for optimization"""
        self.performance_history.append({
            'timestamp': time.time(),
            'provider': provider.value,
            'model': model,
            'complexity': complexity.value,
            'duration': duration,
            'success': 'error' not in result,
            'tokens': result.get('usage', {}).get('total_tokens', 0)
        })
        
        # Keep last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def get_performance_insights(self) -> dict[str, Any]:
        """Get performance insights and recommendations"""
        if not self.performance_history:
            return {'message': 'No performance data available'}
        
        # Calculate statistics
        total_requests = len(self.performance_history)
        success_rate = sum(1 for r in self.performance_history if r['success']) / total_requests
        avg_duration = sum(r['duration'] for r in self.performance_history) / total_requests
        
        # Provider statistics
        provider_stats = {}
        for record in self.performance_history:
            provider = record['provider']
            if provider not in provider_stats:
                provider_stats[provider] = {'requests': 0, 'avg_duration': 0, 'success_rate': 0}
            provider_stats[provider]['requests'] += 1
        
        return {
            'total_requests': total_requests,
            'success_rate': success_rate,
            'avg_duration': avg_duration,
            'provider_stats': provider_stats,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list[str]:
        """Generate optimization recommendations based on performance history"""
        recommendations = []
        
        if not self.performance_history:
            return recommendations
        
        # Analyze recent performance
        recent = self.performance_history[-100:]
        
        # Check for high failure rate
        failure_rate = sum(1 for r in recent if not r['success']) / len(recent)
        if failure_rate > 0.1:
            recommendations.append("High failure rate detected. Consider reviewing API keys and rate limits.")
        
        # Check for slow responses
        avg_duration = sum(r['duration'] for r in recent) / len(recent)
        if avg_duration > 5.0:
            recommendations.append("Slow response times detected. Consider using faster models for simple tasks.")
        
        return recommendations


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> MultiModelOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MultiModelOrchestrator()
    return _orchestrator_instance
