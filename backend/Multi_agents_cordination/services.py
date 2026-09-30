"""
Multi-Agent Coordination Service
=================================
Orchestrates multiple agents using different coordination strategies:
- sequential   : agents run one after another, each receiving prior output
- parallel     : all agents run concurrently, results merged
- hierarchical : orchestrator delegates to specialists via sub-tasks
- collaborative: agents iteratively refine a shared answer (rounds of critique)
- competitive  : agents produce independent answers; best one is selected

Uses AgentCoordinationSession, AgentInteraction, and CoordinationMetric
models to log every step for audit and analytics.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class CoordinationService:
    """
    Coordinate a group of agents to solve a task together.
    All activity is recorded via AgentCoordinationSession / AgentInteraction.
    """

    def __init__(self):
        pass  # stateless — all context is passed per call

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def execute_strategy(
        self,
        session,  # agents.models.Session
        strategy: str,  # CoordinationStrategy value
        agents: list,  # list of agents.models.Agent
        task: str,  # plain-text task description
        context: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the chosen coordination strategy for the given agents and task.

        Returns a dict with keys:
          strategy, task, agents_involved, results, final_answer,
          coordination_session_id, duration_ms
        """
        context = context or {}
        start = time.monotonic()

        # Create an audit session record
        coord_session = self._create_coord_session(session, strategy, task, context)
        return self._execute(
            coord_session, strategy, agents, task, context, start, chat_session=session
        )

    def execute_on_coordination_session(
        self,
        coord_session,  # Multi_agents_cordination.AgentCoordinationSession
        strategy: str,
        agents: list,
        task: str,
        context: dict | None = None,
    ) -> dict[str, Any]:
        """Run a strategy on an existing AgentCoordinationSession (HTTP API path)."""
        context = {**(coord_session.context or {}), **(context or {})}
        start = time.monotonic()
        if strategy:
            coord_session.strategy = strategy
            coord_session.save(update_fields=["strategy"])
        return self._execute(
            coord_session,
            strategy or coord_session.strategy,
            agents,
            task,
            context,
            start,
        )

    def _execute(
        self, coord_session, strategy, agents, task, context, start, chat_session=None
    ):
        try:
            if strategy == "sequential":
                results, final_answer = self._run_sequential(
                    coord_session, agents, task, context
                )
            elif strategy == "parallel":
                results, final_answer = self._run_parallel(
                    coord_session, agents, task, context
                )
            elif strategy == "hierarchical":
                results, final_answer = self._run_hierarchical(
                    coord_session, agents, task, context, chat_session
                )
            elif strategy == "collaborative":
                results, final_answer = self._run_collaborative(
                    coord_session, agents, task, context
                )
            elif strategy == "competitive":
                results, final_answer = self._run_competitive(
                    coord_session, agents, task, context
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            self._close_coord_session(coord_session, success=True)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Coordination strategy '{strategy}' failed: {e}")
            self._close_coord_session(coord_session, success=False)
            results = {}
            final_answer = f"Coordination failed: {e}"

        duration_ms = int((time.monotonic() - start) * 1000)
        self._record_metric(coord_session, "duration_ms", float(duration_ms))
        self._record_metric(coord_session, "agents_count", float(len(agents)))

        # Persist final answer into session context for the UI
        try:
            coord_session.context = {
                **(coord_session.context or {}),
                "task": task[:500],
                "final_answer": (
                    final_answer[:5000]
                    if isinstance(final_answer, str)
                    else str(final_answer)[:5000]
                ),
                "results_keys": (
                    list(results.keys()) if isinstance(results, dict) else []
                ),
            }
            coord_session.save(update_fields=["context", "updated_at"])
        except Exception:  # noqa: BLE001, S110
            pass

        return {
            "strategy": strategy,
            "task": task[:200],
            "agents_involved": [a.name for a in agents],
            "results": results,
            "final_answer": final_answer,
            "coordination_session_id": str(coord_session.id),
            "duration_ms": duration_ms,
            "status": (
                "completed"
                if "failed" not in str(final_answer).lower()[:40]
                else "failed"
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Strategy implementations
    # ─────────────────────────────────────────────────────────────────────────

    def _run_sequential(
        self,
        coord_session,
        agents: list,
        task: str,
        context: dict,
    ):
        """Each agent processes the task in order; outputs chain into the next."""
        from agents.services.groq_service import GroqService

        groq = GroqService()

        results: dict[str, Any] = {}
        accumulated_context = task

        for agent in agents:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are {agent.name} ({agent.type} agent). "
                        f"You are part of a sequential multi-agent pipeline. "
                        f"Build on the prior output below and add your specialized perspective."
                    ),
                },
                {"role": "user", "content": accumulated_context},
            ]
            response = groq.chat_completion(messages)
            agent_output = response.get("content", "")

            results[agent.name] = agent_output
            self._log_interaction(
                coord_session,
                agent,
                None,
                "sequential_step",
                {
                    "input": accumulated_context[:300],
                    "output": agent_output[:300],
                },
            )

            # Pass this agent's output as input to the next
            accumulated_context = (
                f"Prior agent ({agent.name}) output:\n{agent_output}\n\n"
                f"Original task: {task}"
            )

        return results, accumulated_context

    def _run_parallel(
        self,
        coord_session,
        agents: list,
        task: str,
        context: dict,
    ):
        """All agents process the task simultaneously; results are merged."""
        from agents.services.groq_service import GroqService

        groq = GroqService()

        def run_agent(agent):
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are {agent.name} ({agent.type} agent). "
                        f"Answer this task from your specialist perspective."
                    ),
                },
                {"role": "user", "content": task},
            ]
            response = groq.chat_completion(messages)
            return agent, response.get("content", "")

        results: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
            futures = {executor.submit(run_agent, a): a for a in agents}
            for future in as_completed(futures):
                try:
                    agent, output = future.result()
                    results[agent.name] = output
                    self._log_interaction(
                        coord_session,
                        agent,
                        None,
                        "parallel_result",
                        {
                            "output": output[:300],
                        },
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Parallel agent failed: {e}")

        # Merge: concatenate all outputs with headers
        merged = "\n\n".join(
            f"=== {name} ===\n{output}" for name, output in results.items()
        )
        return results, merged

    def _run_hierarchical(
        self,
        coord_session,
        agents: list,
        task: str,
        context: dict,
        session,
    ):
        """
        Orchestrator agent delegates sub-tasks to specialists, then synthesises.
        """
        from agents.services.groq_service import GroqService

        groq = GroqService()

        orchestrator = next((a for a in agents if a.type == "orchestrator"), agents[0])
        specialists = [a for a in agents if a != orchestrator]

        # Step 1: Orchestrator creates a delegation plan
        plan_messages = [
            {
                "role": "system",
                "content": (
                    f"You are {orchestrator.name}, the lead orchestrator. "
                    "Create a JSON delegation plan: a list of objects each with "
                    "{'agent_name': str, 'sub_task': str}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n"
                    f"Available specialists: {[a.name + '(' + a.type + ')' for a in specialists]}"
                ),
            },
        ]
        plan_response = groq.chat_completion(plan_messages)
        plan_text = plan_response.get("content", "[]")

        delegation_plan = []
        try:
            import re

            match = re.search(r"\[.*\]", plan_text, re.DOTALL)
            delegation_plan = json.loads(match.group()) if match else []
        except Exception:  # noqa: BLE001
            delegation_plan = [
                {"agent_name": a.name, "sub_task": task} for a in specialists
            ]

        # Step 2: Execute each delegation
        results: dict[str, Any] = {}
        specialist_map = {a.name: a for a in specialists}

        for item in delegation_plan:
            agent_name = item.get("agent_name")
            sub_task = item.get("sub_task", task)
            agent = specialist_map.get(agent_name)
            if agent is None:
                continue

            messages = [
                {
                    "role": "system",
                    "content": f"You are {agent.name} ({agent.type} agent). Execute this sub-task precisely.",
                },
                {"role": "user", "content": sub_task},
            ]
            response = groq.chat_completion(messages)
            output = response.get("content", "")
            results[agent_name] = output
            self._log_interaction(
                coord_session,
                orchestrator,
                agent,
                "delegation",
                {
                    "sub_task": sub_task[:200],
                    "output": output[:300],
                },
            )

        # Step 3: Orchestrator synthesises
        synthesis_messages = [
            {
                "role": "system",
                "content": f"You are {orchestrator.name}. Synthesise the specialist outputs into a final answer.",
            },
            {
                "role": "user",
                "content": (
                    f"Original task: {task}\n\n"
                    f"Specialist outputs:\n{json.dumps(results, indent=2)}"
                ),
            },
        ]
        synthesis = groq.chat_completion(synthesis_messages)
        final_answer = synthesis.get("content", "")

        return results, final_answer

    def _run_collaborative(
        self,
        coord_session,
        agents: list,
        task: str,
        context: dict,
        rounds: int = 2,
    ):
        """
        Agents iteratively refine a shared answer.
        Round 1: each agent proposes an answer.
        Round 2+: each agent critiques and improves the previous round's draft.
        """
        from agents.services.groq_service import GroqService

        groq = GroqService()

        results: dict[str, Any] = {}
        current_draft = task

        for round_num in range(1, rounds + 1):
            round_outputs: dict[str, str] = {}
            for agent in agents:
                if round_num == 1:
                    prompt = f"Task: {task}\nProvide your initial answer."
                else:
                    prompt = (
                        f"Task: {task}\n\n"
                        f"Current collaborative draft:\n{current_draft}\n\n"
                        "Critique and improve the draft. Keep the best parts and fix weaknesses."
                    )

                messages = [
                    {
                        "role": "system",
                        "content": (
                            f"You are {agent.name} ({agent.type} agent) in a collaborative refinement process."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
                response = groq.chat_completion(messages)
                output = response.get("content", "")
                round_outputs[agent.name] = output
                self._log_interaction(
                    coord_session,
                    agent,
                    None,
                    f"collaborative_round_{round_num}",
                    {
                        "output": output[:300],
                    },
                )

            # Merge round outputs into a new draft
            current_draft = "\n\n".join(
                f"[{name}]: {out}" for name, out in round_outputs.items()
            )
            results[f"round_{round_num}"] = round_outputs

        return results, current_draft

    def _run_competitive(
        self,
        coord_session,
        agents: list,
        task: str,
        context: dict,
    ):
        """
        Each agent independently solves the task.
        A judge LLM selects the best answer.
        """
        from agents.services.groq_service import GroqService

        groq = GroqService()

        # All agents answer independently
        results: dict[str, str] = {}
        for agent in agents:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are {agent.name} ({agent.type} agent). "
                        "Provide the best possible answer to this task."
                    ),
                },
                {"role": "user", "content": task},
            ]
            response = groq.chat_completion(messages)
            output = response.get("content", "")
            results[agent.name] = output
            self._log_interaction(
                coord_session,
                agent,
                None,
                "competitive_entry",
                {
                    "output": output[:300],
                },
            )

        # Judge selects winner
        judge_messages = [
            {
                "role": "system",
                "content": (
                    "You are an impartial judge. Evaluate the following agent responses "
                    "and select the BEST one. Respond with JSON: "
                    '{"winner": "<agent_name>", "reason": "<brief reason>"}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\n" f"Responses:\n{json.dumps(results, indent=2)}"
                ),
            },
        ]
        judge_response = groq.chat_completion(judge_messages, temperature=0.1)
        judge_text = judge_response.get("content", "")

        winner_name = next(iter(results.keys())) if results else ""
        try:
            import re

            match = re.search(r"\{.*\}", judge_text, re.DOTALL)
            if match:
                verdict = json.loads(match.group())
                winner_name = verdict.get("winner", winner_name)
        except Exception:  # noqa: BLE001, S110
            pass

        final_answer = results.get(
            winner_name, next(iter(results.values())) if results else ""
        )
        self._record_metric(coord_session, "competitive_winner", 0.0)

        return results, f"[Winner: {winner_name}]\n\n{final_answer}"

    # ─────────────────────────────────────────────────────────────────────────
    # DB helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _create_coord_session(self, session, strategy: str, task: str, context: dict):
        from .models import AgentCoordinationSession

        return AgentCoordinationSession.objects.create(
            name=f"auto:{strategy}:{str(task)[:50]}",
            strategy=strategy,
            user=session.user,
            config={"task": task[:500], "session_id": str(session.id)},
            context=context,
            is_active=True,
        )

    def _close_coord_session(self, coord_session, success: bool):
        try:
            coord_session.is_active = False
            coord_session.completed_at = datetime.now(tz=timezone.utc)
            coord_session.context["success"] = success
            coord_session.save(update_fields=["is_active", "completed_at", "context"])
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Could not close coordination session: {e}")

    def _log_interaction(
        self,
        coord_session,
        source_agent,
        target_agent,
        interaction_type: str,
        content: dict,
    ):
        try:
            from .models import AgentInteraction

            AgentInteraction.objects.create(
                coordination_session=coord_session,
                source_agent_id=source_agent.id,
                target_agent_id=target_agent.id if target_agent else source_agent.id,
                interaction_type=interaction_type,
                content=content,
                processed=True,
                processed_at=datetime.now(tz=timezone.utc),
            )
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Interaction log skipped: {e}")

    def _record_metric(self, coord_session, name: str, value: float):
        try:
            from .models import CoordinationMetric

            CoordinationMetric.objects.create(
                coordination_session=coord_session,
                metric_name=name,
                metric_value=value,
            )
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Metric record skipped: {e}")
