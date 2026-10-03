from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class DLQTask(Task):
    """
    Custom base task that routes failed tasks to a Dead Letter Queue (DLQ).
    Redis does not natively support AMQP DLXs, so we implement it via `on_failure`.
    """

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            f"Task {self.name}[{task_id}] failed. Sending to DLQ. "
            f"Exception: {exc}\nArgs: {args}\nKwargs: {kwargs}"
        )

        # We trigger another task specifically bound to the DLQ queue.
        # This acts as our dead-letter sink.
        from .celery import app

        app.send_task(
            "backend.tasks.process_dlq_message",
            args=[self.name, task_id, str(args), str(kwargs), str(exc)],
            queue="dlq",
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)


from .celery import app


@app.task(queue="dlq", ignore_result=True)
def process_dlq_message(
    original_task_name, original_task_id, args_str, kwargs_str, exc_str
):
    """
    This task receives messages that failed their main processing.
    In a real system, you might store these in a DB table for manual replay.
    """
    logger.warning(
        f"[DLQ] Received failed task {original_task_name}[{original_task_id}].\n"
        f"Exception: {exc_str}"
    )


@app.task(base=DLQTask, bind=True, ignore_result=True)
def failing_dlq_task(self):
    """A test task that will intentionally fail and route to the DLQ."""
    raise ValueError("Intentional failure to test DLQ routing")
