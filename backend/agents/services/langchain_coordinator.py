import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from django.conf import settings
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from .. import models
from ..models import Message
from .enhanced_agent_coordinator import EnhancedAgentCoordinator
from .groq_service import GroqService

logger = logging.getLogger(__name__)


def _invoke_agent_via_groq(agent_type: str, task: str, context: str = "") -> str:
    """
    Helper: calls Groq API with the correct agent system prompt and returns the raw text response.
    This is the real execution that makes agents actually DO something.
    """
    from groq import Groq

    agent_prompts = {
        "orchestrator": (
            "You are an Orchestrator Agent. Your job is to analyse requests, decompose them "
            "into subtasks, coordinate specialist agents, and synthesise their outputs into a "
            "single coherent answer. Think step-by-step and be explicit about your reasoning."
        ),
        "reasoning": (
            "You are a Reasoning Agent. Apply rigorous logical analysis, break problems into "
            "clear steps, and show every inference. Always justify your conclusions."
        ),
        "vision": (
            "You are a Vision Agent. Analyse visual content, describe images in detail, "
            "extract text (OCR), detect objects, and reason about visual patterns."
        ),
        "action": (
            "You are an Action Agent. Execute concrete tasks, call external tools, "
            "perform operations, and report results precisely. Be specific and actionable."
        ),
        "memory": (
            "You are a Memory Agent. Retrieve, store, and organise contextual information. "
            "Summarise what you know and flag gaps that need filling."
        ),
    }

    system_prompt = agent_prompts.get(
        agent_type, "You are a specialised AI assistant. Be helpful and precise."
    )

    messages_payload = [{"role": "system", "content": system_prompt}]
    if context:
        messages_payload.append({"role": "user", "content": f"Context:\n{context}\n\nTask:\n{task}"})
    else:
        messages_payload.append({"role": "user", "content": task})

    client = Groq(api_key=settings.GROQ_API_KEY)
    model = settings.GROQ_CONFIG.get("MODEL", "llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        messages=messages_payload,
        model=model,
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────────────────────────────────────
# Real tools for LangChain AgentExecutor
# ─────────────────────────────────────────────────────────────────────────────

@tool
def send_message_to_agent(agent_id: str, content: str, task_id: str | None = None) -> dict[str, Any]:
    """
    Send a message to a specific agent and receive their actual response.
    The agent will process the content using its specialised Groq-powered LLM and return a real answer.
    """
    try:
        from .. import models as agent_models

        # Resolve agent type from DB so we use the right system prompt
        try:
            agent = agent_models.Agent.objects.get(id=agent_id)
            agent_type = str(agent.type)
        except Exception:  # noqa: BLE001
            agent_type = "orchestrator"

        # Actually invoke the agent
        agent_response = _invoke_agent_via_groq(agent_type, content)

        # Persist result to task output_data if task_id provided
        if task_id:
            try:
                task = agent_models.Task.objects.get(id=task_id)
                existing = task.output_data or {}
                existing[f"agent_{agent_id}_response"] = agent_response
                task.output_data = existing
                task.save(update_fields=["output_data"])
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to update task output data: {e}")

        return {
            "status": "success",
            "agent_id": agent_id,
            "agent_type": agent_type,
            "response": agent_response,
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"Failed to communicate with agent: {e!s}"}

@tool
def execute_agent_task(agent_type: str, task_description: str, context_json: str = "{}") -> dict[str, Any]:
    """
    Execute a task using a named specialist agent (orchestrator / vision / reasoning / action / memory).
    The agent is powered by Groq LLM and returns a REAL response — not a stub.
    Use this to delegate work to the right specialist and get their actual analysis back.
    context_json: optional JSON string with extra context (e.g. previous results).
    """
    try:
        ctx = json.loads(context_json) if context_json else {}
        context_str = json.dumps(ctx, indent=2) if ctx else ""
        result = _invoke_agent_via_groq(agent_type, task_description, context_str)
        return {
            "status": "success",
            "agent_type": agent_type,
            "result": result,
            "task": task_description,
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e), "agent_type": agent_type}


@tool
def search_memory(query: str, session_id: str = "", agent_id: str = "") -> dict[str, Any]:
    """
    Search the persistent agent memory for context relevant to a query.
    Returns the top matching memory entries so the orchestrator can incorporate prior knowledge.
    """
    try:
        from .. import models as agent_models

        filters: dict[str, Any] = {}
        if session_id:
            filters["session_id"] = session_id
        if agent_id:
            filters["agent_id"] = agent_id

        memories = agent_models.AgentMemory.objects.filter(**filters).order_by(
            "-importance_score", "-accessed_at"
        )[:20]

        query_words = set(query.lower().split())
        scored = []
        for mem in memories:
            val_str = str(mem.value).lower()
            key_str = str(mem.key).lower()
            score = sum(1 for w in query_words if w in val_str or w in key_str)
            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = [
            {
                "key": mem.key,
                "value": mem.value,
                "importance": float(mem.importance_score),
                "relevance_score": score,
            }
            for score, mem in scored[:5]
        ]
        return {"status": "success", "memories": results, "count": len(results)}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e), "memories": []}


@tool
def store_insight(key: str, value: str, session_id: str = "", agent_id: str = "", importance: float = 0.7) -> dict[str, Any]:
    """
    Store an important insight, finding, or intermediate result in agent memory.
    Use this to persist knowledge that should be referenced later in the conversation.
    importance: 0.0–1.0 (higher = more important, retrieved first).
    """
    try:
        from .. import models as agent_models

        create_kwargs: dict[str, Any] = {
            "key": key,
            "value": {"content": value, "timestamp": datetime.now(timezone.utc).isoformat()},
            "importance_score": importance,
        }
        if session_id:
            create_kwargs["session_id"] = session_id
        if agent_id:
            create_kwargs["agent_id"] = agent_id

        memory = agent_models.AgentMemory.objects.create(**create_kwargs)
        return {"status": "success", "memory_id": str(memory.id), "key": key}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}


@tool
def plan_task_decomposition(task_description: str, available_agents: str) -> dict[str, Any]:
    """
    Use LLM to decompose a complex task into ordered subtasks and assign each to the best agent.
    Returns a JSON plan with step, agent_type, subtask, and dependencies.
    Call this before executing multi-step work so each subtask is handled by the right specialist.
    """
    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        model = settings.GROQ_CONFIG.get("MODEL", "llama-3.3-70b-versatile")

        system = (
            'You are a task planning expert. Decompose the task into subtasks and assign each to '
            'the most appropriate agent. Return ONLY valid JSON:\n'
            '{"plan":[{"step":1,"agent_type":"reasoning","subtask":"...","depends_on":[]}],'
            '"reasoning":"why this plan"}'
        )
        messages_payload = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Task: {task_description}\n\nAvailable agents: {available_agents}",
            },
        ]

        resp = client.chat.completions.create(
            messages=messages_payload, model=model, temperature=0.2, max_tokens=512
        )
        content = resp.choices[0].message.content

        try:
            plan = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            plan = json.loads(match.group()) if match else {"plan": [], "reasoning": content}

        return {"status": "success", "decomposition": plan}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}


@tool
def get_agent_status(agent_id: str) -> dict[str, Any]:
    """Get the current status and capabilities of an agent"""
    try:
        try:
            from .. import models as agent_models
            agent = agent_models.Agent.objects.get(id=agent_id)
            return {
                "agent_id": str(agent.id),
                "name": agent.name,
                "type": agent.type,
                "status": agent.status,
                "capabilities": agent.capabilities or [],
                "is_active": agent.is_active
            }
        except Exception:  # noqa: BLE001
            return {"error": f"Agent with ID {agent_id} not found"}
    except Exception:  # noqa: BLE001
        return {"error": f"Agent with ID {agent_id} not found"}

@tool
def update_task_status(task_id: str, status: str, output: str | None = None) -> dict[str, Any]:
    """Update the status of a task"""
    try:
        from .. import models as agent_models
        task = agent_models.Task.objects.get(id=task_id)
        task.status = status
        if output:
            task.output_data = {"result": output}
        task.save()
        return {
            "task_id": str(task.id),
            "status": task.status,
            "updated_at": task.updated_at.isoformat() if hasattr(task, 'updated_at') else datetime.now(timezone.utc).isoformat()
        }
    except Exception:  # noqa: BLE001
        return {"error": f"Task with ID {task_id} not found"}

@tool
def create_subtask(parent_task_id: str, title: str, description: str, assigned_agent_id: str) -> dict[str, Any]:
    """Create a subtask for a parent task"""
    try:
        from .. import models as agent_models
        parent_task = agent_models.Task.objects.get(id=parent_task_id)
        subtask = agent_models.Task.objects.create(
            title=title,
            description=description,
            task_type="subtask",
            priority=parent_task.priority,
            status=agent_models.TaskStatus.PENDING,
            assigned_agent_id=assigned_agent_id,
            created_by=parent_task.created_by,
            session=parent_task.session,
            requirements=parent_task.requirements or {},
            input_data=parent_task.input_data or {}
        )
        return {
            "subtask_id": str(subtask.id),
            "parent_task_id": str(parent_task.id),
            "title": subtask.title,
            "status": subtask.status
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to create subtask: {e!s}"}

@tool
def get_agent_performance(agent_id: str) -> dict[str, Any]:
    """Get performance metrics for an agent"""
    try:
        from .. import models as agent_models
        agent = agent_models.Agent.objects.get(id=agent_id)
        # Get recent performance metrics
        recent_metrics = agent.metrics.all().order_by('-timestamp')[:5]
        metrics_data = [
            {
                "metric_name": metric.metric_name,
                "value": metric.metric_value,
                "timestamp": metric.timestamp.isoformat()
            }
            for metric in recent_metrics
        ]
        return {
            "agent_id": str(agent.id),
            "name": agent.name,
            "metrics": metrics_data
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to retrieve performance metrics: {e!s}"}

@tool
def assign_task_to_agent(task_id: str, agent_id: str) -> dict[str, Any]:
    """Assign a task to a specific agent"""
    try:
        from .. import models as agent_models
        task = agent_models.Task.objects.get(id=task_id)
        agent = agent_models.Agent.objects.get(id=agent_id)
        task.assigned_agent = agent
        task.status = agent_models.TaskStatus.PENDING
        task.save()
        return {
            "task_id": str(task.id),
            "assigned_agent": agent.name,
            "status": "assigned"
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to assign task: {e!s}"}

@tool
def get_task_details(task_id: str) -> dict[str, Any]:
    """Get detailed information about a task"""
    try:
        from .. import models as agent_models
        task = agent_models.Task.objects.get(id=task_id)
        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "assigned_agent": task.assigned_agent.name if task.assigned_agent else None,
            "created_at": task.created_at.isoformat(),
            "input_data": task.input_data or {}
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to get task details: {e!s}"}

class LangchainAgentCoordinator:
    """
    Langchain-based coordinator for managing multi-agent workflows with enhanced collaboration.
    This coordinator implements defined agent roles, communication protocols, and decision-making processes.
    """
    
    def __init__(self, session: 'models.Session'):
        self.session = session
        self.groq_service = GroqService()
        self.enhanced_coordinator = EnhancedAgentCoordinator(session)
        api_key = settings.GROQ_API_KEY or None
        self.llm = ChatGroq(
            temperature=0.7,
            model=settings.GROQ_CONFIG.get('MODEL', 'llama-3.3-70b-versatile'),
            api_key=api_key
        ) if api_key else None
        self.tools = [
            send_message_to_agent,
            execute_agent_task,
            search_memory,
            store_insight,
            plan_task_decomposition,
            get_agent_status,
            update_task_status,
            create_subtask,
            get_agent_performance,
            assign_task_to_agent,
            get_task_details,
        ]
        
    def process_message(self, message: 'models.Message') -> dict[str, Any]:
        """
        Process incoming message using Langchain-based multi-agent coordination
        
        Args:
            message: The message to process
            
        Returns:
            Coordination results
        """
        logger.info(f"Processing message with Langchain coordinator: {message.id}")
        
        # Create a conversation history for context
        conversation_history = self._build_conversation_history(message)
        
        # Determine which agents should handle this message
        relevant_agents = self._determine_relevant_agents(message)
        
        # Create tasks for relevant agents
        tasks = []
        for agent in relevant_agents:
            task = self._create_agent_task(agent, message)
            tasks.append(task)
        
        # Use Langchain to orchestrate the workflow
        workflow_result = self._orchestrate_with_langchain(
            message, relevant_agents, tasks, conversation_history
        )
        
        # Send response back to session
        self._send_response_to_session(workflow_result, message)
        
        return {
            'message_id': str(message.id),
            'agents_involved': [agent.name for agent in relevant_agents],
            'tasks_created': len(tasks),
            'response': workflow_result
        }
    
    def _build_conversation_history(self, message: 'models.Message') -> list[dict[str, Any]]:
        """Build conversation history from previous messages"""
        try:
            from .. import models as agent_models
            recent_messages = agent_models.Message.objects.filter(
                session=self.session
            ).order_by('-created_at')[:10]  # Last 10 messages
            
            history = []
            for msg in reversed(list(recent_messages)):  # Oldest first
                if hasattr(msg, 'sender_agent') and msg.sender_agent:
                    history.append(
                        HumanMessage(content=f"[{msg.sender_agent.name}]: {msg.content}")
                    )
                else:
                    history.append(
                        HumanMessage(content=msg.content)
                    )
            return history
        except Exception:  # noqa: BLE001
            return []
        
        return history
    
    def _determine_relevant_agents(self, message: 'models.Message') -> list['models.Agent']:
        """
        Use an LLM call to decide which specialist agents are needed for this message.
        Falls back to keyword-based selection if LLM is unavailable.
        """
        if not self.llm:
            return self.enhanced_coordinator._determine_relevant_agents_enhanced(message)

        try:
            session_agents = self.session.agents.filter(is_active=True)
            agent_list = [
                f"{a.name} ({a.type}): {', '.join(a.capabilities or [])}"
                for a in session_agents
            ]

            planning_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a task router. Given a user message, decide which specialist "
                        "agent types are needed. Always include 'orchestrator'. Add others ONLY "
                        "when genuinely required.\n"
                        "Available types: orchestrator, vision, reasoning, action, memory.\n"
                        "Return ONLY a JSON array, e.g. [\"orchestrator\",\"reasoning\"]"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User message: {message.content}\n"
                        f"Message type: {message.message_type}\n"
                        f"Available agents:\n" + "\n".join(agent_list)
                    ),
                },
            ]

            response = self.groq_service.chat_completion(
                planning_messages, max_tokens=64, temperature=0.1
            )
            content = response.get("content", "")
            match = re.search(r"\[.*?\]", content, re.DOTALL)
            needed_types: list[str] = json.loads(match.group()) if match else ["orchestrator", "reasoning"]

            relevant_agents = []
            for agent_type in needed_types:
                agent = session_agents.filter(type=agent_type).first()
                if agent and agent not in relevant_agents:
                    relevant_agents.append(agent)

            # Guarantee orchestrator is always present
            if not relevant_agents:
                orchestrator = session_agents.filter(type="orchestrator").first()
                if orchestrator:
                    relevant_agents.append(orchestrator)

            logger.info(f"LLM selected agents: {[a.type for a in relevant_agents]}")
            return relevant_agents

        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM agent planning failed ({e}); falling back to keyword selection")
            return self.enhanced_coordinator._determine_relevant_agents_enhanced(message)
    
    def _create_agent_task(self, agent: 'models.Agent', message: 'models.Message') -> 'models.Task':
        """Create a task for an agent to process a message"""
        return self.enhanced_coordinator._create_agent_task(agent, message)
    
    def _orchestrate_with_langchain(
        self, 
        message: 'models.Message', 
        agents: list['models.Agent'], 
        tasks: list['models.Task'],
        conversation_history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Orchestrate agent workflow using Langchain with defined roles and protocols
        
        Args:
            message: The original message
            agents: List of agents to coordinate
            tasks: List of tasks to execute
            conversation_history: Previous conversation context
            
        Returns:
            Orchestration results
        """
        # Create a system prompt for the orchestrator with defined roles
        system_prompt = self._create_orchestrator_prompt_with_roles(agents, tasks)
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent executor
        try:
            if self.llm is None:
                logger.error("LLM not initialized due to missing API key")
                # Fallback to the enhanced coordinator
                return self.enhanced_coordinator.process_message(message)
            agent_executor = create_tool_calling_agent(self.llm, self.tools, prompt)
            executor = AgentExecutor(
                agent=agent_executor,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,                  # allow real multi-step reasoning
                return_intermediate_steps=True,     # capture tool calls + observations
                early_stopping_method="generate",
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to create agent executor: {e!s}")
            return self.enhanced_coordinator.process_message(message)

        # Build rich input so the LLM can plan before it acts
        agent_list = "\n".join([f"  - {a.name} (type={a.type}, id={a.id})" for a in agents])
        task_list = "\n".join([f"  - [{t.id}] {t.title}: {t.description}" for t in tasks])
        session_id = str(self.session.id)
        # Fetch recent memory to give the LLM prior context
        try:
            from ..models import AgentMemory
            recent_memories = AgentMemory.objects.filter(
                session=self.session
            ).order_by("-importance_score")[:5]
            memory_summary = "\n".join(
                f"  - [{m.key}]: {str(m.value)[:120]}" for m in recent_memories
            ) or "  (none yet)"
        except Exception:  # noqa: BLE001
            memory_summary = "  (unavailable)"

        input_text = (
            f"User message: {message.content}\n"
            f"Message type: {message.message_type}\n\n"
            f"Session ID: {session_id}\n\n"
            f"Available agents:\n{agent_list}\n\n"
            f"Pending tasks:\n{task_list}\n\n"
            f"Recent memory context:\n{memory_summary}\n\n"
            "Instructions:\n"
            "1. Use plan_task_decomposition to create an execution plan first.\n"
            "2. Execute each subtask by calling execute_agent_task with the correct agent_type.\n"
            "3. Use search_memory to retrieve relevant prior knowledge before reasoning.\n"
            "4. Use store_insight to persist important intermediate findings.\n"
            "5. Use send_message_to_agent to get a specialist's perspective when needed.\n"
            "6. Synthesise all results into a coherent final answer for the user."
        )

        # Execute the agentic loop
        try:
            result = executor.invoke({
                "input": input_text,
                "chat_history": conversation_history,
            })
            logger.info("Langchain ReAct orchestration completed successfully")

            # Capture the intermediate reasoning steps for transparency
            steps = result.get("intermediate_steps", [])
            tool_trace = [
                {
                    "tool": action.tool,
                    "input": action.tool_input,
                    "observation": str(obs)[:300],
                }
                for action, obs in steps
            ]

            return {
                "content": result["output"],
                "orchestrated": True,
                "method": "langchain_react_loop",
                "agents_coordinated": len(agents),
                "reasoning_steps": len(steps),
                "tool_trace": tool_trace,
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Langchain orchestration failed: {e!s}")
            # Fallback to enhanced coordinator
            return self.enhanced_coordinator.process_message(message)
    
    def _create_orchestrator_prompt_with_roles(self, agents: list['models.Agent'], tasks: list['models.Task']) -> str:
        """Create a system prompt for the Langchain orchestrator with defined agent roles"""
        # Define agent roles and responsibilities
        agent_roles = {
            "orchestrator": "Master coordinator that decomposes complex tasks, assigns work to specialists, and synthesizes final responses",
            "vision": "Specialist in visual analysis including image description, object detection, and OCR",
            "reasoning": "Expert in logical analysis, problem-solving, and critical thinking",
            "action": "Executor that performs actions, integrates with external systems, and carries out tasks",
            "memory": "Knowledge manager that stores, retrieves, and maintains context and historical information"
        }
        
        # Define communication protocols
        communication_protocols = """
        Communication Protocols:
        1. Always clearly identify the recipient agent when sending messages
        2. Provide complete context when delegating tasks
        3. Acknowledge receipt of messages and task assignments
        4. Report task completion with results
        5. Request clarification when requirements are unclear
        6. Escalate issues that cannot be resolved independently
        """
        
        # Define decision-making processes
        decision_processes = """
        Decision-Making Processes:
        1. Task Analysis: Analyze the complexity and requirements of incoming tasks
        2. Agent Selection: Choose the most suitable agents based on capabilities and performance history
        3. Task Decomposition: Break complex tasks into manageable subtasks when needed
        4. Parallel Processing: Execute independent subtasks concurrently for efficiency
        5. Sequential Processing: Execute dependent tasks in the correct order
        6. Result Validation: Review and validate results from specialized agents
        7. Conflict Resolution: Resolve discrepancies between agent outputs
        8. Confidence Scoring: Assess the reliability of agent responses
        9. Synthesis: Combine insights from multiple agents into a coherent response
        10. Quality Assurance: Ensure completeness and accuracy before finalizing
        11. Learning: Update agent performance metrics based on outcomes
        12. Escalation: Route complex issues to human supervisors when needed
        """
        
        agent_descriptions = []
        for agent in agents:
            agent_type_str = str(agent.type)
            role_description = agent_roles.get(agent_type_str, "Specialized assistant with specific capabilities")
            agent_type_display = agent_type_str
            capabilities_list = agent.capabilities if isinstance(agent.capabilities, list) else []
            capabilities_str = ', '.join(str(cap) for cap in capabilities_list)
            agent_descriptions.append(
                f"- {agent.name} ({agent_type_display}): {role_description}. Capabilities: {capabilities_str}"
            )
        
        task_descriptions = []
        for task in tasks:
            task_descriptions.append(
                f"- {task.title}: {task.description}"
            )
        
        return f"""
        You are an advanced Multi-Agent Orchestrator implementing a sophisticated coordination system.
        
        Agent Roles:
        {chr(10).join(agent_descriptions)}
        
        Communication Protocols:
        {communication_protocols}
        
        Decision-Making Processes:
        {decision_processes}
        
        Current Tasks:
        {chr(10).join(task_descriptions)}
        
        You have access to specialized tools for agent coordination:
        - send_message_to_agent: Communicate directly with specific agents
        - get_agent_status: Check availability and capabilities of agents
        - update_task_status: Track progress of assigned tasks
        - create_subtask: Break complex tasks into manageable subtasks
        - get_agent_performance: Evaluate agent capabilities based on historical performance
        - assign_task_to_agent: Delegate tasks to specific agents
        - get_task_details: Retrieve detailed information about tasks
        
        Your coordination workflow should follow these steps:
        1. Analyze the user request and identify required capabilities
        2. Select appropriate agents based on their roles and capabilities
        3. Decompose complex tasks into subtasks if needed
        4. Assign tasks to agents following the communication protocols
        5. Monitor progress and facilitate agent collaboration
        6. Synthesize results into a coherent, comprehensive response
        7. Ensure quality and completeness before responding to the user
        
        Always provide clear, structured responses that directly address the user's needs.
        Coordinate agents efficiently and ensure all relevant information is considered.
        """
    
    def _resolve_conflicts(self, agent_responses: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Resolve conflicts between agent responses using confidence scoring
        
        Args:
            agent_responses: List of responses from different agents
            
        Returns:
            Resolved response with highest confidence or synthesized response
        """
        if not agent_responses:
            return {"content": "No responses to resolve", "confidence": 0.0}
        
        # If only one response, return it
        if len(agent_responses) == 1:
            return agent_responses[0]
        
        # Calculate confidence scores for each response
        scored_responses = []
        for response in agent_responses:
            # Extract or calculate confidence (default to 0.5 if not provided)
            confidence = response.get("confidence", 0.5)
            # Adjust confidence based on agent performance
            agent_id = response.get("agent_id")
            if agent_id:
                try:
                    from .. import models as agent_models
                    agent = agent_models.Agent.objects.get(id=agent_id)
                    # Get recent performance metrics
                    recent_metrics = agent.metrics.filter(metric_name="accuracy").order_by('-timestamp')[:5]
                    if recent_metrics:
                        avg_accuracy = sum(m.metric_value for m in recent_metrics) / len(recent_metrics)
                        confidence = (confidence + avg_accuracy) / 2
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to update confidence from agent metrics: {e}")  # Use original confidence if we can't get agent metrics
            
            scored_responses.append({
                "response": response,
                "confidence": confidence
            })
        
        # Sort by confidence (highest first)
        scored_responses.sort(key=lambda x: x["confidence"], reverse=True)
        
        # If highest confidence is significantly higher than others, use it
        if len(scored_responses) >= 2 and scored_responses[0]["confidence"] > scored_responses[1]["confidence"] + 0.2:
            return scored_responses[0]["response"]
        
        # Otherwise, synthesize a combined response
        return self._synthesize_responses(scored_responses)
    
    def _synthesize_responses(self, scored_responses: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Synthesize multiple agent responses into a coherent response
        
        Args:
            scored_responses: List of responses with confidence scores
            
        Returns:
            Synthesized response
        """
        if not scored_responses:
            return {"content": "No responses to synthesize", "confidence": 0.0}
        
        # Weight responses by confidence
        total_confidence = sum(sr["confidence"] for sr in scored_responses)
        if total_confidence == 0:
            # Equal weighting if all confidences are zero
            weighted_content = "\n".join(sr["response"].get("content", "") for sr in scored_responses)
            return {"content": weighted_content, "confidence": 0.0}
        
        # Create weighted synthesis
        synthesis_parts = []
        for sr in scored_responses:
            weight = sr["confidence"] / total_confidence
            content = sr["response"].get("content", "")
            if content:
                synthesis_parts.append(f"[{weight:.2f} weight] {content}")
        
        synthesized_content = "\n\nSynthesized response:\n" + "\n".join(synthesis_parts)
        avg_confidence = total_confidence / len(scored_responses)
        
        return {
            "content": synthesized_content,
            "confidence": avg_confidence,
            "synthesized": True,
            "sources": len(scored_responses)
        }
    
    def _send_response_to_session(self, response: dict[str, Any], original_message: Message):
        """Send response back to the session via WebSocket"""
        # Use the enhanced coordinator's method for consistency
        try:
            self.enhanced_coordinator._send_response_to_session(response, original_message)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to send response to session: {e!s}")