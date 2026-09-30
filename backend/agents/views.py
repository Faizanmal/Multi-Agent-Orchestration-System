import json
import logging
import time
import uuid
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Agent,
    AgentMemory,
    AgentStatus,
    Message,
    PerformanceMetric,
    Session,
    Task,
    TaskStatus,
    WorkflowTemplate,
)
from .serializers import (
    AgentMemorySerializer,
    AgentSerializer,
    MessageSerializer,
    PerformanceMetricSerializer,
    SessionSerializer,
    TaskSerializer,
)
from .services.agent_coordinator import AgentCoordinator
from .services.agent_selector import SmartAgentSelector
from .services.analytics_dashboard import AnalyticsDashboard
from .services.groq_service import GroqService
from .services.multimodal_processor import MultiModalProcessor
from .services.performance_tracker import PerformanceTracker
from .services.workflow_engine import WorkflowEngine

# Get the custom user model
User = get_user_model()
logger = logging.getLogger(__name__)

TRANSIENT_ERROR_MARKERS = (
    "timeout",
    "timed out",
    "temporarily unavailable",
    "connection reset",
    "connection aborted",
    "connection refused",
    "network is unreachable",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "rate limit",
    "429",
)


def _is_transient_coordinator_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in TRANSIENT_ERROR_MARKERS)


def _run_coordinator_with_auto_retry(
    coordinator: AgentCoordinator,
    message: Message,
    max_retries: int = 1,
    backoff_seconds: float = 0.75,
):
    """
    Execute coordinator.process_message with transient-failure auto-retry.
    Returns (result, attempts_used, auto_retried).
    """
    attempts_used = 0
    for attempt_index in range(max_retries + 1):
        attempts_used = attempt_index + 1
        try:
            return (
                coordinator.process_message(message),
                attempts_used,
                attempt_index > 0,
            )
        except Exception as exc:
            is_last = attempt_index >= max_retries
            if is_last or not _is_transient_coordinator_error(exc):
                raise
            sleep_for = backoff_seconds * attempts_used
            logger.warning(
                "Transient coordinator failure message_id=%s attempt=%s/%s backoff=%.2fs",
                message.id,
                attempts_used,
                max_retries + 1,
                sleep_for,
            )
            time.sleep(sleep_for)


class AgentViewSet(viewsets.ModelViewSet):
    serializer_class = AgentSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    # Use standard 'pk' lookup_field (model's primary key is UUID 'id') and map URL kwarg 'id'
    lookup_field = "pk"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Agent.objects.none()
        if settings.DEBUG:
            return Agent.objects.all()
        return Agent.objects.filter(owner=self.request.user)

    def get_object(self):
        """Custom object retrieval with verbose diagnostics in DEBUG.

        We are seeing a 404 despite the UUID appearing in the list endpoint. This override
        bypasses any potential queryset filtering quirks and surfaces detailed context.
        """
        # DRF will populate kwargs with lookup_url_kwarg ('id') so fetch that first, fallback to pk
        pk = (
            self.kwargs.get(self.lookup_url_kwarg)
            or self.kwargs.get("pk")
            or self.kwargs.get("id")
        )
        debug_mode = settings.DEBUG
        if debug_mode:
            print("[AgentViewSet.get_object] Incoming lookup:")
            print(f"  lookup_field attr: {self.lookup_field}")
            print(f"  kwargs keys: {list(self.kwargs.keys())}")
            print(f"  raw pk value: {pk}")
            print(f"  pk repr: {pk!r} length={len(str(pk))} type={type(pk)}")
        if not pk:
            raise NotFound("No primary key provided")
        base_qs = Agent.objects.all()
        if debug_mode:
            try:
                total = base_qs.count()
                sample_ids = list(base_qs.values_list("id", flat=True)[:5])
            except Exception as e:  # noqa: BLE001
                total = f"error: {e}"
                sample_ids = []
            print(f"  Total agents in DB: {total}")
            print(f"  Sample first 5 IDs: {sample_ids}")
            # Direct existence via any() materialization to surface anomalies
            materialized = list(base_qs.values_list("id", flat=True))
            direct_membership = pk in [str(x) for x in materialized]
            print(
                f"  Direct membership check (materialized list) => {direct_membership}"
            )
        # Try direct string filter and UUID cast filter
        exists_global = base_qs.filter(id=pk).exists()
        if debug_mode:
            print(f"  ORM filter existence check: {exists_global}")
            if not exists_global:
                # Try coercing to UUID explicitly
                import uuid as _uuid

                try:
                    uuid_obj = _uuid.UUID(str(pk))
                    exists_uuid = base_qs.filter(id=uuid_obj).exists()
                except Exception as e:  # noqa: BLE001
                    exists_uuid = f"error converting to UUID: {e}"
                print(f"  Existence with coerced UUID object: {exists_uuid}")
                # Extra diagnostics: show filter values fetched via IN query
                try:
                    probe = list(
                        base_qs.filter(id__in=[pk]).values_list("id", flat=True)
                    )
                    print(f"  Probe filter(id__in=[pk]) returned: {probe}")
                except Exception as e:  # noqa: BLE001
                    print(f"  Probe filter error: {e}")
                # Manual fallback if membership is True
                if "direct_membership" in locals() and direct_membership:
                    print(
                        "  Anomaly detected: membership True but ORM filter False. Using manual scan fallback."
                    )
                    for obj in base_qs:
                        if str(obj.id) == str(pk):
                            print(
                                "  Manual scan located agent; returning fallback instance."
                            )
                            return obj
        if not exists_global:
            if debug_mode:
                raise NotFound(
                    detail={
                        "detail": "Agent not found in global queryset",
                        "id": pk,
                        "debug": {
                            "global_exists": exists_global,
                            "query_example": f"Agent.objects.filter(id='{pk}')",
                        },
                    }
                )
            raise NotFound("No Agent matches the given query.")
        # Ownership filter only if not debug
        if not debug_mode:
            owned_qs = base_qs.filter(id=pk, owner=self.request.user)
            if not owned_qs.exists():
                raise NotFound("No Agent matches the given query for this user.")
            return owned_qs.first()
        if debug_mode:
            print("  Fetching instance via get(id=pk)...")
        try:
            return base_qs.get(id=pk)
        except Exception as e:
            if debug_mode:
                print(f"  Direct get(id=pk) failed: {e}")
                # Manual fallback scan (already materialized earlier)
                for obj in base_qs:
                    if str(obj.id) == str(pk):
                        print("  Fallback linear scan matched object.")
                        return obj
            raise

    # Diagnostic override to understand why detail lookup returns 404
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        if settings.DEBUG:
            data = serializer.data
            data["_diagnostic"] = {
                "id": str(instance.id),
                "status": instance.status,
                "owner": getattr(instance.owner, "id", None),
            }
            return Response(data)
        return Response(serializer.data)

    def perform_create(self, serializer):
        if not settings.DEBUG and self.request.user.is_authenticated:
            serializer.save(owner=self.request.user)
        else:
            # For development without auth, use first user or create default user
            # Note: CustomUser uses email as USERNAME_FIELD
            default_user, _ = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )
            serializer.save(owner=default_user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None, **kwargs):
        agent = self.get_object()
        agent.status = AgentStatus.ACTIVE
        agent.save()

        # Notify via WebSocket
        channel_layer = get_channel_layer()
        user_id = request.user.id if request.user.is_authenticated else "default"
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "agent_status_update",
                "agent_id": str(agent.id),
                "status": agent.status,
            },
        )

        return Response({"status": "Agent activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None, **kwargs):
        agent = self.get_object()
        agent.status = AgentStatus.IDLE
        agent.save()

        return Response({"status": "Agent deactivated"})

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None, **kwargs):
        agent = self.get_object()
        metrics = PerformanceMetric.objects.filter(agent=agent).order_by("-timestamp")[
            :100
        ]
        serializer = PerformanceMetricSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="raw/(?P<agent_id>[^/.]+)")
    def raw_lookup(self, request, agent_id=None):
        """Direct lookup bypassing get_object for debugging purposes."""
        info = {"requested_id": agent_id}
        try:
            exists = Agent.objects.filter(id=agent_id).exists()
            info["exists"] = exists
            if exists:
                agent = Agent.objects.get(id=agent_id)
                info["name"] = agent.name
                info["status"] = agent.status
                return Response(info)
            return Response(info, status=404)
        except Exception as e:  # noqa: BLE001
            info["error"] = str(e)
            return Response(info, status=500)


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Session.objects.none()
        if settings.DEBUG:
            return Session.objects.all()
        return Session.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Always ensure we have a valid user
        if self.request.user.is_authenticated:
            user = self.request.user
            print(f"DEBUG: Using authenticated user: {user.email} (ID: {user.pk})")
        else:
            # For development without auth, use first user or create default user
            # Note: CustomUser uses email as USERNAME_FIELD
            user, created = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )
            print(
                f"DEBUG: Using default user: {user.email} (ID: {user.pk}, Created: {created})"
            )

        # Verify user exists and has valid ID
        if not user or not user.pk:
            print(f"ERROR: Invalid user - user={user}, pk={user.pk if user else None}")
            raise ValidationError(
                {"user": "Valid user is required to create a session"}
            )

        print(f"DEBUG: About to save session with user_id={user.pk}")
        try:
            session = serializer.save(user=user)
            print(f"DEBUG: Session created successfully: {session.id}")
        except Exception as e:
            print(f"ERROR: Failed to save session: {e}")
            import traceback

            traceback.print_exc()
            raise

    @action(detail=True, methods=["post"])
    def add_agent(self, request, pk=None):
        session = self.get_object()
        agent_id = request.data.get("agent_id")

        try:
            if settings.DEBUG:
                agent = Agent.objects.get(id=agent_id)
            else:
                agent = Agent.objects.get(id=agent_id, owner=request.user)
            session.agents.add(agent)
            return Response({"status": "Agent added to session"})
        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, *args, **kwargs):
        session = self.get_object()
        session_id = str(session.id)
        self.perform_destroy(session)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"session_{session_id}",
            {
                "type": "session_deleted",
                "session_id": session_id,
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        session = self.get_object()
        content = request.data.get("content")
        message_type = request.data.get("type", "text")
        run_id = str(uuid.uuid4())
        started_at = timezone.now()

        if not content or not str(content).strip():
            raise ValidationError({"content": "Message content is required."})

        # Get user for message
        user = request.user if request.user.is_authenticated else None
        if not user and settings.DEBUG:
            # Note: CustomUser uses email as USERNAME_FIELD
            user, _ = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )

        # Create message
        request_metadata = request.data.get("metadata", {})
        if not isinstance(request_metadata, dict):
            request_metadata = {"raw": request_metadata}

        message = Message.objects.create(
            session=session,
            sender=user,
            content=content,
            message_type=message_type,
            metadata={
                **request_metadata,
                "processing": {
                    "run_id": run_id,
                    "status": "started",
                    "source": "session_send_message",
                    "started_at": started_at.isoformat(),
                },
            },
        )

        # Process message with agents
        coordinator = AgentCoordinator(session)
        try:
            result, attempts_used, auto_retried = _run_coordinator_with_auto_retry(
                coordinator=coordinator,
                message=message,
                max_retries=1,
                backoff_seconds=0.75,
            )
            completed_at = timezone.now()
            processing_ms = int((completed_at - started_at).total_seconds() * 1000)
            message.metadata["processing"] = {
                "run_id": run_id,
                "status": "completed",
                "source": "session_send_message",
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "processing_ms": processing_ms,
                "routing": result.get("routing", "unknown"),
                "tasks_created": result.get("tasks_created", 0),
                "agents_involved": result.get("agents_involved", []),
                "attempts_used": attempts_used,
                "auto_retried": auto_retried,
            }
            message.save(update_fields=["metadata"])
        except Exception as exc:
            completed_at = timezone.now()
            processing_ms = int((completed_at - started_at).total_seconds() * 1000)
            logger.exception(
                "Message processing failed run_id=%s session_id=%s message_id=%s",
                run_id,
                session.id,
                message.id,
            )
            message.metadata["processing"] = {
                "run_id": run_id,
                "status": "failed",
                "source": "session_send_message",
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "processing_ms": processing_ms,
                "error_code": (
                    "COORDINATOR_EXECUTION_FAILED_TRANSIENT"
                    if _is_transient_coordinator_error(exc)
                    else "COORDINATOR_EXECUTION_FAILED"
                ),
                "error_message": str(exc)[:300],
                "attempts_used": 2 if _is_transient_coordinator_error(exc) else 1,
                "auto_retried": _is_transient_coordinator_error(exc),
            }
            message.save(update_fields=["metadata"])

        serializer = MessageSerializer(message)
        return Response(
            {
                **serializer.data,
                "processing": message.metadata.get("processing", {}),
            }
        )

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        session = self.get_object()
        messages = session.messages.all().order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Task.objects.none()
        return Task.objects.filter(session__user=self.request.user)

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        task = self.get_object()

        if task.status != TaskStatus.PENDING:
            return Response(
                {"error": "Task is not in pending state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        task.save()

        # Execute task asynchronously
        coordinator = AgentCoordinator(task.session)
        coordinator.execute_task(task)

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        task = self.get_object()

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return Response(
                {"error": "Task cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = TaskStatus.CANCELLED
        task.save()

        return Response({"status": "Task cancelled"})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Message.objects.none()
        if settings.DEBUG:
            # In debug mode, allow filtering by session parameter
            session_id = self.request.query_params.get("session")
            if session_id:
                return Message.objects.filter(session_id=session_id)
            return Message.objects.all()
        return Message.objects.filter(session__user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        agent_response = getattr(self, "agent_response", None)
        if agent_response:
            response_serializer = self.get_serializer(agent_response)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        session_id = self.request.data.get("session_id")

        if not session_id:
            raise ValidationError({"session_id": "This field is required."})

        try:
            if settings.DEBUG:
                session = Session.objects.get(id=session_id)
                # Use default user in debug mode
                # Note: CustomUser uses email as USERNAME_FIELD
                default_user, _ = User.objects.get_or_create(
                    email="default@example.com",
                    defaults={
                        "username": "default_user",
                        "first_name": "Default",
                        "last_name": "User",
                    },
                )
                message = serializer.save(session=session, sender=default_user)

                # Ensure the selected agent is linked to this session
                agent_id = self.request.data.get("agent_id") or (
                    self.request.data.get("metadata") or {}
                ).get("agent_id")
                if agent_id:
                    try:
                        agent = Agent.objects.get(id=agent_id)
                        session.agents.add(agent)
                    except Agent.DoesNotExist:
                        pass

                # Attach integration sub-agents for connected services
                from api_integrations.models import APIIntegration
                from api_integrations.services import ensure_integration_agents

                integ_qs = APIIntegration.objects.filter(status="active")
                if getattr(self.request.user, "is_authenticated", False):
                    integ_qs = integ_qs.filter(created_by=self.request.user)
                for integ in integ_qs[:10]:
                    for sub_agent in ensure_integration_agents(integ):
                        session.agents.add(sub_agent)

                # Process message with agent response in debug mode
                self.agent_response = self.process_with_agent(message)

            else:
                session = Session.objects.get(id=session_id, user=self.request.user)
                message = serializer.save(session=session, sender=self.request.user)

                agent_id = self.request.data.get("agent_id") or (
                    self.request.data.get("metadata") or {}
                ).get("agent_id")
                if agent_id:
                    try:
                        agent = Agent.objects.get(id=agent_id, owner=self.request.user)
                        session.agents.add(agent)
                    except Agent.DoesNotExist:
                        pass

                # Attach integration sub-agents for this user's connected services
                from api_integrations.models import APIIntegration
                from api_integrations.services import ensure_integration_agents

                for integ in APIIntegration.objects.filter(
                    status="active", created_by=self.request.user
                )[:10]:
                    for sub_agent in ensure_integration_agents(integ):
                        session.agents.add(sub_agent)

                # Process message with agent response
                self.agent_response = self.process_with_agent(message)

        except Session.DoesNotExist:
            raise ValidationError({"session_id": "Invalid session ID."})

    def process_with_agent(self, user_message):
        """Process user message and generate agent response"""
        run_id = None
        if isinstance(user_message.metadata, dict):
            run_id = (user_message.metadata.get("processing") or {}).get("run_id")
        run_id = run_id or str(uuid.uuid4())

        try:
            logger.info(
                "Processing message via AgentCoordinator run_id=%s message_id=%s",
                run_id,
                user_message.id,
            )

            from .services.agent_coordinator import AgentCoordinator

            coordinator = AgentCoordinator(user_message.session)

            # This calls GroqService/LLM to process the message and assigns tasks
            result = coordinator.process_message(user_message)

            response_data = result.get("response", {})
            response_content = (
                response_data.get("content") or "Error: No content generated"
            )

            # Create agent response message in DB
            agent_response = Message.objects.create(
                session=user_message.session,
                sender=None,  # Leave sender None for agent responses
                content=response_content,
                message_type="text",
                metadata={
                    "run_id": run_id,
                    "response_to": str(user_message.id),
                    "via": "http_api",
                    "is_agent_response": True,
                    "agent_results": response_data.get("agent_results", {}),
                },
            )

            logger.info(
                "Created agent response run_id=%s response_id=%s",
                run_id,
                agent_response.id,
            )
            return agent_response

        except Exception as e:
            logger.exception(
                "Failed to create agent response run_id=%s message_id=%s",
                run_id,
                user_message.id,
            )

            # Fallback message
            return Message.objects.create(
                session=user_message.session,
                sender=None,
                content=f"Sorry, I encountered an internal error: {e!s}",
                message_type="text",
                metadata={
                    "run_id": run_id,
                    "response_to": str(user_message.id),
                    "via": "http_api",
                    "is_agent_response": True,
                    "error_code": "AGENT_RESPONSE_FALLBACK",
                    "error_message": str(e)[:300],
                },
            )

    @action(detail=False, methods=["get"])
    def runs(self, request):
        """
        List message processing runs with optional filters:
        - status: started|completed|failed
        - run_id: exact run ID
        - error_code: exact error code
        - session_id: session UUID
        - limit: max rows (default 50, max 200)
        """
        qs = self.get_queryset().exclude(metadata__processing__isnull=True)

        status_filter = request.query_params.get("status")
        run_id_filter = request.query_params.get("run_id")
        error_code_filter = request.query_params.get("error_code")
        session_id_filter = request.query_params.get("session_id")
        limit_raw = request.query_params.get("limit", "50")

        try:
            limit = max(1, min(int(limit_raw), 200))
        except (TypeError, ValueError):
            limit = 50

        if status_filter:
            qs = qs.filter(metadata__processing__status=status_filter)
        if run_id_filter:
            qs = qs.filter(metadata__processing__run_id=run_id_filter)
        if error_code_filter:
            qs = qs.filter(metadata__processing__error_code=error_code_filter)
        if session_id_filter:
            qs = qs.filter(session_id=session_id_filter)

        qs = qs.order_by("-created_at")[:limit]
        rows = []
        for message in qs:
            processing = (message.metadata or {}).get("processing", {})
            rows.append(
                {
                    "message_id": str(message.id),
                    "session_id": str(message.session_id),
                    "run_id": processing.get("run_id"),
                    "status": processing.get("status", "unknown"),
                    "routing": processing.get("routing"),
                    "tasks_created": processing.get("tasks_created"),
                    "agents_involved": processing.get("agents_involved", []),
                    "processing_ms": processing.get("processing_ms"),
                    "error_code": processing.get("error_code"),
                    "error_message": processing.get("error_message"),
                    "started_at": processing.get("started_at"),
                    "completed_at": processing.get("completed_at"),
                    "created_at": message.created_at.isoformat(),
                }
            )

        status_counts = {}
        for row in rows:
            status_key = row.get("status", "unknown")
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

        return Response(
            {
                "count": len(rows),
                "status_counts": status_counts,
                "filters": {
                    "status": status_filter,
                    "run_id": run_id_filter,
                    "error_code": error_code_filter,
                    "session_id": session_id_filter,
                    "limit": limit,
                },
                "runs": rows,
            }
        )

    @action(detail=False, methods=["get"])
    def reliability_summary(self, request):
        """
        Reliability rollup for message processing runs.
        Query params:
        - hours: lookback window in hours (default 168 = 7 days)
        """
        hours_raw = request.query_params.get("hours", "168")
        try:
            hours = max(1, min(int(hours_raw), 24 * 90))
        except (TypeError, ValueError):
            hours = 168

        since = timezone.now() - timedelta(hours=hours)
        qs = (
            self.get_queryset()
            .filter(created_at__gte=since)
            .exclude(metadata__processing__isnull=True)
        )

        total_runs = 0
        completed_runs = 0
        failed_runs = 0
        transient_failures = 0
        auto_retried_runs = 0
        auto_retry_recovered_runs = 0
        attempts_total = 0
        slow_runs_over_5s = 0

        for message in qs:
            processing = (message.metadata or {}).get("processing", {})
            status = processing.get("status")
            error_code = processing.get("error_code", "") or ""
            auto_retried = bool(processing.get("auto_retried", False))
            attempts_used = int(processing.get("attempts_used", 1) or 1)
            processing_ms = int(processing.get("processing_ms", 0) or 0)

            total_runs += 1
            attempts_total += attempts_used

            if processing_ms > 5000:
                slow_runs_over_5s += 1

            if status == "completed":
                completed_runs += 1
                if auto_retried:
                    auto_retry_recovered_runs += 1
            elif status == "failed":
                failed_runs += 1

            if auto_retried:
                auto_retried_runs += 1
            if "TRANSIENT" in str(error_code).upper():
                transient_failures += 1

        success_rate = (
            round((completed_runs / total_runs) * 100, 2) if total_runs else 0.0
        )
        failure_rate = round((failed_runs / total_runs) * 100, 2) if total_runs else 0.0
        avg_attempts = round(attempts_total / total_runs, 2) if total_runs else 0.0
        auto_retry_recovery_rate = (
            round((auto_retry_recovered_runs / auto_retried_runs) * 100, 2)
            if auto_retried_runs
            else 0.0
        )
        slow_run_rate = (
            round((slow_runs_over_5s / total_runs) * 100, 2) if total_runs else 0.0
        )

        return Response(
            {
                "window": {
                    "hours": hours,
                    "since": since.isoformat(),
                    "until": timezone.now().isoformat(),
                },
                "totals": {
                    "runs": total_runs,
                    "completed": completed_runs,
                    "failed": failed_runs,
                    "transient_failures": transient_failures,
                    "auto_retried_runs": auto_retried_runs,
                    "auto_retry_recovered_runs": auto_retry_recovered_runs,
                    "slow_runs_over_5s": slow_runs_over_5s,
                },
                "rates": {
                    "success_rate_pct": success_rate,
                    "failure_rate_pct": failure_rate,
                    "auto_retry_recovery_rate_pct": auto_retry_recovery_rate,
                    "slow_run_rate_pct": slow_run_rate,
                    "avg_attempts_per_run": avg_attempts,
                },
            }
        )

    @action(detail=False, methods=["post"])
    def retry_failed(self, request):
        """
        Retry a failed message processing run.
        Accepts either:
        - message_id
        - run_id
        """
        message_id = request.data.get("message_id")
        run_id = request.data.get("run_id")

        if not message_id and not run_id:
            raise ValidationError({"detail": "Provide either message_id or run_id."})

        target_qs = self.get_queryset().exclude(metadata__processing__isnull=True)
        if message_id:
            target_qs = target_qs.filter(id=message_id)
        else:
            target_qs = target_qs.filter(metadata__processing__run_id=run_id)

        # Retry only original user messages, not generated agent replies
        target_qs = target_qs.filter(
            Q(metadata__is_agent_response__isnull=True)
            | Q(metadata__is_agent_response=False)
        )
        message = target_qs.order_by("-created_at").first()
        if not message:
            raise NotFound("Failed run message not found.")

        processing = (message.metadata or {}).get("processing", {})
        if processing.get("status") != "failed":
            raise ValidationError(
                {"detail": "Only runs with failed status can be retried."}
            )

        new_run_id = str(uuid.uuid4())
        retry_started_at = timezone.now()
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        metadata["processing"] = {
            "run_id": new_run_id,
            "status": "started",
            "source": "message_retry_failed",
            "started_at": retry_started_at.isoformat(),
            "retry_of_run_id": processing.get("run_id"),
            "retry_count": int(processing.get("retry_count", 0)) + 1,
        }
        message.metadata = metadata
        message.save(update_fields=["metadata"])

        try:
            coordinator = AgentCoordinator(message.session)
            result, attempts_used, auto_retried = _run_coordinator_with_auto_retry(
                coordinator=coordinator,
                message=message,
                max_retries=1,
                backoff_seconds=0.75,
            )
            retry_completed_at = timezone.now()
            retry_ms = int(
                (retry_completed_at - retry_started_at).total_seconds() * 1000
            )
            message.metadata["processing"] = {
                "run_id": new_run_id,
                "status": "completed",
                "source": "message_retry_failed",
                "started_at": retry_started_at.isoformat(),
                "completed_at": retry_completed_at.isoformat(),
                "processing_ms": retry_ms,
                "retry_of_run_id": processing.get("run_id"),
                "retry_count": metadata["processing"]["retry_count"],
                "routing": result.get("routing", "unknown"),
                "tasks_created": result.get("tasks_created", 0),
                "agents_involved": result.get("agents_involved", []),
                "attempts_used": attempts_used,
                "auto_retried": auto_retried,
            }
            message.save(update_fields=["metadata"])
        except Exception as exc:
            retry_completed_at = timezone.now()
            retry_ms = int(
                (retry_completed_at - retry_started_at).total_seconds() * 1000
            )
            logger.exception(
                "Retry failed run_id=%s message_id=%s",
                new_run_id,
                message.id,
            )
            message.metadata["processing"] = {
                "run_id": new_run_id,
                "status": "failed",
                "source": "message_retry_failed",
                "started_at": retry_started_at.isoformat(),
                "completed_at": retry_completed_at.isoformat(),
                "processing_ms": retry_ms,
                "retry_of_run_id": processing.get("run_id"),
                "retry_count": metadata["processing"]["retry_count"],
                "error_code": (
                    "COORDINATOR_RETRY_FAILED_TRANSIENT"
                    if _is_transient_coordinator_error(exc)
                    else "COORDINATOR_RETRY_FAILED"
                ),
                "error_message": str(exc)[:300],
                "attempts_used": 2 if _is_transient_coordinator_error(exc) else 1,
                "auto_retried": _is_transient_coordinator_error(exc),
            }
            message.save(update_fields=["metadata"])
            raise ValidationError({"detail": "Retry failed", "run_id": new_run_id})

        return Response(
            {
                "status": "retried",
                "message_id": str(message.id),
                "session_id": str(message.session_id),
                "run_id": new_run_id,
                "retry_of_run_id": processing.get("run_id"),
                "processing": message.metadata.get("processing", {}),
            }
        )

    @action(detail=False, methods=["post"])
    def process_multimodal(self, request):
        """Process multimodal input (text, image, audio)"""
        session_id = request.data.get("session_id")
        content = request.data.get("content", "")
        file_attachment = request.FILES.get("file")
        message_type = request.data.get("type", "text")

        try:
            session = Session.objects.get(id=session_id, user=request.user)
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Create message
        message = Message.objects.create(
            session=session,
            sender=request.user,
            content=content,
            message_type=message_type,
            file_attachment=file_attachment,
            metadata=request.data.get("metadata", {}),
        )

        # Process with appropriate agent
        coordinator = AgentCoordinator(session)
        response = coordinator.process_multimodal_message(message)

        return Response(
            {"message": MessageSerializer(message).data, "response": response}
        )


class PerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerformanceMetricSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return PerformanceMetric.objects.none()
        if settings.DEBUG:
            return PerformanceMetric.objects.all()
        return PerformanceMetric.objects.filter(agent__owner=self.request.user)

    @action(detail=False, methods=["get"], url_path="agent/(?P<agent_id>[^/.]+)")
    def agent_performance(self, request, agent_id=None):
        """Get performance metrics for a specific agent"""
        try:
            if settings.DEBUG:
                agent = Agent.objects.get(id=agent_id)
            else:
                agent = Agent.objects.get(id=agent_id, owner=request.user)

            metrics = PerformanceMetric.objects.filter(agent=agent).order_by(
                "-timestamp"
            )[:100]
            serializer = PerformanceMetricSerializer(metrics, many=True)
            return Response(
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "status": agent.status,
                    "metrics": serializer.data,
                }
            )

        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def real_time_metrics(self, request):
        """Get real-time performance metrics for all user's agents"""
        if settings.DEBUG:
            agents = Agent.objects.all()[:20]  # Limit for performance
        else:
            agents = Agent.objects.filter(owner=request.user)

        metrics_data = []

        for agent in agents:
            latest_metrics = PerformanceMetric.objects.filter(agent=agent).order_by(
                "-timestamp"
            )[:10]
            agent_data = {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "status": agent.status,
                "metrics": (
                    PerformanceMetricSerializer(latest_metrics, many=True).data
                    if latest_metrics.exists()
                    else []
                ),
            }
            metrics_data.append(agent_data)

        return Response(metrics_data)


class GroqIntegrationView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    @action(detail=False, methods=["post"])
    def chat_completion(self, request):
        """Direct Groq API chat completion"""
        messages = request.data.get("messages", [])
        model = request.data.get("model", "llama-3.3-70b-versatile")

        groq_service = GroqService()
        response = groq_service.chat_completion(messages, model=model)

        return Response(response)

    @action(detail=False, methods=["post"])
    def stream_completion(self, request):
        """Streaming chat completion"""
        messages = request.data.get("messages", [])
        session_id = request.data.get("session_id")

        try:
            Session.objects.get(id=session_id, user=request.user)
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        groq_service = GroqService()

        # Start streaming response
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"session_{session_id}",
            {"type": "stream_start", "message": "Starting stream..."},
        )

        # This would be handled asynchronously in a real implementation
        groq_service.stream_completion(messages, session_id)

        return Response({"status": "Stream started"})


class AgentMemoryViewSet(viewsets.ModelViewSet):
    serializer_class = AgentMemorySerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return AgentMemory.objects.none()
        return AgentMemory.objects.filter(agent__owner=self.request.user)

    @action(detail=False, methods=["post"])
    def store_memory(self, request):
        """Store a memory for an agent"""
        agent_id = request.data.get("agent_id")
        session_id = request.data.get("session_id")
        key = request.data.get("key")
        value = request.data.get("value")
        importance_score = request.data.get("importance_score", 1.0)

        try:
            agent = Agent.objects.get(id=agent_id, owner=request.user)
            session = Session.objects.get(id=session_id, user=request.user)
        except (Agent.DoesNotExist, Session.DoesNotExist):
            return Response(
                {"error": "Agent or Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        memory, _ = AgentMemory.objects.update_or_create(
            agent=agent,
            session=session,
            key=key,
            defaults={"value": value, "importance_score": importance_score},
        )

        serializer = self.get_serializer(memory)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def retrieve_memories(self, request):
        """Retrieve memories for an agent in a session"""
        agent_id = request.query_params.get("agent_id")
        session_id = request.query_params.get("session_id")

        if not agent_id or not session_id:
            return Response(
                {"error": "agent_id and session_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        memories = (
            self.get_queryset()
            .filter(agent_id=agent_id, session_id=session_id)
            .order_by("-importance_score")[:50]
        )

        serializer = self.get_serializer(memories, many=True)
        return Response(serializer.data)


# Enhanced Views for Advanced Features


class SmartAgentViewSet(viewsets.ViewSet):
    """Enhanced agent management with smart selection and performance tracking."""

    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_selector = SmartAgentSelector()
        self.performance_tracker = PerformanceTracker()

    @action(detail=False, methods=["post"])
    def select_best_agent(self, request):
        """Automatically select the best agent for a given task."""
        task_type = request.data.get("task_type", "")
        task_description = request.data.get("description", "")
        requirements = request.data.get("requirements", {})

        if not task_type:
            return Response(
                {"error": "task_type is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = self.agent_selector.select_best_agent(
                task_type=task_type,
                task_description=task_description,
                requirements=requirements,
            )

            if agent:
                explanation = self.agent_selector.explain_selection(
                    agent, task_type, task_description, requirements
                )

                return Response(
                    {
                        "selected_agent": AgentSerializer(agent).data,
                        "explanation": explanation,
                    }
                )
            else:
                return Response(
                    {"error": "No suitable agent found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def get_agent_recommendations(self, request):
        """Get top N agent recommendations with scores."""
        task_type = request.data.get("task_type", "")
        task_description = request.data.get("description", "")
        count = request.data.get("count", 3)

        if not task_type:
            return Response(
                {"error": "task_type is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            recommendations = self.agent_selector.get_agent_recommendations(
                task_type=task_type, task_description=task_description, count=count
            )

            result = []
            for agent, score in recommendations:
                result.append(
                    {
                        "agent": AgentSerializer(agent).data,
                        "suitability_score": score,
                        "recommendation_reason": f"Score: {score:.3f} - Good match for {task_type} tasks",
                    }
                )

            return Response({"recommendations": result})

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def performance_analysis(self, request, pk=None):
        """Get detailed performance analysis for an agent."""
        try:
            agent = get_object_or_404(Agent, pk=pk)
            days = int(request.query_params.get("days", 30))

            performance_data = self.performance_tracker.get_agent_performance(
                agent_id=str(agent.id), days=days
            )

            recommendations = self.performance_tracker.get_performance_recommendations(
                agent_id=str(agent.id)
            )

            return Response(
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "performance_data": performance_data,
                    "recommendations": recommendations,
                }
            )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WorkflowViewSet(viewsets.ViewSet):
    """Advanced workflow automation and management."""

    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_engine = WorkflowEngine()

    @action(detail=False, methods=["post"])
    def execute_workflow(self, request):
        """Execute a workflow with given definition and input data."""
        workflow_definition = request.data.get("workflow_definition", {})
        input_data = request.data.get("input_data", {})
        session_id = request.data.get("session_id")

        if not workflow_definition:
            return Response(
                {"error": "workflow_definition is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get user ID
            user_id = (
                str(request.user.id) if request.user.is_authenticated else "default"
            )

            # Execute workflow asynchronously
            result = async_to_sync(self.workflow_engine.execute_workflow)(
                workflow_definition=workflow_definition,
                input_data=input_data,
                user_id=user_id,
                session_id=session_id,
            )

            return Response(result)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def workflow_status(self, request):
        """Get the status of a running workflow."""
        workflow_id = request.query_params.get("workflow_id")

        if not workflow_id:
            return Response(
                {"error": "workflow_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            status_data = self.workflow_engine.get_workflow_status(workflow_id)

            if status_data:
                return Response(status_data)
            else:
                return Response(
                    {"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def cancel_workflow(self, request):
        """Cancel a running workflow."""
        workflow_id = request.data.get("workflow_id")

        if not workflow_id:
            return Response(
                {"error": "workflow_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            success = self.workflow_engine.cancel_workflow(workflow_id)

            if success:
                return Response({"status": "Workflow cancelled successfully"})
            else:
                return Response(
                    {"error": "Workflow not found or already completed"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def workflow_templates(self, request):
        """Get available workflow templates."""
        try:
            templates = WorkflowTemplate.objects.filter(is_public=True).order_by(
                "-usage_count"
            )

            # If user is authenticated, include their private templates
            if request.user.is_authenticated:
                user_templates = WorkflowTemplate.objects.filter(
                    created_by=request.user
                ).order_by("-updated_at")
                templates = templates.union(user_templates)

            template_data = []
            for template in templates:
                template_data.append(
                    {
                        "id": str(template.id),
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "tags": template.tags,
                        "usage_count": template.usage_count,
                        "average_rating": template.average_rating,
                        "is_public": template.is_public,
                        "created_at": template.created_at.isoformat(),
                    }
                )

            return Response({"templates": template_data})

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MultiModalProcessorViewSet(viewsets.ViewSet):
    """Advanced multi-modal processing capabilities."""

    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # noqa: RUF012

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processor = MultiModalProcessor()

    @action(detail=False, methods=["post"])
    def process_multimodal(self, request):
        """Process multi-modal input data."""
        try:
            input_data = {}
            processing_options = request.data.get("processing_options", {})

            # Handle text input
            if "text" in request.data:
                input_data["text"] = request.data["text"]

            # Handle file uploads
            for field_name in ["image", "audio", "video", "document"]:
                if field_name in request.FILES:
                    input_data[field_name] = request.FILES[field_name]

            if not input_data:
                return Response(
                    {"error": "No input data provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process the multi-modal input
            result = async_to_sync(self.processor.process_multimodal_input)(
                input_data=input_data, processing_options=processing_options
            )

            return Response(result)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def analyze_text(self, request):
        """Analyze text content with AI."""
        text_content = request.data.get("text", "")
        options = request.data.get("options", {})

        if not text_content:
            return Response(
                {"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = async_to_sync(self.processor._process_text)(
                text_data=text_content, options=options
            )

            return Response(result)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def analyze_image(self, request):
        """Analyze image content with computer vision."""
        if "image" not in request.FILES:
            return Response(
                {"error": "image file is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES["image"]
        options = json.loads(request.data.get("options", "{}"))

        try:
            result = async_to_sync(self.processor._process_image)(
                image_data=image_file, options=options
            )

            return Response(result)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """Advanced analytics and dashboard data."""

    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics = AnalyticsDashboard()

    @action(detail=False, methods=["get"])
    def dashboard_data(self, request):
        """Get comprehensive dashboard analytics."""
        try:
            user_id = str(request.user.id) if request.user.is_authenticated else None
            time_range = request.query_params.get("time_range", "7d")
            include_predictions = (
                request.query_params.get("predictions", "true").lower() == "true"
            )

            result = async_to_sync(self.analytics.get_dashboard_data)(
                user_id=user_id,
                time_range=time_range,
                include_predictions=include_predictions,
            )

            return Response(result)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def system_performance(self, request):
        """Get overall system performance metrics."""
        try:
            days = int(request.query_params.get("days", 7))

            performance_data = (
                self.analytics.performance_tracker.get_system_performance(days=days)
            )

            return Response(performance_data)

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def insights(self, request):
        """Get intelligent insights and recommendations."""
        try:
            user_id = str(request.user.id) if request.user.is_authenticated else None
            days = int(request.query_params.get("days", 30))
            since_date = timezone.now() - timedelta(days=days)

            insights = async_to_sync(self.analytics._generate_insights)(
                user_id=user_id, since_date=since_date
            )

            recommendations = async_to_sync(self.analytics._get_recommendations)(
                user_id=user_id, since_date=since_date
            )

            return Response(
                {
                    "insights": insights,
                    "recommendations": recommendations,
                    "generated_at": timezone.now().isoformat(),
                }
            )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AutomationViewSet(viewsets.ViewSet):
    """Automated task management and scheduling."""

    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def create_automated_task(self, request):
        """Create an automated task with smart agent assignment."""
        try:
            task_data = request.data

            # Validate required fields
            required_fields = ["title", "description", "task_type"]
            for field in required_fields:
                if field not in task_data:
                    return Response(
                        {"error": f"{field} is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Get or create session
            session_id = task_data.get("session_id")
            if session_id:
                try:
                    session = Session.objects.get(id=session_id)
                except Session.DoesNotExist:
                    return Response(
                        {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new session
                user = (
                    request.user
                    if request.user.is_authenticated
                    else User.objects.get(username="default_user")
                )
                session = Session.objects.create(
                    name=f"Auto Session - {task_data['title']}", user=user
                )

            # Smart agent selection
            agent_selector = SmartAgentSelector()
            agent = agent_selector.select_best_agent(
                task_type=task_data["task_type"],
                task_description=task_data["description"],
                requirements=task_data.get("requirements", {}),
            )

            if not agent:
                return Response(
                    {"error": "No suitable agent found for this task"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Create task
            task = Task.objects.create(
                title=task_data["title"],
                description=task_data["description"],
                task_type=task_data["task_type"],
                priority=task_data.get("priority", "normal"),
                assigned_agent=agent,
                created_by=(
                    request.user
                    if request.user.is_authenticated
                    else User.objects.get(username="default_user")
                ),
                session=session,
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
            )

            # Start task processing (in a real implementation, this would be queued)
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = timezone.now()
            task.save()

            return Response(
                {
                    "task": TaskSerializer(task).data,
                    "assigned_agent": AgentSerializer(agent).data,
                    "session": SessionSerializer(session).data,
                    "message": "Task created and assigned automatically",
                }
            )

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def task_suggestions(self, request):
        """Get intelligent task suggestions based on user patterns."""
        try:
            user_id = request.user.id if request.user.is_authenticated else None

            if not user_id:
                return Response({"suggestions": []})

            # Get user's recent tasks to analyze patterns
            recent_tasks = Task.objects.filter(
                created_by_id=user_id,
                created_at__gte=timezone.now() - timedelta(days=30),
            ).order_by("-created_at")[:20]

            # Analyze patterns and generate suggestions
            suggestions = []

            # Most common task types
            task_types = {}
            for task in recent_tasks:
                task_types[task.task_type] = task_types.get(task.task_type, 0) + 1

            # Generate suggestions based on patterns
            for task_type, count in sorted(
                task_types.items(), key=lambda x: x[1], reverse=True
            )[:3]:
                suggestions.append(
                    {
                        "type": "frequent_task_type",
                        "title": f"Create {task_type} task",
                        "description": f"You've created {count} {task_type} tasks recently. Create another?",
                        "suggested_task_type": task_type,
                        "confidence": min(count / 10.0, 1.0),
                    }
                )

            # Time-based suggestions
            current_hour = timezone.now().hour
            if 9 <= current_hour <= 17:  # Business hours
                suggestions.append(
                    {
                        "type": "time_based",
                        "title": "Daily productivity task",
                        "description": "Start your productive day with a focused task",
                        "suggested_task_type": "productivity",
                        "confidence": 0.7,
                    }
                )

            return Response({"suggestions": suggestions})

        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
