import json
import logging
from datetime import datetime, timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Agent, Message, Session

# Get the custom user model
User = get_user_model()

logger = logging.getLogger(__name__)


class AgentPresenceTracker:
    """Track online agents and their status"""

    def __init__(self):
        self.online_agents = (
            {}
        )  # {agent_id: {'channel_name': ..., 'status': ..., 'last_seen': ...}}

    def agent_online(self, agent_id, channel_name):
        """Mark agent as online"""
        self.online_agents[agent_id] = {
            "channel_name": channel_name,
            "status": "available",
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }

    def agent_offline(self, agent_id):
        """Mark agent as offline"""
        if agent_id in self.online_agents:
            del self.online_agents[agent_id]

    def update_status(self, agent_id, status):
        """Update agent status"""
        if agent_id in self.online_agents:
            self.online_agents[agent_id]["status"] = status
            self.online_agents[agent_id]["last_seen"] = datetime.now(
                timezone.utc
            ).isoformat()

    def get_online_agents(self):
        """Get list of online agents"""
        return list(self.online_agents.keys())

    def is_online(self, agent_id):
        """Check if agent is online"""
        return agent_id in self.online_agents


# Global presence tracker
presence_tracker = AgentPresenceTracker()


class SessionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for session-based communication with real-time coordination"""

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.session_group_name = f"session_{self.session_id}"

        print(f"DEBUG: WebSocket connection attempt for session: {self.session_id}")
        print(f"DEBUG: Group name: {self.session_group_name}")

        # Ensure session exists with default agents
        session = await self.ensure_session_exists()
        print(f"DEBUG: Session ensured: {session.id if session else 'None'}")

        # Join session group
        await self.channel_layer.group_add(self.session_group_name, self.channel_name)

        await self.accept()
        print(f"DEBUG: WebSocket connection accepted for session: {self.session_id}")

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "session_id": self.session_id,
                    "message": "Connected to session",
                }
            )
        )

    async def disconnect(self, close_code):
        # Leave session group
        await self.channel_layer.group_discard(
            self.session_group_name, self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "message")

            logger.info(f"Received message: {data}")
            print(f"DEBUG: Received WebSocket message: {data}")

            if message_type == "chat_message":
                await self.handle_chat_message(data)
            elif message_type == "agent_command":
                await self.handle_agent_command(data)
            elif message_type == "stream_request":
                await self.handle_stream_request(data)
            elif message_type == "ping":
                # Respond to ping with pong
                await self.send(text_data=json.dumps({"type": "pong"}))
            else:
                await self.send_error("Unknown message type")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:  # noqa: BLE001
            logger.error(f"WebSocket receive error: {e!s}")
            await self.send_error(f"Processing error: {e!s}")

    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        content = data.get("content", "")
        user_id = data.get("user_id")
        message_type = data.get("message_type", "text")

        print(f"DEBUG: Processing chat message: content='{content}', user_id={user_id}")

        if not content and message_type == "text":
            await self.send_error("Message content is required")
            return

        # Get session and user
        session = await self.get_session()
        user = await self.get_user(user_id) if user_id else None

        print(f"DEBUG: Session found: {session is not None}")
        if session:
            print(f"DEBUG: Session name: {session['name']}")
            print(f"DEBUG: Session agents count: {session['agents_count']}")

        if not session:
            await self.send_error("Session not found")
            return

        # Create message and get sender info
        message_info = await self.create_message_with_sender_info(
            session, user, content, message_type, data.get("metadata", {})
        )
        message_id = message_info["id"]
        sender_name = message_info["sender"]
        created_at = message_info["created_at"]

        print(f"DEBUG: Message created: {message_id}")

        # Broadcast to session group
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message_id,
                    "content": content,
                    "message_type": message_type,
                    "sender": sender_name,
                    "timestamp": created_at,
                },
            },
        )

        print(f"DEBUG: Message broadcasted to group: {self.session_group_name}")

        # Process with agents (async)
        print("DEBUG: About to call process_with_agents")
        try:
            result = await self.process_with_agents(
                session, message_id, content, self.session_group_name
            )
            print(
                f"DEBUG: process_with_agents completed successfully with result: {result}"
            )
        except Exception as e:  # noqa: BLE001
            print(f"DEBUG: process_with_agents failed with error: {e}")
            import traceback

            traceback.print_exc()

    async def handle_agent_command(self, data):
        """Handle agent-specific commands"""
        command = data.get("command")
        agent_id = data.get("agent_id")

        if command == "activate":
            await self.activate_agent(agent_id)
        elif command == "deactivate":
            await self.deactivate_agent(agent_id)
        elif command == "status":
            await self.get_agent_status(agent_id)
        else:
            await self.send_error(f"Unknown command: {command}")

    async def handle_stream_request(self, data):
        """
        Handle streaming request — sends real token-by-token output from Groq.
        Runs the synchronous Groq streaming generator in a thread-pool so the
        async WebSocket event loop is never blocked.
        """
        content = data.get("content", "") or data.get("message", "")
        model = data.get("model")

        await self.send(
            text_data=json.dumps(
                {
                    "type": "stream_start",
                    "message": "Generating response...",
                }
            )
        )

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        from django.conf import settings

        from .services.groq_service import GroqService

        if not settings.GROQ_API_KEY:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "stream_chunk",
                        "chunk": "Groq API key not configured.",
                        "full_content": "Groq API key not configured.",
                        "done": False,
                    }
                )
            )
            await self.send(
                text_data=json.dumps(
                    {"type": "stream_end", "done": True, "full_content": ""}
                )
            )
            return

        messages_payload = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant in a multi-agent system. "
                    "Format responses using Markdown."
                ),
            },
            {"role": "user", "content": content},
        ]

        groq_service = GroqService()
        full_content = ""
        loop = asyncio.get_event_loop()

        # Collect streaming chunks in a background thread so we don't block the event loop
        def _run_stream():
            chunks = []
            try:
                chunks.extend(
                    list(groq_service.stream_completion(messages_payload, model=model))
                )
            except Exception as exc:  # noqa: BLE001
                chunks.append({"error": str(exc), "content": "", "done": True})
            return chunks

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                chunks = await loop.run_in_executor(executor, _run_stream)

            for chunk in chunks:
                if chunk.get("error"):
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "stream_chunk",
                                "chunk": f"[Error: {chunk['error']}]",
                                "full_content": full_content,
                                "done": False,
                            }
                        )
                    )
                    break

                token = chunk.get("content", "")
                if token:
                    full_content += token
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "stream_chunk",
                                "chunk": token,
                                "full_content": full_content,
                                "done": False,
                            }
                        )
                    )

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "stream_end",
                        "full_content": full_content,
                        "done": True,
                    }
                )
            )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Streaming error: {e}")
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "stream_end",
                        "full_content": full_content,
                        "error": str(e),
                        "done": True,
                    }
                )
            )

    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(
            text_data=json.dumps({"type": "chat_message", "message": event["message"]})
        )

    async def agent_response(self, event):
        """Send agent response to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "agent_response",
                    "response": event["response"],
                    "original_message_id": event.get("original_message_id"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def task_completed(self, event):
        """Send task completion notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_completed",
                    "task_id": event["task_id"],
                    "agent_name": event["agent_name"],
                    "status": event["status"],
                    "result": event["result"],
                }
            )
        )

    async def stream_start(self, event):
        """Handle stream start"""
        await self.send(
            text_data=json.dumps({"type": "stream_start", "message": event["message"]})
        )

    async def stream_update(self, event):
        """Handle stream update"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "stream_chunk",
                    "chunk": event["chunk"],
                    "full_content": event["full_content"],
                    "done": False,
                }
            )
        )

    async def stream_end(self, event):
        """Handle stream end"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "stream_end",
                    "full_content": event.get("full_content", ""),
                    "done": True,
                }
            )
        )

    # Helper methods
    async def send_error(self, error_message):
        """Send error message"""
        await self.send(
            text_data=json.dumps({"type": "error", "message": error_message})
        )

    @database_sync_to_async
    def ensure_session_exists(self):
        """Ensure session exists with default agents"""
        try:
            # Try to get session by ID if it's a valid UUID
            import uuid as uuid_module

            try:
                session_uuid = uuid_module.UUID(self.session_id)
                session = Session.objects.get(id=session_uuid)
                return session
            except ValueError:
                # If session_id is not a valid UUID, try to find by name or create new
                pass

            # Try to find session by name for string IDs
            try:
                session = Session.objects.get(name=self.session_id)
                return session
            except Session.DoesNotExist:
                pass

        except Session.DoesNotExist:
            pass

        # Create new session with proper UUID
        import uuid as uuid_module

        # User is already imported at the top of the file

        # Get or create a default user for WebSocket sessions
        # Note: CustomUser uses email as USERNAME_FIELD
        default_user, _ = User.objects.get_or_create(
            email="websocket@example.com",
            defaults={
                "username": "websocket_user",
                "first_name": "WebSocket",
                "last_name": "User",
            },
        )

        session = Session.objects.create(
            name=f"Session {self.session_id}",
            user=default_user,
            context={
                "created_via": "websocket",
                "original_session_id": self.session_id,
            },
        )

        # Create default agents for this session — reuse platform agents, don't duplicate
        default_agent_names = [
            "Master Orchestrator",
            "Vision Analyst",
            "Logic Engine",
            "Action Executor",
        ]
        existing_agents = list(
            Agent.objects.filter(name__in=default_agent_names, is_active=True)[:4]
        )

        if not existing_agents:
            default_agents = [
                {
                    "name": "Master Orchestrator",
                    "type": "orchestrator",
                    "capabilities": [
                        "task_coordination",
                        "agent_management",
                        "workflow_optimization",
                    ],
                },
                {
                    "name": "Vision Analyst",
                    "type": "vision",
                    "capabilities": [
                        "image_analysis",
                        "object_detection",
                        "visual_reasoning",
                    ],
                },
                {
                    "name": "Logic Engine",
                    "type": "reasoning",
                    "capabilities": [
                        "logical_reasoning",
                        "problem_solving",
                        "analysis",
                    ],
                },
            ]
            for agent_data in default_agents:
                agent = Agent.objects.create(
                    name=agent_data["name"],
                    type=agent_data["type"],
                    capabilities=agent_data["capabilities"],
                    owner=default_user,
                    is_active=True,
                    status="idle",
                )
                existing_agents.append(agent)
        else:
            for agent in existing_agents:
                session.agents.add(agent)
            return session

        for agent in existing_agents:
            session.agents.add(agent)

        return session

    @database_sync_to_async
    def get_session(self):
        """Get session from database with eager loaded data"""
        try:
            # Try UUID first
            import uuid as uuid_module

            try:
                session_uuid = uuid_module.UUID(self.session_id)
                session = Session.objects.prefetch_related("agents").get(
                    id=session_uuid
                )
                return {
                    "id": str(session.id),
                    "name": session.name,
                    "user_id": str(session.user_id),
                    "agents_count": session.agents.count(),
                    "is_active": session.is_active,
                    "context": session.context,
                    "session_obj": session,  # Keep reference for later use
                }
            except ValueError:
                # Fall back to name lookup for string IDs
                pass

            # Try to find session by name for string IDs
            try:
                session = Session.objects.prefetch_related("agents").get(
                    name=self.session_id
                )
                return {
                    "id": str(session.id),
                    "name": session.name,
                    "user_id": str(session.user_id),
                    "agents_count": session.agents.count(),
                    "is_active": session.is_active,
                    "context": session.context,
                    "session_obj": session,
                }
            except Session.DoesNotExist:
                pass

            # Try to find by original session ID in context
            try:
                session = Session.objects.prefetch_related("agents").get(
                    context__original_session_id=self.session_id
                )
                return {
                    "id": str(session.id),
                    "name": session.name,
                    "user_id": str(session.user_id),
                    "agents_count": session.agents.count(),
                    "is_active": session.is_active,
                    "context": session.context,
                    "session_obj": session,
                }
            except Session.DoesNotExist:
                pass

        except Session.DoesNotExist:
            pass

        return None

    @database_sync_to_async
    def get_user(self, user_id):
        """Get user from database"""
        try:
            user = User.objects.get(id=user_id)
            return {"id": str(user.id), "username": user.username, "email": user.email}
        except User.DoesNotExist:
            return None
            return None

    @database_sync_to_async
    def create_message_with_sender_info(
        self, session, user, content, message_type, metadata
    ):
        """Create message in database and return serialized info"""
        # Get the actual session object if it's a dict
        if isinstance(session, dict):
            session_obj = session["session_obj"]
        else:
            session_obj = session

        # Get user object if it's a dict
        user_obj = None
        if user and isinstance(user, dict):
            user_id = user["id"]
            user_obj = User.objects.get(id=user_id)
        elif user:
            user_obj = user

        message = Message.objects.create(
            session=session_obj,
            sender=user_obj,
            content=content,
            message_type=message_type,
            metadata=metadata,
        )

        return {
            "id": str(message.id),
            "sender": user_obj.username if user_obj else "Anonymous",
            "created_at": message.created_at.isoformat(),
        }

    async def process_with_agents(
        self, session_data, message_id, message_content, group_name
    ):
        """
        Process message through the full multi-agent orchestration pipeline.
        Routes through LangchainAgentCoordinator (ReAct loop) for real agent reasoning,
        then sends the response back over WebSocket.
        """
        from django.conf import settings

        from .services.groq_service import GroqService

        if not settings.GROQ_API_KEY:
            await self._async_send_fallback_response(
                message_id, group_name, "Groq API key not configured"
            )
            return {"status": "fallback", "reason": "no_api_key"}

        try:
            # ── Run the full agent coordinator in a thread (it's sync Django ORM) ──
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def _run_coordinator():
                import uuid as uuid_module

                from .models import Message as AgentMessage
                from .models import Session
                from .services.langchain_coordinator import LangchainAgentCoordinator

                try:
                    session_uuid = uuid_module.UUID(session_data["id"])
                    session_obj = Session.objects.get(id=session_uuid)
                except Exception:  # noqa: BLE001
                    # Fallback to simple Groq call if session can't be loaded
                    return None, None

                # Get the message object
                try:
                    msg_uuid = uuid_module.UUID(message_id)
                    message_obj = AgentMessage.objects.get(id=msg_uuid)
                except Exception:  # noqa: BLE001
                    return None, None

                coordinator = LangchainAgentCoordinator(session_obj)
                result = coordinator.process_message(message_obj)
                return result, None

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                result, _ = await loop.run_in_executor(executor, _run_coordinator)

            if result is None:
                # Coordinator failed — fall back to direct Groq call
                raise RuntimeError("Coordinator returned None")

            # Extract final response content
            response_data = result.get("response", result)
            if isinstance(response_data, dict):
                response_content = (
                    response_data.get("content")
                    or response_data.get("message")
                    or str(response_data)
                )
            else:
                response_content = str(response_data)

            agent_name = (
                result.get("agents_involved", ["Orchestrator"])[0]
                if result.get("agents_involved")
                else "Orchestrator"
            )
            agent_id = await self.get_first_active_agent_id(session_data["id"])

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Full coordinator failed, using direct Groq: {e}")
            # Direct Groq fallback
            try:
                groq_service = GroqService()
                agent_name = (
                    await self.get_first_active_agent(session_data["id"])
                    or "Master Orchestrator"
                )
                messages_history = [
                    {
                        "role": "system",
                        "content": (
                            f"You are {agent_name}, a helpful AI assistant in a multi-agent system. "
                            "Format responses using Markdown with headers, bullet points, and code blocks."
                        ),
                    },
                    {"role": "user", "content": message_content},
                ]
                groq_response = groq_service.chat_completion(messages_history)
                response_content = groq_response.get(
                    "content", "Unable to process request."
                )
                agent_id = await self.get_first_active_agent_id(session_data["id"])
            except Exception as e2:  # noqa: BLE001
                await self._async_send_fallback_response(
                    message_id, group_name, str(e2)
                )
                return {"status": "error", "error": str(e2)}

        await self.channel_layer.group_send(
            group_name,
            {
                "type": "agent_response",
                "response": {
                    "content": response_content,
                    "synthesized": True,
                    "orchestrator": agent_name,
                    "agent_id": agent_id,
                },
                "original_message_id": message_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return {"status": "processed", "agent": agent_name}

    async def _async_send_fallback_response(self, message_id, group_name, reason):
        """Send a fallback response when API is not available"""
        fallback_content = f"I received your message. However, I'm currently running in limited mode ({reason}). Please configure the GROQ_API_KEY environment variable for full AI capabilities."

        await self.channel_layer.group_send(
            group_name,
            {
                "type": "agent_response",
                "response": {
                    "content": fallback_content,
                    "synthesized": False,
                    "orchestrator": "System",
                    "fallback": True,
                },
                "original_message_id": message_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _async_send_error_response(self, message_id, group_name, error):
        """Send an error response"""
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "agent_response",
                "response": {
                    "content": f"I encountered an issue processing your request. Error: {error}",
                    "synthesized": False,
                    "orchestrator": "System",
                    "error": True,
                },
                "original_message_id": message_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @database_sync_to_async
    def get_first_active_agent(self, session_id):
        """Get the name of the first active agent for a session"""
        try:
            session = Session.objects.get(id=session_id)
            agent = session.agents.filter(is_active=True).first()
            return agent.name if agent else None
        except Session.DoesNotExist:
            return None

    @database_sync_to_async
    def get_first_active_agent_id(self, session_id):
        """Get the ID of the first active agent for a session"""
        try:
            session = Session.objects.get(id=session_id)
            agent = session.agents.filter(is_active=True).first()
            return str(agent.id) if agent else None
        except Session.DoesNotExist:
            return None

    @database_sync_to_async
    def activate_agent(self, agent_id):
        """Activate agent"""
        try:
            agent = Agent.objects.get(id=agent_id)
            agent.status = "active"
            agent.save()
            return True
        except Agent.DoesNotExist:
            return False

    @database_sync_to_async
    def deactivate_agent(self, agent_id):
        """Deactivate agent"""
        try:
            agent = Agent.objects.get(id=agent_id)
            agent.status = "idle"
            agent.save()
            return True
        except Agent.DoesNotExist:
            return False

    @database_sync_to_async
    def get_agent_status(self, agent_id):
        """Get agent status"""
        try:
            agent = Agent.objects.get(id=agent_id)
            return {
                "id": str(agent.id),
                "name": agent.name,
                "status": agent.status,
                "type": agent.type,
            }
        except Agent.DoesNotExist:
            return None


class UserConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user-specific notifications"""

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.user_group_name = f"user_{self.user_id}"

        # Join user group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "user_id": self.user_id,
                    "message": "Connected to user notifications",
                }
            )
        )

    async def disconnect(self, close_code):
        # Leave user group
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            # Handle user-specific commands if needed
            pass
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def agent_status_update(self, event):
        """Handle agent status updates"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "agent_status_update",
                    "agent_id": event["agent_id"],
                    "status": event["status"],
                }
            )
        )

    async def notification(self, event):
        """Handle general notifications"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": event["message"],
                    "level": event.get("level", "info"),
                }
            )
        )

    async def send_error(self, error_message):
        """Send error message"""
        await self.send(
            text_data=json.dumps({"type": "error", "message": error_message})
        )


class AgentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for agent-specific monitoring"""

    async def connect(self):
        self.agent_id = self.scope["url_route"]["kwargs"]["agent_id"]
        self.agent_group_name = f"agent_{self.agent_id}"

        # Join agent group
        await self.channel_layer.group_add(self.agent_group_name, self.channel_name)

        await self.accept()

        # Send agent info
        agent_info = await self.get_agent_info()
        if agent_info:
            await self.send(
                text_data=json.dumps({"type": "agent_connected", "agent": agent_info})
            )

    async def disconnect(self, close_code):
        # Leave agent group
        await self.channel_layer.group_discard(self.agent_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            # Handle agent-specific commands
            pass
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")

    async def performance_update(self, event):
        """Handle performance metric updates"""
        await self.send(
            text_data=json.dumps(
                {"type": "performance_update", "metrics": event["metrics"]}
            )
        )

    async def task_assigned(self, event):
        """Handle task assignment"""
        await self.send(
            text_data=json.dumps({"type": "task_assigned", "task": event["task"]})
        )

    async def send_error(self, error_message):
        """Send error message"""
        await self.send(
            text_data=json.dumps({"type": "error", "message": error_message})
        )

    @database_sync_to_async
    def get_agent_info(self):
        """Get agent information"""
        try:
            agent = Agent.objects.get(id=self.agent_id)
            return {
                "id": str(agent.id),
                "name": agent.name,
                "type": agent.type,
                "status": agent.status,
                "capabilities": agent.capabilities,
            }
        except Agent.DoesNotExist:
            return None
