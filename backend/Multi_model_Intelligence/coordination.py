"""
Model-to-model coordination.

Registered AIModelConfig entries collaborate via:
  - route        : pick best model (+ failover across others)
  - collaborative: multi-round propose → critique → synthesize
  - debate       : independent answers → peer critique → judge
  - pipeline     : sequential stages, each model refining the last output
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from django.db.models import Q

from .models import AIModelConfig, ModelCoordinationRun
from .services import ModelProvider, get_orchestrator

logger = logging.getLogger(__name__)


class ModelCoordinationService:
    """Coordinate multiple registered AI models on a shared task."""

    MODES = ("route", "collaborative", "debate", "pipeline")

    def resolve_models(
        self,
        model_ids: list[str] | None = None,
        user=None,
        require_active: bool = True,
    ) -> list[AIModelConfig]:
        qs = AIModelConfig.objects.all()
        if require_active:
            qs = qs.filter(is_active=True)
        if user and getattr(user, "is_authenticated", False):
            qs = qs.filter(Q(created_by=user) | Q(created_by__isnull=True))
        if model_ids:
            qs = qs.filter(id__in=model_ids)
            # Preserve requested order
            by_id = {str(m.id): m for m in qs}
            ordered = [by_id[i] for i in model_ids if i in by_id]
            return ordered
        return list(qs.order_by("-is_default", "-created_at")[:8])

    def run(
        self,
        mode: str,
        prompt: str,
        model_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
        user=None,
    ) -> dict[str, Any]:
        mode = (mode or "route").lower()
        if mode not in self.MODES:
            raise ValueError(
                f"Unknown mode '{mode}'. Use one of: {', '.join(self.MODES)}"
            )

        options = options or {}
        models = self.resolve_models(model_ids, user=user)
        if not models:
            raise ValueError(
                "No active AI models available. Add models on the Intelligence page first."
            )

        start = time.monotonic()
        run = ModelCoordinationRun.objects.create(
            user=user if user and getattr(user, "is_authenticated", False) else None,
            mode=mode,
            prompt=prompt[:8000],
            model_ids=[str(m.id) for m in models],
            status="running",
            options=options,
        )

        try:
            if mode == "route":
                result = self._run_route(models, prompt, options)
            elif mode == "collaborative":
                result = self._run_collaborative(models, prompt, options)
            elif mode == "debate":
                result = self._run_debate(models, prompt, options)
            else:
                result = self._run_pipeline(models, prompt, options)

            duration_ms = int((time.monotonic() - start) * 1000)
            run.status = "completed"
            run.result = result
            run.final_answer = (result.get("final_answer") or "")[:20000]
            run.duration_ms = duration_ms
            run.save(update_fields=["status", "result", "final_answer", "duration_ms"])

            return {
                "run_id": str(run.id),
                "mode": mode,
                "models_used": [
                    {
                        "id": str(m.id),
                        "name": m.name,
                        "provider": m.provider,
                        "model_id": m.model_id,
                    }
                    for m in models
                ],
                "duration_ms": duration_ms,
                **result,
            }
        except Exception as exc:
            run.status = "failed"
            run.result = {"error": str(exc)}
            run.duration_ms = int((time.monotonic() - start) * 1000)
            run.save(update_fields=["status", "result", "duration_ms"])
            raise

    # ------------------------------------------------------------------
    # Invoke a single AIModelConfig
    # ------------------------------------------------------------------

    def invoke(
        self, config: AIModelConfig, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        orchestrator = get_orchestrator()
        provider_key = (config.provider or "").lower().strip()
        model_name = config.model_id

        provider_map = {
            "groq": ModelProvider.GROQ,
            "openai": ModelProvider.OPENAI,
            "anthropic": ModelProvider.ANTHROPIC,
            "google": ModelProvider.GOOGLE,
            "nvidia": ModelProvider.NVIDIA,
            "mistral": ModelProvider.OPENAI,  # OpenAI-compatible fallback when configured
        }
        provider = provider_map.get(provider_key)
        if not provider:
            raise ValueError(
                f"Unsupported provider for coordination: {config.provider}"
            )

        # Prefer direct forced model call
        try:
            if provider == ModelProvider.GROQ:
                result = orchestrator._groq_completion(
                    messages, model_name, False, **kwargs
                )
            elif provider == ModelProvider.OPENAI:
                result = orchestrator._openai_completion(
                    messages, model_name, False, **kwargs
                )
            elif provider == ModelProvider.ANTHROPIC:
                result = orchestrator._anthropic_completion(
                    messages, model_name, False, **kwargs
                )
            elif provider == ModelProvider.GOOGLE:
                result = orchestrator._google_completion(
                    messages, model_name, False, **kwargs
                )
            elif provider == ModelProvider.NVIDIA:
                result = orchestrator._nvidia_completion(
                    messages, model_name, False, **kwargs
                )
            else:
                raise ValueError(f"No completion handler for {provider}")

            content = result.get("content") or ""
            return {
                "status": "success",
                "content": content,
                "provider": provider_key,
                "model": model_name,
                "model_config_id": str(config.id),
                "model_name": config.name,
                "usage": result.get("usage") or {},
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Model %s/%s failed: %s", config.provider, model_name, exc)
            return {
                "status": "error",
                "content": "",
                "error": str(exc),
                "provider": provider_key,
                "model": model_name,
                "model_config_id": str(config.id),
                "model_name": config.name,
            }

    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------

    def _run_route(
        self, models: list[AIModelConfig], prompt: str, options: dict
    ) -> dict[str, Any]:
        """Pick best model by priority, failover through the rest."""
        priority = options.get("priority", "balanced")
        messages = [{"role": "user", "content": prompt}]

        # Prefer default / capability match, then remaining
        ordered = sorted(
            models,
            key=lambda m: (
                not m.is_default,
                m.provider != "groq" if priority == "speed" else 0,
            ),
        )
        tried = []
        for config in ordered:
            out = self.invoke(config, messages)
            tried.append(out)
            if out.get("status") == "success" and out.get("content"):
                return {
                    "final_answer": out["content"],
                    "selected": {
                        "id": str(config.id),
                        "name": config.name,
                        "provider": config.provider,
                        "model_id": config.model_id,
                    },
                    "fallbacks_tried": [t for t in tried if t is not out],
                    "per_model": {str(config.id): out},
                }

        return {
            "final_answer": "All selected models failed. Check API keys and provider configuration.",
            "selected": None,
            "fallbacks_tried": tried,
            "per_model": {t.get("model_config_id"): t for t in tried},
        }

    def _run_collaborative(
        self, models: list[AIModelConfig], prompt: str, options: dict
    ) -> dict[str, Any]:
        rounds = max(1, min(int(options.get("rounds", 2)), 4))
        messages_base = [{"role": "user", "content": prompt}]
        per_model: dict[str, Any] = {}
        round_logs: list[dict[str, Any]] = []

        # Round 1: independent proposals (parallel)
        proposals = {}
        with ThreadPoolExecutor(max_workers=min(4, len(models))) as pool:
            futures = {
                pool.submit(
                    self.invoke,
                    m,
                    [
                        {
                            "role": "system",
                            "content": "You are collaborating with other AI models. Give a clear, substantive answer.",
                        },
                        *messages_base,
                    ],
                ): m
                for m in models
            }
            for fut in as_completed(futures):
                m = futures[fut]
                out = fut.result()
                proposals[str(m.id)] = out
                per_model[str(m.id)] = out

        round_logs.append({"round": 1, "type": "propose", "outputs": proposals})

        draft = self._merge_texts(
            [
                p.get("content", "")
                for p in proposals.values()
                if p.get("status") == "success"
            ]
        )
        if not draft:
            return {
                "final_answer": "Collaboration failed: no model produced a proposal.",
                "rounds": round_logs,
                "per_model": per_model,
            }

        # Subsequent rounds: critique & refine
        for r in range(2, rounds + 1):
            refined_bits = []
            refine_outputs = {}
            critique_prompt = (
                f"Original task:\n{prompt}\n\n"
                f"Current shared draft:\n{draft}\n\n"
                "Improve the draft. Keep what is strong, fix gaps, and return the full improved answer."
            )
            for m in models:
                out = self.invoke(
                    m,
                    [
                        {
                            "role": "system",
                            "content": "You refine a shared draft with peer AI models.",
                        },
                        {"role": "user", "content": critique_prompt},
                    ],
                )
                refine_outputs[str(m.id)] = out
                per_model[str(m.id)] = out
                if out.get("status") == "success" and out.get("content"):
                    refined_bits.append(out["content"])
            round_logs.append({"round": r, "type": "refine", "outputs": refine_outputs})
            if refined_bits:
                draft = self._merge_texts(refined_bits)

        # Final synthesis with first successful / default model
        synthesizer = next((m for m in models if m.is_default), models[0])
        synth = self.invoke(
            synthesizer,
            [
                {
                    "role": "system",
                    "content": "Synthesize the best final answer from collaborative model drafts. Be concise and complete.",
                },
                {
                    "role": "user",
                    "content": f"Task:\n{prompt}\n\nCollaborative draft:\n{draft}\n\nProduce the final answer.",
                },
            ],
        )
        final = synth.get("content") if synth.get("status") == "success" else draft
        return {
            "final_answer": final,
            "rounds": round_logs,
            "synthesizer": {
                "id": str(synthesizer.id),
                "name": synthesizer.name,
                "provider": synthesizer.provider,
            },
            "per_model": per_model,
        }

    def _run_debate(
        self, models: list[AIModelConfig], prompt: str, options: dict
    ) -> dict[str, Any]:
        rounds = max(1, min(int(options.get("rounds", 2)), 3))
        positions: dict[str, Any] = {}
        critiques: list[dict[str, Any]] = []

        # Opening positions
        with ThreadPoolExecutor(max_workers=min(4, len(models))) as pool:
            futures = {
                pool.submit(
                    self.invoke,
                    m,
                    [
                        {
                            "role": "system",
                            "content": (
                                "You are debating with other AI models. State your best answer clearly "
                                "and list 2–3 key reasons."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                ): m
                for m in models
            }
            for fut in as_completed(futures):
                m = futures[fut]
                positions[str(m.id)] = {
                    **fut.result(),
                    "name": m.name,
                    "provider": m.provider,
                }

        # Critique rounds
        for r in range(1, rounds):
            round_critiques = {}
            summary = "\n\n".join(
                f"### {positions[mid].get('name')} ({positions[mid].get('provider')})\n{positions[mid].get('content', '')}"
                for mid in positions
            )
            for m in models:
                out = self.invoke(
                    m,
                    [
                        {
                            "role": "system",
                            "content": "Critique peer answers briefly, then restate your improved position.",
                        },
                        {
                            "role": "user",
                            "content": f"Task:\n{prompt}\n\nPeer positions:\n{summary}\n\nYour improved answer:",
                        },
                    ],
                )
                if out.get("status") == "success" and out.get("content"):
                    positions[str(m.id)] = {
                        **out,
                        "name": m.name,
                        "provider": m.provider,
                    }
                round_critiques[str(m.id)] = out
            critiques.append({"round": r, "outputs": round_critiques})

        # Judge
        judge = None
        judge_id = options.get("judge_model_id")
        if judge_id:
            judge = next((m for m in models if str(m.id) == str(judge_id)), None)
        if not judge:
            judge = next((m for m in models if m.is_default), models[0])

        ballot = "\n\n".join(
            f"MODEL_ID={mid}\nNAME={positions[mid].get('name')}\nANSWER:\n{positions[mid].get('content', '')}"
            for mid in positions
        )
        judge_out = self.invoke(
            judge,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an impartial judge. Pick the best answer. "
                        'Reply with JSON: {"winner_model_id":"...","confidence":0-1,"reason":"...","final_answer":"..."}'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Task:\n{prompt}\n\nCandidates:\n{ballot}",
                },
            ],
        )

        verdict = self._parse_verdict(judge_out.get("content", ""), positions, judge)
        return {
            "final_answer": verdict.get("final_answer")
            or judge_out.get("content")
            or "",
            "positions": positions,
            "critiques": critiques,
            "verdict": verdict,
            "judge": {
                "id": str(judge.id),
                "name": judge.name,
                "provider": judge.provider,
            },
            "per_model": positions,
        }

    def _run_pipeline(
        self, models: list[AIModelConfig], prompt: str, options: dict
    ) -> dict[str, Any]:
        stages_opt = options.get("stages")
        if stages_opt and isinstance(stages_opt, list) and stages_opt:
            stage_models = []
            for stage in stages_opt:
                mid = str(stage.get("model_id", ""))
                match = next((m for m in models if str(m.id) == mid), None)
                if match:
                    stage_models.append((match, stage.get("role") or "process"))
            if not stage_models:
                stage_models = [(m, "process") for m in models]
        else:
            default_roles = ["outline", "expand", "critique", "finalize"]
            stage_models = [
                (m, default_roles[i] if i < len(default_roles) else "process")
                for i, m in enumerate(models)
            ]

        stages = []
        current = prompt
        for config, role in stage_models:
            role_prompt = {
                "outline": "Create a structured outline for the task.",
                "expand": "Expand the previous stage into a full draft.",
                "critique": "Critique and improve the draft; return the improved full text.",
                "finalize": "Produce the polished final answer.",
                "process": "Process the input and return an improved result.",
            }.get(role, f'Perform the "{role}" stage.')

            out = self.invoke(
                config,
                [
                    {
                        "role": "system",
                        "content": f'You are stage "{role}" in a multi-model pipeline. {role_prompt}',
                    },
                    {
                        "role": "user",
                        "content": f"Original task:\n{prompt}\n\nPrevious stage output:\n{current}",
                    },
                ],
            )
            stages.append(
                {
                    "role": role,
                    "model_id": str(config.id),
                    "name": config.name,
                    "provider": config.provider,
                    "output": out,
                }
            )
            if out.get("status") == "success" and out.get("content"):
                current = out["content"]

        return {
            "final_answer": current,
            "stages": stages,
            "per_model": {s["model_id"]: s["output"] for s in stages},
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_texts(texts: list[str]) -> str:
        texts = [t.strip() for t in texts if t and t.strip()]
        if not texts:
            return ""
        if len(texts) == 1:
            return texts[0]
        # Prefer longest substantive answer as draft base
        return max(texts, key=len)

    @staticmethod
    def _parse_verdict(
        raw: str, positions: dict[str, Any], judge: AIModelConfig
    ) -> dict[str, Any]:
        import json
        import re

        winner = None
        confidence = 0.5
        reason = ""
        final_answer = raw

        try:
            match = re.search(r"\{[\s\S]*\}", raw or "")
            if match:
                data = json.loads(match.group(0))
                winner = data.get("winner_model_id")
                confidence = float(data.get("confidence", 0.5))
                reason = data.get("reason", "")
                final_answer = (
                    data.get("final_answer")
                    or positions.get(str(winner), {}).get("content")
                    or raw
                )
        except Exception:  # noqa: BLE001
            # Fallback: pick longest successful position
            best = max(
                positions.values(),
                key=lambda p: (
                    len(p.get("content") or "") if p.get("status") == "success" else 0
                ),
                default={},
            )
            winner = best.get("model_config_id")
            final_answer = best.get("content") or raw
            reason = "Fallback selection by answer length"

        return {
            "winner_model_id": winner,
            "confidence": confidence,
            "reason": reason,
            "final_answer": final_answer,
            "judge_model_id": str(judge.id),
        }


_coordination_service: ModelCoordinationService | None = None


def get_coordination_service() -> ModelCoordinationService:
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = ModelCoordinationService()
    return _coordination_service
