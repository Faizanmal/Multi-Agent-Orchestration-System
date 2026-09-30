"""Default AI model catalog and seeding helpers."""

from .models import AIModelConfig

DEFAULT_AI_MODELS = [
    {
        'name': 'Llama 3.3 70B (Groq)',
        'model_type': 'text',
        'provider': 'groq',
        'model_id': 'llama-3.3-70b-versatile',
        'capabilities': ['reasoning', 'coding', 'fast'],
        'is_default': True,
    },
    {
        'name': 'GPT-4o',
        'model_type': 'multimodal',
        'provider': 'openai',
        'model_id': 'gpt-4o',
        'capabilities': ['reasoning', 'coding', 'vision', 'analysis'],
    },
    {
        'name': 'Claude 3.5 Sonnet',
        'model_type': 'text',
        'provider': 'anthropic',
        'model_id': 'claude-3-5-sonnet-latest',
        'capabilities': ['reasoning', 'writing', 'analysis', 'coding'],
    },
    {
        'name': 'Gemini 1.5 Pro',
        'model_type': 'multimodal',
        'provider': 'google',
        'model_id': 'gemini-1.5-pro',
        'capabilities': ['vision', 'reasoning', 'multimodal'],
    },
    {
        'name': 'Whisper Large',
        'model_type': 'audio',
        'provider': 'openai',
        'model_id': 'whisper-1',
        'capabilities': ['transcription', 'translation'],
    },
]


def seed_default_ai_models(user=None) -> list[str]:
    created: list[str] = []
    for item in DEFAULT_AI_MODELS:
        obj, was_created = AIModelConfig.objects.get_or_create(
            provider=item['provider'],
            model_id=item['model_id'],
            defaults={
                'name': item['name'],
                'model_type': item['model_type'],
                'capabilities': item['capabilities'],
                'is_default': item.get('is_default', False),
                'is_active': True,
                'created_by': user,
            },
        )
        if was_created:
            created.append(str(obj.id))
    return created


PROVIDER_MODEL_OPTIONS = {
    'groq': [
        ('llama-3.3-70b-versatile', 'Llama 3.3 70B'),
        ('llama-3.1-8b-instant', 'Llama 3.1 8B Instant'),
        ('mixtral-8x7b-32768', 'Mixtral 8x7B'),
    ],
    'openai': [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
        ('whisper-1', 'Whisper'),
    ],
    'anthropic': [
        ('claude-3-5-sonnet-latest', 'Claude 3.5 Sonnet'),
        ('claude-3-opus-latest', 'Claude 3 Opus'),
        ('claude-3-haiku-latest', 'Claude 3 Haiku'),
    ],
    'google': [
        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
    ],
    'mistral': [
        ('mistral-large-latest', 'Mistral Large'),
        ('mistral-small-latest', 'Mistral Small'),
    ],
    'custom': [
        ('custom', 'Custom model ID'),
    ],
}
