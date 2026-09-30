"""
Agent Learning Service
Implements reinforcement learning algorithms and adaptive coordination
"""

import json
import random
from decimal import Decimal
from typing import Any

import numpy as np
from django.db.models import Q
from django.utils import timezone

from ..learning_models import (
    AdaptiveCoordinationRule,
    AgentExperience,
    AgentLearningProfile,
    AgentSkillEvolution,
    LearningSession,
    LearningStrategy,
)
from ..models import Agent, Session


class AgentLearningService:
    """Service for managing agent learning and adaptation"""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.profile, _ = AgentLearningProfile.objects.get_or_create(agent=agent)

    def record_experience(
        self,
        state: dict,
        action: dict,
        reward: float,
        next_state: dict,
        task_type: str,
        done: bool = False,
        session: Session | None = None,
        coordination_strategy: str = "",
        execution_time_ms: int | None = None,
    ) -> AgentExperience:
        """Record a new experience for learning"""
        experience = AgentExperience.objects.create(
            agent=self.agent,
            session=session,
            state=state,
            action=action,
            reward=Decimal(str(reward)),
            next_state=next_state,
            done=done,
            task_type=task_type,
            coordination_strategy=coordination_strategy,
            execution_time_ms=execution_time_ms,
        )

        # Update profile statistics
        self.profile.total_experiences += 1
        if reward > 0:
            self.profile.successful_experiences += 1
        else:
            self.profile.failed_experiences += 1

        # Update average reward (exponential moving average)
        alpha = 0.1
        current_avg = float(self.profile.average_reward)
        new_avg = current_avg + alpha * (reward - current_avg)
        self.profile.average_reward = Decimal(str(new_avg))

        # Update best reward
        if reward > float(self.profile.best_reward):
            self.profile.best_reward = Decimal(str(reward))

        self.profile.save()

        # Update Q-table if using Q-learning
        if self.profile.strategy == LearningStrategy.Q_LEARNING:
            self._update_q_table(state, action, reward, next_state, done)

        return experience

    def _update_q_table(
        self, state: dict, action: dict, reward: float, next_state: dict, done: bool
    ):
        """Update Q-table using Q-learning algorithm"""
        state_key = json.dumps(state, sort_keys=True)
        action_key = json.dumps(action, sort_keys=True)
        next_state_key = json.dumps(next_state, sort_keys=True)

        # Get current Q-value
        q_table = self.profile.q_table
        state_actions = q_table.get(state_key, {})
        current_q = state_actions.get(action_key, 0.0)

        # Calculate max Q-value for next state
        if done:
            max_next_q = 0.0
        else:
            next_state_actions = q_table.get(next_state_key, {})
            max_next_q = max(next_state_actions.values()) if next_state_actions else 0.0

        # Q-learning update rule
        learning_rate = float(self.profile.learning_rate)
        discount_factor = float(self.profile.discount_factor)
        new_q = current_q + learning_rate * (
            reward + discount_factor * max_next_q - current_q
        )

        # Update Q-table
        if state_key not in q_table:
            q_table[state_key] = {}
        q_table[state_key][action_key] = new_q

        self.profile.q_table = q_table
        self.profile.last_training_at = timezone.now()
        self.profile.save()

    def select_action(self, state: dict, available_actions: list[dict]) -> dict:
        """Select action using epsilon-greedy policy"""
        if not self.profile.is_learning_enabled or not available_actions:
            return random.choice(available_actions)

        # Epsilon-greedy exploration
        exploration_rate = float(self.profile.exploration_rate)
        if random.random() < exploration_rate:
            # Explore: random action
            return random.choice(available_actions)

        # Exploit: best known action
        state_key = json.dumps(state, sort_keys=True)
        state_actions = self.profile.q_table.get(state_key, {})

        if not state_actions:
            return random.choice(available_actions)

        # Find action with highest Q-value among available actions
        best_action = None
        best_q = float("-inf")

        for action in available_actions:
            action_key = json.dumps(action, sort_keys=True)
            q_value = state_actions.get(action_key, 0.0)
            if q_value > best_q:
                best_q = q_value
                best_action = action

        return best_action if best_action else random.choice(available_actions)

    def update_skill(self, skill_name: str, success: bool, performance_score: float):
        """Update agent skill proficiency"""
        skill, _ = AgentSkillEvolution.objects.get_or_create(
            agent=self.agent, skill_name=skill_name
        )
        skill.record_usage(success, performance_score)

        # Update profile skill matrix
        skill_matrix = self.profile.skill_matrix
        skill_matrix[skill_name] = float(skill.proficiency_level)
        self.profile.skill_matrix = skill_matrix
        self.profile.save()

    def get_specialized_tasks(self) -> list[str]:
        """Get tasks the agent excels at"""
        threshold = 0.75  # Proficiency threshold for specialization

        specialized = []
        for skill_name, proficiency in self.profile.skill_matrix.items():
            if proficiency >= threshold:
                specialized.append(skill_name)

        return specialized

    def start_learning_session(
        self, session_type: str, initial_performance: float, config: dict | None = None
    ) -> LearningSession:
        """Start a new learning session"""
        return LearningSession.objects.create(
            agent=self.agent,
            session_type=session_type,
            initial_performance=Decimal(str(initial_performance)),
            final_performance=Decimal(str(initial_performance)),
            training_config=config or {},
        )

    def complete_learning_session(
        self,
        session: LearningSession,
        final_performance: float,
        experiences_processed: int,
    ):
        """Complete a learning session"""
        session.final_performance = Decimal(str(final_performance))
        session.experiences_processed = experiences_processed
        session.complete()

        # Update profile performance score
        self.profile.current_performance_score = session.final_performance
        self.profile.save()

    def batch_learn(self, batch_size: int = 32, epochs: int = 10) -> dict:
        """Perform batch learning from recent experiences"""
        # Get recent experiences
        recent_experiences = AgentExperience.objects.filter(agent=self.agent).order_by(
            "-created_at"
        )[:1000]

        if len(recent_experiences) < batch_size:
            return {"error": "Insufficient experiences for batch learning"}

        # Start learning session
        current_performance = float(self.profile.current_performance_score)
        learning_session = self.start_learning_session(
            "batch", current_performance, {"batch_size": batch_size, "epochs": epochs}
        )

        experiences_processed = 0

        for epoch in range(epochs):
            # Sample random batch
            batch = random.sample(
                list(recent_experiences), min(batch_size, len(recent_experiences))
            )

            for exp in batch:
                # Re-apply Q-learning update
                self._update_q_table(
                    exp.state, exp.action, float(exp.reward), exp.next_state, exp.done
                )
                experiences_processed += 1

        # Calculate new performance (average reward)
        final_performance = float(self.profile.average_reward)
        self.complete_learning_session(
            learning_session, final_performance, experiences_processed
        )

        # Decay exploration rate
        self.profile.update_exploration_rate()

        return {
            "session_id": str(learning_session.id),
            "experiences_processed": experiences_processed,
            "initial_performance": current_performance,
            "final_performance": final_performance,
            "improvement": final_performance - current_performance,
        }


class AdaptiveCoordinationService:
    """Service for adaptive coordination strategy selection"""

    @staticmethod
    def recommend_strategy(
        task_type: str,
        agent_count: int,
        task_complexity: int,
        context: dict | None = None,
    ) -> tuple[str, dict]:
        """Recommend coordination strategy based on learned rules"""

        # Find applicable rules
        rules = AdaptiveCoordinationRule.objects.filter(
            is_active=True,
            task_complexity_min__lte=task_complexity,
            task_complexity_max__gte=task_complexity,
            agent_count_min__lte=agent_count,
            agent_count_max__gte=agent_count,
        ).order_by("-success_rate", "-times_applied")

        # Filter by task type if specified
        if task_type:
            rules = rules.filter(
                Q(task_types__contains=[task_type]) | Q(task_types__contains=["*"])
            )

        # Select best rule
        best_rule = rules.first()

        if best_rule:
            return best_rule.recommended_strategy, best_rule.strategy_parameters

        # Fallback: default strategy based on simple heuristics
        if agent_count == 1:
            return "sequential", {}
        elif task_complexity > 70:
            return "hierarchical", {"max_depth": 3}
        elif agent_count > 5:
            return "parallel", {"max_concurrent": agent_count}
        else:
            return "collaborative", {"consensus_threshold": 0.7}

    @staticmethod
    def record_strategy_outcome(rule_id: str, success: bool, improvement: float):
        """Record outcome of applying a coordination rule"""
        try:
            rule = AdaptiveCoordinationRule.objects.get(id=rule_id)
            rule.update_performance(success, improvement)
        except AdaptiveCoordinationRule.DoesNotExist:
            pass

    @staticmethod
    def create_learned_rule(
        name: str,
        task_types: list[str],
        complexity_range: tuple[int, int],
        agent_count_range: tuple[int, int],
        recommended_strategy: str,
        creator,
        description: str = "",
    ) -> AdaptiveCoordinationRule:
        """Create a new coordination rule from learned patterns"""
        return AdaptiveCoordinationRule.objects.create(
            name=name,
            description=description or f"Auto-generated rule for {task_types}",
            task_complexity_min=complexity_range[0],
            task_complexity_max=complexity_range[1],
            agent_count_min=agent_count_range[0],
            agent_count_max=agent_count_range[1],
            task_types=task_types,
            recommended_strategy=recommended_strategy,
            is_auto_generated=True,
            created_by=creator,
        )

    @staticmethod
    def analyze_patterns_and_generate_rules(creator, min_samples: int = 50):
        """
        Analyze historical coordination sessions and auto-generate rules
        for strategy combinations that show consistently high success rates.
        """
        from django.db.models import Avg, Count
        from Multi_agents_cordination.models import (
            AgentCoordinationSession,
            CoordinationMetric,
        )

        generated_rules: list[AdaptiveCoordinationRule] = []

        # ── Aggregate completed sessions grouped by strategy ──────────────────
        strategy_stats = (
            AgentCoordinationSession.objects.filter(
                is_active=False, completed_at__isnull=False
            )
            .values("strategy")
            .annotate(
                session_count=Count("id"),
                avg_duration=Avg(
                    "metrics__metric_value",
                    filter=Q(metrics__metric_name="duration_ms"),
                ),
            )
            .filter(session_count__gte=min_samples)
        )

        for stat in strategy_stats:
            strategy = stat["strategy"]
            session_count = stat["session_count"]
            avg_duration_ms = stat["avg_duration"] or 0.0

            # Determine complexity range from recorded agent counts
            agent_counts = list(
                CoordinationMetric.objects.filter(
                    coordination_session__strategy=strategy,
                    metric_name="agents_count",
                ).values_list("metric_value", flat=True)
            )
            if not agent_counts:
                continue

            min_agents = max(1, int(min(agent_counts)))
            max_agents = max(min_agents, int(max(agent_counts)))

            # Success proxy: sessions that completed with no 'error' metrics
            error_sessions = (
                CoordinationMetric.objects.filter(
                    coordination_session__strategy=strategy,
                    metric_name="error",
                )
                .values("coordination_session_id")
                .distinct()
                .count()
            )
            success_rate = max(0.0, (session_count - error_sessions) / session_count)

            # Only create a rule if strategy is reliably successful
            if success_rate < 0.6:
                continue

            # Derive complexity score from average duration (simple heuristic)
            if avg_duration_ms < 2000:
                complexity_min, complexity_max = 0, 40
            elif avg_duration_ms < 8000:
                complexity_min, complexity_max = 30, 70
            else:
                complexity_min, complexity_max = 60, 100

            rule_name = f"auto_{strategy}_{min_agents}_{max_agents}_agents"

            # Skip if an identical auto-generated rule already exists
            if AdaptiveCoordinationRule.objects.filter(
                name=rule_name, is_auto_generated=True
            ).exists():
                continue

            rule = AdaptiveCoordinationRule.objects.create(
                name=rule_name,
                description=(
                    f"Auto-generated from {session_count} sessions. "
                    f"Strategy '{strategy}' had {success_rate:.0%} success rate."
                ),
                task_complexity_min=complexity_min,
                task_complexity_max=complexity_max,
                agent_count_min=min_agents,
                agent_count_max=max_agents,
                task_types=["*"],
                recommended_strategy=strategy,
                strategy_parameters={"avg_duration_ms": round(avg_duration_ms, 1)},
                is_auto_generated=True,
                created_by=creator,
            )
            generated_rules.append(rule)

        return generated_rules


class SkillEvolutionTracker:
    """Tracks and analyzes skill evolution across agents"""

    @staticmethod
    def get_agent_expertise(agent: Agent) -> dict[str, Any]:
        """Get comprehensive expertise profile for agent"""
        skills = AgentSkillEvolution.objects.filter(agent=agent).order_by(
            "-proficiency_level"
        )

        return {
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "total_skills": skills.count(),
            "top_skills": [
                {
                    "skill": skill.skill_name,
                    "proficiency": float(skill.proficiency_level),
                    "confidence": float(skill.confidence_score),
                    "usage_count": skill.usage_count,
                }
                for skill in skills[:10]
            ],
            "skill_diversity": SkillEvolutionTracker._calculate_skill_diversity(skills),
            "overall_performance": (
                float(agent.learning_profile.current_performance_score)
                if hasattr(agent, "learning_profile")
                else 0.5
            ),
        }

    @staticmethod
    def _calculate_skill_diversity(skills) -> float:
        """Calculate Shannon entropy of skill distribution"""
        if not skills:
            return 0.0

        total_usage = sum(skill.usage_count for skill in skills)
        if total_usage == 0:
            return 0.0

        entropy = 0.0
        for skill in skills:
            p = skill.usage_count / total_usage
            if p > 0:
                entropy -= p * np.log2(p)

        # Normalize to 0-1 range
        max_entropy = np.log2(len(skills)) if len(skills) > 1 else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0

    @staticmethod
    def recommend_training(agent: Agent) -> list[dict]:
        """Recommend training areas for agent improvement"""
        skills = AgentSkillEvolution.objects.filter(agent=agent)

        recommendations = []

        # Find skills with low proficiency but high usage (need improvement)
        for skill in skills:
            if skill.usage_count > 10 and float(skill.proficiency_level) < 0.6:
                recommendations.append(
                    {
                        "skill": skill.skill_name,
                        "priority": "high",
                        "reason": "Frequently used but low proficiency",
                        "current_level": float(skill.proficiency_level),
                        "target_level": 0.8,
                    }
                )

        # Find skills with declining performance
        for skill in skills:
            if len(skill.performance_history) >= 10:
                recent = skill.performance_history[-10:]
                early = skill.performance_history[:10]
                recent_avg = np.mean([h["performance"] for h in recent])
                early_avg = np.mean([h["performance"] for h in early])

                if recent_avg < early_avg * 0.8:  # 20% decline
                    recommendations.append(
                        {
                            "skill": skill.skill_name,
                            "priority": "medium",
                            "reason": "Performance declining",
                            "decline_percentage": ((early_avg - recent_avg) / early_avg)
                            * 100,
                        }
                    )

        return sorted(
            recommendations, key=lambda x: 0 if x["priority"] == "high" else 1
        )
