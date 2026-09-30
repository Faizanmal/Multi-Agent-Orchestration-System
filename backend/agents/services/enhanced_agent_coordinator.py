import logging
from datetime import datetime, timezone
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from ..models import Agent, AgentStatus, Message, Session, Task, TaskStatus
from .agent_selector import SmartAgentSelector
from .audio_service import AudioService
from .groq_service import GroqService
from .langchain_coordinator import LangchainAgentCoordinator
from .performance_tracker import PerformanceTracker
from .vision_service import VisionService

logger = logging.getLogger(__name__)


class EnhancedAgentCoordinator:
    """
    Enhanced coordinator for managing multi-agent workflows and communication with improved performance
    """

    def __init__(self, session: Session):
        self.session = session
        self.groq_service = GroqService()
        self.vision_service = VisionService()
        self.audio_service = AudioService()
        self.performance_tracker = PerformanceTracker()
        self.agent_selector = SmartAgentSelector()
        self.active_agents = {}
        self.task_queue = []

    def process_message(self, message: Message) -> dict[str, Any]:
        """
        Process incoming message and coordinate agent responses with enhanced logic

        Args:
            message: The message to process

        Returns:
            Coordination results
        """
        logger.info(f"Processing message: {message.id}")

        # Use Langchain-based coordination for enhanced collaboration
        try:
            langchain_coordinator = LangchainAgentCoordinator(self.session)
            result = langchain_coordinator.process_message(message)
            return result
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Langchain coordination failed, falling back to enhanced coordination: {e!s}"
            )
            # Fallback to original enhanced coordination
            # Determine which agents should handle this message using smart selection
            relevant_agents = self._determine_relevant_agents_enhanced(message)

            # Create tasks for relevant agents
            tasks = []
            for agent in relevant_agents:
                task = self._create_agent_task(agent, message)
                tasks.append(task)

            # Execute tasks in appropriate order with performance tracking
            results = self._execute_tasks_enhanced(tasks)

            # Synthesize results from all agents with improved synthesis
            final_response = self._synthesize_responses_enhanced(results)

            # Send response back to session
            self._send_response_to_session(final_response, message)

            return {
                "message_id": str(message.id),
                "agents_involved": [agent.name for agent in relevant_agents],
                "tasks_created": len(tasks),
                "response": final_response,
            }

    def process_multimodal_message(self, message: Message) -> dict[str, Any]:
        """
        Process multimodal message with appropriate specialized agents

        Args:
            message: The multimodal message

        Returns:
            Processing results
        """
        logger.info(f"Processing multimodal message: {message.message_type}")

        results = {}

        # Process based on message type
        if message.message_type == "image" and message.file_attachment:
            results["vision"] = self.vision_service.analyze_image(
                message.file_attachment.path
            )

        elif message.message_type == "audio" and message.file_attachment:
            results["audio"] = self.audio_service.process_audio(
                message.file_attachment.path
            )

        elif message.message_type == "text":
            results["text"] = self._process_text_message(message)

        # Use reasoning agent to combine insights
        reasoning_agent = self._get_agent_by_type("reasoning")
        if reasoning_agent:
            combined_analysis = self._get_combined_analysis(results, message.content)
            results["reasoning"] = combined_analysis

        # Generate final response
        orchestrator_agent = self._get_agent_by_type("orchestrator")
        if orchestrator_agent:
            final_response = self._orchestrate_final_response(results, message)
            results["final_response"] = final_response

        return results

    def execute_task(self, task: Task) -> dict[str, Any]:
        """
        Execute a specific task with the assigned agent

        Args:
            task: The task to execute

        Returns:
            Execution results
        """
        logger.info(f"Executing task: {task.id}")

        agent = task.assigned_agent

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        task.save()

        start_time = datetime.now(timezone.utc)

        try:
            # Execute based on agent type
            if agent.type == "orchestrator":
                result = self._execute_orchestrator_task(task)
            elif agent.type == "vision":
                result = self._execute_vision_task(task)
            elif agent.type == "reasoning":
                result = self._execute_reasoning_task(task)
            elif agent.type == "action":
                result = self._execute_action_task(task)
            elif agent.type == "memory":
                result = self._execute_memory_task(task)
            else:
                result = self._execute_generic_task(task)

            # Update task with results
            task.output_data = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Task execution failed: {e!s}")
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            result = {"error": str(e)}

        task.save()

        # Track performance
        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        success = task.status == TaskStatus.COMPLETED

        self.performance_tracker.track_task_execution(
            agent_id=str(agent.id),
            task_id=str(task.id),
            task_type=agent.type,
            start_time=start_time,
            end_time=end_time,
            success=success,
            execution_time=execution_time,
        )

        # Notify via WebSocket
        self._notify_task_completion(task, result)

        return result

    def _determine_relevant_agents_enhanced(self, message: Message) -> list[Agent]:
        """Enhanced agent determination with smart selection"""
        relevant_agents = []
        session_agents = self.session.agents.filter(is_active=True)

        # Always include orchestrator if available
        orchestrator = session_agents.filter(type="orchestrator").first()
        if orchestrator:
            relevant_agents.append(orchestrator)

        # Use smart agent selector for better agent matching
        content = message.content.lower()

        # Determine agent needs based on content analysis
        needs_vision = (
            "image" in content
            or "picture" in content
            or "photo" in content
            or "visual" in content
            or message.message_type == "image"
        )
        needs_reasoning = (
            "think" in content
            or "reason" in content
            or "analyze" in content
            or "logic" in content
            or "problem" in content
        )
        needs_action = (
            "do" in content
            or "execute" in content
            or "run" in content
            or "perform" in content
            or "task" in content
        )
        needs_memory = (
            "remember" in content
            or "recall" in content
            or "store" in content
            or "save" in content
            or "history" in content
        )

        # Select best agents using smart selection
        if needs_vision:
            vision_agent = self.agent_selector.select_best_agent(
                "vision", content, session_agents.filter(type="vision")
            )
            if vision_agent and vision_agent not in relevant_agents:
                relevant_agents.append(vision_agent)

        if needs_reasoning:
            reasoning_agent = self.agent_selector.select_best_agent(
                "reasoning", content, session_agents.filter(type="reasoning")
            )
            if reasoning_agent and reasoning_agent not in relevant_agents:
                relevant_agents.append(reasoning_agent)

        if needs_action:
            action_agent = self.agent_selector.select_best_agent(
                "action", content, session_agents.filter(type="action")
            )
            if action_agent and action_agent not in relevant_agents:
                relevant_agents.append(action_agent)

        if needs_memory:
            memory_agent = self.agent_selector.select_best_agent(
                "memory", content, session_agents.filter(type="memory")
            )
            if memory_agent and memory_agent not in relevant_agents:
                relevant_agents.append(memory_agent)

        # If no specific agents identified, include reasoning agent for general analysis
        if len(relevant_agents) <= 1:  # Only orchestrator so far
            reasoning_agent = self.agent_selector.select_best_agent(
                "reasoning", content, session_agents.filter(type="reasoning")
            )
            if reasoning_agent and reasoning_agent not in relevant_agents:
                relevant_agents.append(reasoning_agent)

        return relevant_agents

    def _create_agent_task(self, agent: Agent, message: Message) -> Task:
        """Create a task for an agent to process a message"""
        task = Task.objects.create(
            session=self.session,
            assigned_agent=agent,
            title=f"Process {message.message_type} message",
            description=f"Process message: {message.content[:100]}...",
            input_data={
                "message_id": str(message.id),
                "content": message.content,
                "message_type": message.message_type,
                "metadata": message.metadata,
                "file_path": (
                    message.file_attachment.path if message.file_attachment else None
                ),
            },
            priority=self._calculate_task_priority(agent, message),
        )

        return task

    def _execute_tasks_enhanced(self, tasks: list[Task]) -> dict[str, Any]:
        """Execute multiple tasks with parallel processing for better performance"""
        results = {}

        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Execute high-priority tasks first, then others in parallel where possible
        high_priority_tasks = [t for t in sorted_tasks if t.priority >= 8]
        regular_tasks = [t for t in sorted_tasks if t.priority < 8]

        # Execute high-priority tasks sequentially
        for task in high_priority_tasks:
            result = self.execute_task(task)
            results[str(task.id)] = result

            # Update agent status
            task.assigned_agent.status = AgentStatus.ACTIVE
            task.assigned_agent.save()

        # Execute regular tasks (can be parallelized in future)
        for task in regular_tasks:
            result = self.execute_task(task)
            results[str(task.id)] = result

            # Update agent status
            task.assigned_agent.status = AgentStatus.ACTIVE
            task.assigned_agent.save()

        return results

    def _synthesize_responses_enhanced(self, results: dict[str, Any]) -> dict[str, Any]:
        """Enhanced response synthesis with better coordination"""
        orchestrator = self._get_agent_by_type("orchestrator")

        if not orchestrator:
            # Simple concatenation if no orchestrator
            return {
                "content": "Multiple agents processed your request.",
                "agent_results": results,
                "synthesized": False,
            }

        # Enhanced synthesis with better structuring
        synthesis_prompt = f"""
        Synthesize the following agent responses into a coherent, helpful response:
        
        Agent Results: {results}
        
        Instructions:
        1. Identify the main request from the user
        2. Extract key insights from each agent's response
        3. Combine insights logically and remove redundancies
        4. Structure the response clearly with sections if needed
        5. Ensure the response directly addresses the user's request
        6. Add confidence indicators where appropriate
        
        Provide a unified, comprehensive response that incorporates insights from all agents.
        """

        messages = [
            {"role": "system", "content": self.groq_service._get_orchestrator_prompt()},
            {"role": "user", "content": synthesis_prompt},
        ]

        synthesis = self.groq_service.chat_completion(messages)

        return {
            "content": synthesis.get("content", "Error synthesizing responses"),
            "agent_results": results,
            "synthesized": True,
            "orchestrator": orchestrator.name,
        }

    def _send_response_to_session(
        self, response: dict[str, Any], original_message: Message
    ):
        """Send response back to the session via WebSocket"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"session_{self.session.id}",
            {
                "type": "agent_response",
                "response": response,
                "original_message_id": str(original_message.id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _get_agent_by_type(self, agent_type: str) -> Agent | None:
        """Get agent by type from session"""
        return self.session.agents.filter(type=agent_type, is_active=True).first()

    def _execute_orchestrator_task(self, task: Task) -> dict[str, Any]:
        """Execute orchestrator-specific task"""
        input_data = task.input_data

        response = self.groq_service.generate_agent_response(
            "orchestrator",
            {"session_context": self.session.context},
            input_data.get("content", ""),
        )

        return {
            "response": response,
            "agent_type": "orchestrator",
            "coordination_actions": [],
        }

    def _execute_vision_task(self, task: Task) -> dict[str, Any]:
        """Execute vision-specific task"""
        input_data = task.input_data
        file_path = input_data.get("file_path")

        if file_path:
            vision_result = self.vision_service.analyze_image(file_path)
        else:
            vision_result = {"error": "No image file provided"}

        # Enhance with Groq analysis
        groq_response = self.groq_service.generate_agent_response(
            "vision",
            {"vision_analysis": vision_result},
            input_data.get("content", "Analyze this visual content"),
        )

        return {
            "vision_analysis": vision_result,
            "groq_analysis": groq_response,
            "agent_type": "vision",
        }

    def _execute_reasoning_task(self, task: Task) -> dict[str, Any]:
        """Execute reasoning-specific task with enhanced logic"""
        input_data = task.input_data

        # Enhanced reasoning with step-by-step approach
        reasoning_prompt = f"""
        Analyze the following request with structured reasoning:
        
        Request: {input_data.get('content', '')}
        
        Please provide your analysis in the following format:
        1. Problem Statement: Clearly identify what needs to be solved
        2. Key Information: List important facts and context
        3. Approach: Describe your reasoning methodology
        4. Analysis: Provide detailed step-by-step reasoning
        5. Conclusion: Summarize findings and recommendations
        """

        response = self.groq_service.generate_agent_response(
            "reasoning",
            {"session_context": self.session.context, "task_context": input_data},
            reasoning_prompt,
        )

        return {
            "reasoning_response": response,
            "agent_type": "reasoning",
            "reasoning_steps": self._extract_reasoning_steps(response),
        }

    def _execute_action_task(self, task: Task) -> dict[str, Any]:
        """Execute action-specific task"""
        input_data = task.input_data

        # This would integrate with MCP tools and external APIs
        response = self.groq_service.generate_agent_response(
            "action", {"available_tools": []}, input_data.get("content", "")
        )

        return {
            "action_response": response,
            "agent_type": "action",
            "actions_taken": [],
        }

    def _execute_memory_task(self, task: Task) -> dict[str, Any]:
        """Execute memory-specific task"""
        input_data = task.input_data

        # Store/retrieve from agent memory
        memory_operations = self._handle_memory_operations(task)

        response = self.groq_service.generate_agent_response(
            "memory",
            {"memory_context": memory_operations},
            input_data.get("content", ""),
        )

        return {
            "memory_response": response,
            "agent_type": "memory",
            "memory_operations": memory_operations,
        }

    def _execute_generic_task(self, task: Task) -> dict[str, Any]:
        """Execute generic task for custom agent types"""
        input_data = task.input_data

        response = self.groq_service.chat_completion(
            [{"role": "user", "content": input_data.get("content", "")}]
        )

        return {"response": response, "agent_type": task.assigned_agent.type}

    def _calculate_task_priority(self, agent: Agent, message: Message) -> int:
        """Calculate task priority based on agent type and message"""
        base_priority = {
            "orchestrator": 10,
            "vision": 8,
            "reasoning": 7,
            "action": 6,
            "memory": 5,
        }

        priority = base_priority.get(agent.type, 5)

        # Adjust based on message type and urgency indicators
        content = message.content.lower()
        urgency_indicators = ["urgent", "asap", "immediately", "now", "quick"]
        if any(indicator in content for indicator in urgency_indicators):
            priority += 2

        if message.message_type == "image" and agent.type == "vision":
            priority += 2
        elif message.message_type == "audio" and agent.type == "vision":
            priority += 1

        # Cap priority at 10
        return min(priority, 10)

    def _notify_task_completion(self, task: Task, result: dict[str, Any]):
        """Notify about task completion via WebSocket"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"session_{self.session.id}",
            {
                "type": "task_completed",
                "task_id": str(task.id),
                "agent_name": task.assigned_agent.name,
                "status": task.status,
                "result": result,
            },
        )

    def _extract_reasoning_steps(self, response: dict[str, Any]) -> list[str]:
        """Extract reasoning steps from response"""
        content = response.get("content", "")
        # Simple extraction - could be enhanced with NLP
        steps = [
            line.strip()
            for line in content.split("\n")
            if line.strip().startswith(("1.", "2.", "3.", "-", "*"))
        ]
        return steps

    def _handle_memory_operations(self, task: Task) -> dict[str, Any]:
        """Handle memory storage and retrieval operations against session context."""
        input_data = task.input_data
        content: str = input_data.get("content", "")
        content_lower = content.lower()

        stored_items: list = []
        retrieved_items: list = []
        memory_updates: list = []

        # ── Retrieve existing memory from session context ─────────────────────
        session_memory: dict[str, Any] = self.session.context.get("agent_memory", {})

        # ── Store: detect save/remember intent ────────────────────────────────
        store_triggers = ("remember", "store", "save", "note that", "keep in mind")
        if any(t in content_lower for t in store_triggers):
            # Key by a short timestamp-based label so entries don't overwrite each other
            from django.utils import timezone as tz

            key = f"mem_{tz.now().strftime('%Y%m%d_%H%M%S')}"
            session_memory[key] = content
            stored_items.append({"key": key, "value": content[:200]})
            memory_updates.append(f"stored: {key}")

        # ── Retrieve: detect recall intent ────────────────────────────────────
        recall_triggers = (
            "recall",
            "what do you know",
            "what did i",
            "retrieve",
            "history",
            "remember when",
        )
        if any(t in content_lower for t in recall_triggers):
            # Return all stored memory entries
            for k, v in session_memory.items():
                retrieved_items.append({"key": k, "value": str(v)[:300]})

        # ── Always surface the last 5 recent session messages as context ──────
        from ..models import Message

        recent_messages = (
            Message.objects.filter(session=self.session)
            .order_by("-created_at")[:5]
            .values("role", "content", "created_at")
        )
        for msg in recent_messages:
            retrieved_items.append(
                {
                    "key": f"msg_{msg['created_at'].strftime('%Y%m%d_%H%M%S')}",
                    "value": f"[{msg['role']}] {str(msg['content'])[:200]}",
                }
            )

        # ── Persist updated memory back to session ────────────────────────────
        if stored_items:
            self.session.context["agent_memory"] = session_memory
            self.session.save(update_fields=["context"])

        return {
            "stored_items": stored_items,
            "retrieved_items": retrieved_items,
            "memory_updates": memory_updates,
        }

    def _process_text_message(self, message: Message) -> dict[str, Any]:
        """Process text-only message"""
        return {
            "content": message.content,
            "analysis": "Text message processed",
            "sentiment": "neutral",  # Could be enhanced with sentiment analysis
            "entities": [],  # Could be enhanced with NER
        }

    def _get_combined_analysis(
        self, results: dict[str, Any], content: str
    ) -> dict[str, Any]:
        """Get combined analysis from reasoning agent"""
        reasoning_prompt = f"""
        Analyze and combine the following multimodal processing results:
        
        Results: {results}
        Original Content: {content}
        
        Provide comprehensive insights and actionable conclusions.
        """

        messages = [
            {"role": "system", "content": self.groq_service._get_reasoning_prompt()},
            {"role": "user", "content": reasoning_prompt},
        ]

        return self.groq_service.chat_completion(messages)

    def _orchestrate_final_response(
        self, results: dict[str, Any], message: Message
    ) -> dict[str, Any]:
        """Orchestrate final response combining all analyses"""
        orchestration_prompt = f"""
        Create a comprehensive response based on the following multimodal analysis:
        
        Analysis Results: {results}
        Original Message: {message.content}
        Message Type: {message.message_type}
        
        Provide a helpful, actionable response that addresses the user's needs.
        """

        messages = [
            {"role": "system", "content": self.groq_service._get_orchestrator_prompt()},
            {"role": "user", "content": orchestration_prompt},
        ]

        return self.groq_service.chat_completion(messages)
