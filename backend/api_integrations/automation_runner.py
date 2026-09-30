"""Execute scheduled automations."""

import json
import logging
from datetime import timedelta

from django.utils import timezone

from .registry import IntegrationToolRegistry

logger = logging.getLogger(__name__)


def _groq_summarize(prompt: str) -> str:
    try:
        from agents.services.groq_service import GroqService

        resp = GroqService().chat_completion(
            [
                {
                    "role": "system",
                    "content": "You summarize data concisely for automation alerts.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        return resp.get("content", "No summary generated.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Groq summarize failed: {e}")
        return f"Summary unavailable: {e}"


def run_inbox_digest(automation, user) -> dict:
    max_emails = int(automation.config.get("max_emails", 10))
    fetch = IntegrationToolRegistry.execute(
        "gmail.read_inbox", {"max_results": max_emails}, user=user
    )
    if fetch.get("status") != "success":
        return {
            "status": "error",
            "message": fetch.get("message", "Gmail fetch failed"),
        }

    emails = fetch.get("emails", [])
    summary = _groq_summarize(
        f"Create a daily inbox digest with action items:\n{json.dumps(emails, indent=2)}"
    )

    slack_channel = automation.config.get("slack_channel")
    if slack_channel:
        post = IntegrationToolRegistry.execute(
            "slack.post_message",
            {"channel": slack_channel, "text": f"📬 Daily Inbox Digest\n\n{summary}"},
            user=user,
        )
        return {"status": "success", "summary": summary, "slack": post}

    return {"status": "success", "summary": summary, "emails_count": len(emails)}


def run_slack_alert(automation, user) -> dict:
    channel = automation.config.get("channel") or automation.config.get("slack_channel")
    message = automation.config.get(
        "message", "Scheduled alert from MultiAgent platform"
    )
    if not channel:
        return {"status": "error", "message": "slack channel required in config"}
    result = IntegrationToolRegistry.execute(
        "slack.post_message", {"channel": channel, "text": message}, user=user
    )
    return result


def run_workflow(automation, user) -> dict:
    if not automation.workflow_id:
        return {"status": "error", "message": "No workflow linked"}
    import asyncio

    from agents.services.workflow_engine import WorkflowEngine
    from workflow_builder.models import VisualWorkflow, WorkflowExecution

    try:
        workflow = VisualWorkflow.objects.get(id=automation.workflow_id)
    except VisualWorkflow.DoesNotExist:
        return {"status": "error", "message": "Workflow not found"}

    execution = WorkflowExecution.objects.create(
        workflow=workflow,
        input_data=automation.config,
        status="running",
        started_at=timezone.now(),
    )
    from workflow_builder.views import VisualWorkflowViewSet

    viewset = VisualWorkflowViewSet()
    steps = viewset._convert_nodes_to_steps(workflow.nodes, workflow.edges)
    definition = {
        "id": str(workflow.id),
        "name": workflow.name,
        "steps": steps,
        "variables": workflow.variables,
        "settings": workflow.settings,
    }

    engine = WorkflowEngine()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            engine.execute_workflow(definition, automation.config, str(user.id))
        )
    finally:
        loop.close()

    execution.status = "completed" if result.get("success") else "failed"
    execution.completed_at = timezone.now()
    execution.output_data = result.get("results", {})
    execution.error_message = result.get("error", "")
    execution.save()
    return {
        "status": "success" if result.get("success") else "error",
        "execution_id": str(execution.id),
        "result": result,
    }


def run_integration_check(automation, user) -> dict:
    from .models import APIIntegration

    results = []
    for integ in APIIntegration.objects.filter(created_by=user, status="active"):
        test = IntegrationToolRegistry.test_integration(integ)
        results.append({"integration": integ.name, **test})
    failures = [r for r in results if r.get("status") != "success"]
    if failures and automation.config.get("slack_channel"):
        IntegrationToolRegistry.execute(
            "slack.post_message",
            {
                "channel": automation.config["slack_channel"],
                "text": f"⚠️ Integration health check: {len(failures)} failure(s)\n"
                + "\n".join(
                    f"- {f['integration']}: {f.get('message')}" for f in failures
                ),
            },
            user=user,
        )
    return {
        "status": "success",
        "checked": len(results),
        "failures": len(failures),
        "details": results,
    }


def run_automation(automation) -> dict:
    user = automation.user
    runners = {
        "inbox_digest": run_inbox_digest,
        "slack_alert": run_slack_alert,
        "workflow_run": run_workflow,
        "integration_check": run_integration_check,
    }
    runner = runners.get(automation.automation_type)
    if not runner:
        return {
            "status": "error",
            "message": f"Unknown automation type: {automation.automation_type}",
        }
    try:
        result = runner(automation, user)
        automation.last_result = result
        automation.last_run_at = timezone.now()
        automation.next_run_at = compute_next_run(automation)
        automation.save(update_fields=["last_result", "last_run_at", "next_run_at"])
        return result
    except Exception as e:
        logger.exception(f"Automation {automation.id} failed")
        automation.last_result = {"status": "error", "message": str(e)}
        automation.last_run_at = timezone.now()
        automation.next_run_at = compute_next_run(automation)
        automation.save(update_fields=["last_result", "last_run_at", "next_run_at"])
        return {"status": "error", "message": str(e)}


def compute_next_run(automation) -> timezone.datetime:
    now = timezone.now()
    if automation.frequency == "hourly":
        return now + timedelta(hours=1)
    if automation.frequency == "daily":
        return now + timedelta(days=1)
    if automation.frequency == "weekly":
        return now + timedelta(weeks=1)
    return now + timedelta(days=1)
