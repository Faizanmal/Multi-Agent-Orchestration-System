"""
Service classes for reinforcement learning and strategy optimization
"""

import logging

logger = logging.getLogger(__name__)


class RLEngine:
    """Reinforcement Learning Engine for agent training"""

    def __init__(self, learning_profile):
        self.profile = learning_profile
        self.learning_rate = learning_profile.learning_rate
        self.discount_factor = learning_profile.discount_factor

    def update_q_values(self, rl_state):
        """Update Q-values using Q-learning algorithm"""
        try:
            # Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
            current_q = rl_state.q_value
            reward = rl_state.reward

            # Get max Q-value for next state (simplified)
            if rl_state.next_state:
                max_next_q = self._estimate_max_q(rl_state.next_state)
            else:
                max_next_q = 0.0

            # Calculate new Q-value
            td_target = reward + (self.discount_factor * max_next_q)
            new_q = current_q + (self.learning_rate * (td_target - current_q))

            rl_state.q_value = new_q
            rl_state.expected_q_value = td_target
            rl_state.save()

            # Update profile success rate
            self._update_success_rate(rl_state.success)

            return new_q

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating Q-values: {e!s}")
            return 0.0

    def _estimate_max_q(self, state: dict) -> float:
        """Estimate maximum Q-value for a state"""
        # Simplified: return average of recent Q-values
        from .models import ReinforcementState

        recent_states = ReinforcementState.objects.filter(
            learning_profile=self.profile
        ).order_by("-created_at")[:10]

        if not recent_states.exists():
            return 0.0

        avg_q = sum(s.q_value for s in recent_states) / len(recent_states)
        return avg_q

    def _update_success_rate(self, success: bool):
        """Update agent's success rate"""
        total_tasks = self.profile.total_tasks_completed
        current_rate = self.profile.success_rate

        if total_tasks <= 1:
            self.profile.success_rate = 1.0 if success else 0.0
        else:
            # Moving average
            self.profile.success_rate = (
                current_rate * (total_tasks - 1) + (1.0 if success else 0.0)
            ) / total_tasks

        self.profile.save()

    def get_best_action(self, state: dict) -> dict:
        """Get best action for current state"""
        try:
            from .models import ReinforcementState

            # Find similar past states
            similar_states = ReinforcementState.objects.filter(
                learning_profile=self.profile, success=True
            ).order_by("-q_value")[:5]

            if not similar_states.exists():
                return {"action": {}, "q_value": 0.0, "confidence": 0.1}

            # Return action with highest Q-value
            best_state = similar_states[0]
            confidence = min(
                1.0, self.profile.success_rate + (similar_states.count() / 50)
            )

            return {
                "action": best_state.action_taken,
                "q_value": best_state.q_value,
                "confidence": confidence,
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting best action: {e!s}")
            return {"action": {}, "q_value": 0.0, "confidence": 0.0}


class StrategyOptimizer:
    """Optimize coordination strategies based on historical performance"""

    def recommend_strategy(
        self, task_description: str, complexity: str, agents: list
    ) -> dict:
        """Recommend best coordination strategy"""
        try:
            from .models import AdaptiveStrategy

            # Map complexity to strategy preference
            strategy_preference = {
                "low": "sequential",
                "medium": "parallel",
                "high": "hierarchical",
                "complex": "collaborative",
            }

            preferred_type = strategy_preference.get(complexity, "parallel")

            # Find best matching strategy
            strategies = AdaptiveStrategy.objects.filter(
                strategy_type=preferred_type, is_active=True
            ).order_by("-confidence_score", "-success_rate")

            if strategies.exists():
                best_strategy = strategies[0]
                return {
                    "strategy_id": str(best_strategy.id),
                    "strategy_name": best_strategy.name,
                    "strategy_type": best_strategy.strategy_type,
                    "confidence": best_strategy.confidence_score,
                    "expected_success_rate": best_strategy.success_rate,
                    "agent_roles": best_strategy.agent_roles,
                    "description": best_strategy.description,
                }

            # Fallback to default strategy
            return {
                "strategy_type": preferred_type,
                "confidence": 0.5,
                "expected_success_rate": 0.7,
                "agent_roles": self._generate_default_roles(preferred_type, agents),
                "description": f"Default {preferred_type} strategy",
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error recommending strategy: {e!s}")
            return {
                "strategy_type": "parallel",
                "confidence": 0.3,
                "description": "Fallback parallel strategy",
            }

    def _generate_default_roles(self, strategy_type: str, agents: list) -> dict:
        """Generate default agent roles for strategy"""
        if not agents:
            return {}

        if strategy_type == "hierarchical":
            return {
                "orchestrator": agents[0] if agents else None,
                "workers": agents[1:] if len(agents) > 1 else [],
            }
        elif strategy_type == "sequential":
            return {"sequence": agents}
        else:
            return {"agents": agents}
