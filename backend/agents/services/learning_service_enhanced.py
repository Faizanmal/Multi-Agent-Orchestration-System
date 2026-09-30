"""
Agent Learning Service - Reinforcement Learning for Agent Self-Improvement
"""

import logging
from collections import deque
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ReinforcementLearningAgent:
    """
    Q-Learning based agent for self-improvement
    Learns optimal action selection based on rewards
    """

    def __init__(
        self,
        agent_id: str,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
    ):
        """
        Initialize RL agent

        Args:
            agent_id: Unique agent identifier
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor for future rewards (gamma)
            epsilon: Exploration rate for epsilon-greedy policy
        """
        self.agent_id = agent_id
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon

        # Q-table: state -> action -> Q-value
        self.q_table = {}

        # Experience replay buffer
        self.replay_buffer = deque(maxlen=10000)

        # Performance tracking
        self.episode_rewards = []
        self.total_steps = 0

    def get_state_representation(self, context: dict) -> str:
        """
        Convert context to state representation

        Args:
            context: Current context dictionary

        Returns:
            State string representation
        """
        # Extract key features for state
        features = [
            context.get("task_type", "unknown"),
            context.get("complexity", "simple"),
            str(context.get("message_length_bucket", "short")),  # short/medium/long
            str(context.get("conversation_depth", 0) // 5),  # Bucketed depth
        ]

        return "|".join(features)

    def select_action(
        self, state: str, available_actions: list[str], explore: bool = True
    ) -> str:
        """
        Select action using epsilon-greedy policy

        Args:
            state: Current state
            available_actions: List of possible actions
            explore: Whether to explore or purely exploit

        Returns:
            Selected action
        """
        # Initialize Q-values for new state
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in available_actions}

        # Epsilon-greedy selection
        if explore and np.random.random() < self.epsilon:
            # Explore: random action
            action = np.random.choice(available_actions)
            logger.debug(f"Agent {self.agent_id}: Exploring with action {action}")
        else:
            # Exploit: best known action
            state_q_values = self.q_table[state]
            max_q = max(state_q_values.values())
            # Handle ties by random selection
            best_actions = [a for a, q in state_q_values.items() if q == max_q]
            action = np.random.choice(best_actions)
            logger.debug(
                f"Agent {self.agent_id}: Exploiting with action {action} (Q={max_q:.3f})"
            )

        return action

    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        next_available_actions: list[str],
    ):
        """
        Update Q-value using Q-learning update rule

        Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Resulting state
            next_available_actions: Actions available in next state
        """
        # Initialize next state Q-values if needed
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in next_available_actions}

        # Get current Q-value
        current_q = self.q_table[state][action]

        # Get max Q-value for next state
        max_next_q = (
            max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        )

        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state][action] = new_q

        logger.debug(
            f"Agent {self.agent_id}: Updated Q({state}, {action}): {current_q:.3f} -> {new_q:.3f}"
        )

        # Store experience
        self.replay_buffer.append(
            {
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "next_actions": next_available_actions,
            }
        )

        self.total_steps += 1

    def experience_replay(self, batch_size: int = 32):
        """
        Perform experience replay to improve learning stability

        Args:
            batch_size: Number of experiences to replay
        """
        if len(self.replay_buffer) < batch_size:
            return

        # Sample random batch
        indices = np.random.choice(len(self.replay_buffer), batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in indices]

        # Update Q-values for sampled experiences
        for exp in batch:
            self.update_q_value(
                exp["state"],
                exp["action"],
                exp["reward"],
                exp["next_state"],
                exp["next_actions"],
            )

    def decay_epsilon(self, decay_rate: float = 0.995, min_epsilon: float = 0.01):
        """Decay exploration rate over time"""
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)

    def get_policy(self) -> dict[str, dict[str, float]]:
        """Get current learned policy"""
        return self.q_table

    def save_policy(self) -> dict[str, Any]:
        """Serialize policy for persistence"""
        return {
            "agent_id": self.agent_id,
            "q_table": self.q_table,
            "epsilon": self.epsilon,
            "total_steps": self.total_steps,
            "replay_buffer_size": len(self.replay_buffer),
        }

    def load_policy(self, policy_data: dict[str, Any]):
        """Load policy from serialized data"""
        self.q_table = policy_data.get("q_table", {})
        self.epsilon = policy_data.get("epsilon", self.epsilon)
        self.total_steps = policy_data.get("total_steps", 0)


class AgentLearningService:
    """
    Service for managing agent learning and self-improvement
    """

    def __init__(self):
        self.rl_agents = {}  # agent_id -> ReinforcementLearningAgent

    def get_or_create_rl_agent(self, agent_id: str) -> ReinforcementLearningAgent:
        """Get or create RL agent instance"""
        if agent_id not in self.rl_agents:
            self.rl_agents[agent_id] = ReinforcementLearningAgent(agent_id)
            # Try to load existing policy
            self._load_agent_policy(agent_id)

        return self.rl_agents[agent_id]

    def recommend_action(
        self, agent_id: str, context: dict, available_actions: list[str]
    ) -> dict[str, Any]:
        """
        Recommend action for agent based on learned policy

        Args:
            agent_id: Agent identifier
            context: Current context
            available_actions: Available actions

        Returns:
            Recommendation with action and confidence
        """
        rl_agent = self.get_or_create_rl_agent(agent_id)
        state = rl_agent.get_state_representation(context)

        # Get action
        action = rl_agent.select_action(state, available_actions, explore=True)

        # Calculate confidence based on Q-value
        if state in rl_agent.q_table and action in rl_agent.q_table[state]:
            q_value = rl_agent.q_table[state][action]
            # Normalize Q-value to confidence (0-1)
            confidence = 1 / (1 + np.exp(-q_value))  # Sigmoid
        else:
            confidence = 0.5  # Neutral for unseen state-action

        return {
            "action": action,
            "confidence": confidence,
            "state": state,
            "exploration_rate": rl_agent.epsilon,
        }

    def provide_feedback(
        self,
        agent_id: str,
        context: dict,
        action: str,
        outcome: dict,
        next_context: dict,
        next_available_actions: list[str],
    ):
        """
        Provide feedback to agent for learning

        Args:
            agent_id: Agent identifier
            context: Context when action was taken
            action: Action that was taken
            outcome: Outcome of the action
            next_context: Resulting context
            next_available_actions: Actions available after
        """
        rl_agent = self.get_or_create_rl_agent(agent_id)

        state = rl_agent.get_state_representation(context)
        next_state = rl_agent.get_state_representation(next_context)

        # Calculate reward based on outcome
        reward = self._calculate_reward(outcome)

        # Update Q-value
        rl_agent.update_q_value(
            state, action, reward, next_state, next_available_actions
        )

        # Periodically perform experience replay
        if rl_agent.total_steps % 10 == 0:
            rl_agent.experience_replay()

        # Decay exploration rate
        if rl_agent.total_steps % 100 == 0:
            rl_agent.decay_epsilon()

        # Save policy periodically
        if rl_agent.total_steps % 50 == 0:
            self._save_agent_policy(agent_id)

        logger.info(
            f"Agent {agent_id} learned from feedback: reward={reward:.3f}, "
            f"steps={rl_agent.total_steps}, epsilon={rl_agent.epsilon:.3f}"
        )

    def _calculate_reward(self, outcome: dict) -> float:
        """
        Calculate reward based on outcome

        Args:
            outcome: Outcome dictionary with metrics

        Returns:
            Reward value
        """
        reward = 0.0

        # Success/failure
        if outcome.get("success", False):
            reward += 1.0
        else:
            reward -= 1.0

        # Response time (faster is better)
        duration = outcome.get("duration_ms", 5000)
        if duration < 1000:
            reward += 0.5
        elif duration > 5000:
            reward -= 0.3

        # User satisfaction (if available)
        satisfaction = outcome.get("user_rating")
        if satisfaction is not None:
            reward += (satisfaction - 3) * 0.5  # Scale from 1-5 to -1 to +1

        # Token efficiency
        tokens = outcome.get("tokens_used", 0)
        if tokens < 500:
            reward += 0.2
        elif tokens > 2000:
            reward -= 0.2

        # Accuracy (if available)
        accuracy = outcome.get("accuracy")
        if accuracy is not None:
            reward += accuracy  # Assuming 0-1 scale

        return reward

    def _load_agent_policy(self, agent_id: str):
        """Load agent policy from database"""
        try:
            from agent_learning.models import AgentLearningPolicy

            policy = (
                AgentLearningPolicy.objects.filter(agent_id=agent_id, is_active=True)
                .order_by("-updated_at")
                .first()
            )

            if policy:
                rl_agent = self.rl_agents[agent_id]
                rl_agent.load_policy(policy.policy_data)
                logger.info(f"Loaded policy for agent {agent_id}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to load policy for agent {agent_id}: {e}")

    def _save_agent_policy(self, agent_id: str):
        """Save agent policy to database"""
        try:
            from agent_learning.models import AgentLearningPolicy

            from agents.models import Agent

            rl_agent = self.rl_agents[agent_id]
            policy_data = rl_agent.save_policy()

            # Get agent instance
            agent = Agent.objects.get(id=agent_id)

            # Deactivate old policies
            AgentLearningPolicy.objects.filter(agent_id=agent_id).update(
                is_active=False
            )

            # Create new policy
            AgentLearningPolicy.objects.create(
                agent=agent,
                agent_id=agent_id,
                policy_data=policy_data,
                total_episodes=rl_agent.total_steps,
                average_reward=(
                    np.mean(rl_agent.episode_rewards[-100:])
                    if rl_agent.episode_rewards
                    else 0.0
                ),
                is_active=True,
            )

            logger.info(f"Saved policy for agent {agent_id}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to save policy for agent {agent_id}: {e}")

    def get_learning_statistics(self, agent_id: str) -> dict[str, Any]:
        """Get learning statistics for an agent"""
        if agent_id not in self.rl_agents:
            return {"message": "Agent has no learning data"}

        rl_agent = self.rl_agents[agent_id]

        # Calculate statistics
        recent_rewards = (
            rl_agent.episode_rewards[-100:] if rl_agent.episode_rewards else []
        )

        stats = {
            "total_steps": rl_agent.total_steps,
            "exploration_rate": rl_agent.epsilon,
            "states_learned": len(rl_agent.q_table),
            "total_state_actions": sum(
                len(actions) for actions in rl_agent.q_table.values()
            ),
            "replay_buffer_size": len(rl_agent.replay_buffer),
            "recent_avg_reward": np.mean(recent_rewards) if recent_rewards else 0.0,
            "learning_rate": rl_agent.learning_rate,
            "discount_factor": rl_agent.discount_factor,
        }

        return stats

    def analyze_agent_performance(self, agent_id: str) -> dict[str, Any]:
        """Analyze agent performance and provide recommendations"""
        if agent_id not in self.rl_agents:
            return {"recommendations": ["Start learning by executing tasks"]}

        rl_agent = self.rl_agents[agent_id]
        recommendations = []

        # Check exploration rate
        if rl_agent.epsilon < 0.05 and rl_agent.total_steps < 1000:
            recommendations.append(
                "Consider increasing exploration rate for better learning"
            )

        # Check Q-table coverage
        states_count = len(rl_agent.q_table)
        if states_count < 10:
            recommendations.append("Limited experience - execute more diverse tasks")

        # Check recent performance
        recent_rewards = rl_agent.episode_rewards[-100:]
        if recent_rewards:
            avg_reward = np.mean(recent_rewards)
            if avg_reward < 0:
                recommendations.append(
                    "Negative average reward - review action selection strategy"
                )

        return {
            "overall_score": self._calculate_overall_score(rl_agent),
            "recommendations": recommendations,
            "learning_progress": (
                "advanced"
                if rl_agent.total_steps > 1000
                else "intermediate" if rl_agent.total_steps > 100 else "beginner"
            ),
        }

    def _calculate_overall_score(self, rl_agent: ReinforcementLearningAgent) -> float:
        """Calculate overall learning score (0-100)"""
        score = 0.0

        # Experience score (0-40)
        experience_score = min(40, (rl_agent.total_steps / 1000) * 40)
        score += experience_score

        # Coverage score (0-30)
        coverage_score = min(30, (len(rl_agent.q_table) / 50) * 30)
        score += coverage_score

        # Performance score (0-30)
        if rl_agent.episode_rewards:
            recent_rewards = rl_agent.episode_rewards[-100:]
            avg_reward = np.mean(recent_rewards)
            # Normalize to 0-30 (assuming rewards are in range -2 to +2)
            performance_score = min(30, max(0, ((avg_reward + 2) / 4) * 30))
            score += performance_score

        return score


# Singleton instance
_learning_service = None


def get_learning_service() -> AgentLearningService:
    """Get or create learning service singleton"""
    global _learning_service
    if _learning_service is None:
        _learning_service = AgentLearningService()
    return _learning_service
