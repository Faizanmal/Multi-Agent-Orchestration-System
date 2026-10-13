import ast
import json
import logging
import operator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}
_SAFE_CMPOPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}
_SAFE_UNARY = {ast.Not: operator.not_, ast.USub: operator.neg}


class WorkflowExecutionError(Exception):
    pass


class VisualWorkflowExecutor:
    """
    Executes a visual workflow defined by ReactFlow JSON (nodes and edges).
    Supports sequential and parallel fan-out, conditional branching, and
    cycle-safe dependency resolution.
    """

    def __init__(
        self, workflow_definition: dict[str, Any], context: dict[str, Any] | None = None
    ):
        self.nodes: list[dict[str, Any]] = workflow_definition.get("nodes", [])
        self.edges: list[dict[str, Any]] = workflow_definition.get("edges", [])
        self.context = context or {}

        self.node_map = {node["id"]: node for node in self.nodes}
        self.outgoing_edges: dict[str, list] = {node["id"]: [] for node in self.nodes}
        self.incoming_edges: dict[str, list] = {node["id"]: [] for node in self.nodes}

        for edge in self.edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src and tgt:
                self.outgoing_edges.setdefault(src, []).append(edge)
                self.incoming_edges.setdefault(tgt, []).append(edge)

        self.execution_log: list[dict[str, Any]] = []
        self._max_parallel = int(
            (self.context.get("settings") or {}).get("max_parallel", 4)
        )

    def find_trigger_nodes(self) -> list[dict[str, Any]]:
        triggers = [
            n for n in self.nodes if n.get("data", {}).get("nodeType") == "trigger"
        ]
        if not triggers:
            triggers = [n for n in self.nodes if not self.incoming_edges.get(n["id"])]
        return triggers

    def execute(self) -> dict[str, Any]:
        triggers = self.find_trigger_nodes()
        if not triggers:
            raise WorkflowExecutionError(
                "No trigger nodes found in workflow definition."
            )

        logger.info(
            "Starting workflow execution. Found %s trigger nodes.", len(triggers)
        )

        completed_nodes: set[str] = set()
        skipped_nodes: set[str] = set()
        ready = {n["id"] for n in triggers}
        visits_without_progress = 0
        max_stalls = max(len(self.nodes) * 3, 10)

        while ready:
            batch_ids = [
                nid
                for nid in list(ready)
                if self._deps_satisfied(nid, completed_nodes, skipped_nodes)
            ]
            if not batch_ids:
                visits_without_progress += 1
                if visits_without_progress > max_stalls:
                    raise WorkflowExecutionError(
                        "Workflow appears cyclic or blocked by unmet dependencies."
                    )
                # Drop a stuck node that can never become ready
                stuck = next(iter(ready), None)
                if stuck:
                    ready.discard(stuck)
                    skipped_nodes.add(stuck)
                    self.execution_log.append(
                        {
                            "node_id": stuck,
                            "status": "skipped",
                            "error": "Unmet dependencies or cycle",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                continue

            visits_without_progress = 0
            batch_nodes = [self.node_map[nid] for nid in batch_ids if nid in self.node_map]
            for nid in batch_ids:
                ready.discard(nid)

            results = self._execute_batch(batch_nodes)

            for node_id, outcome in results.items():
                if outcome.get("_failed"):
                    self.execution_log.append(
                        {
                            "node_id": node_id,
                            "status": "failed",
                            "error": outcome.get("error"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    # Halt further scheduling for this branch
                    continue

                self.context[f"node_{node_id}"] = outcome
                self.execution_log.append(
                    {
                        "node_id": node_id,
                        "status": "success",
                        "result": outcome,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                completed_nodes.add(node_id)

                current_node = self.node_map[node_id]
                for edge in self.outgoing_edges.get(node_id, []):
                    target_id = edge.get("target")
                    if not target_id or target_id in completed_nodes or target_id in skipped_nodes:
                        continue
                    if current_node.get("data", {}).get("nodeType") == "condition":
                        condition_met = bool(outcome.get("condition_met", False))
                        handle = str(edge.get("sourceHandle") or "").lower()
                        if handle in ("true", "false"):
                            if handle != str(condition_met).lower():
                                skipped_nodes.add(target_id)
                                continue
                    ready.add(target_id)

        status = (
            "completed"
            if len(completed_nodes) + len(skipped_nodes) >= len(self.nodes)
            else "partial"
        )
        return {
            "status": status,
            "context": self.context,
            "log": self.execution_log,
            "nodes_executed": len(completed_nodes),
            "nodes_skipped": len(skipped_nodes),
        }

    def _deps_satisfied(
        self, node_id: str, completed: set[str], skipped: set[str]
    ) -> bool:
        for edge in self.incoming_edges.get(node_id, []):
            src = edge.get("source")
            if src and src not in completed and src not in skipped:
                return False
        return True

    def _execute_batch(self, nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        if len(nodes) == 1:
            node = nodes[0]
            try:
                return {node["id"]: self._execute_node(node)}
            except Exception as e:  # noqa: BLE001
                logger.error("Error executing node %s: %s", node["id"], e)
                return {node["id"]: {"_failed": True, "error": str(e)}}

        results: dict[str, dict[str, Any]] = {}
        workers = min(self._max_parallel, len(nodes))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._execute_node, n): n["id"] for n in nodes}
            for fut in as_completed(futures):
                node_id = futures[fut]
                try:
                    results[node_id] = fut.result()
                except Exception as e:  # noqa: BLE001
                    logger.error("Error executing node %s: %s", node_id, e)
                    results[node_id] = {"_failed": True, "error": str(e)}
        return results

    def _execute_node(self, node: dict[str, Any]) -> dict[str, Any]:
        data = node.get("data", {})
        node_type = data.get("nodeType", "action")
        logger.info("Executing node %s of type %s", node["id"], node_type)

        if node_type == "trigger":
            return self._execute_trigger(data)
        if node_type == "agent":
            return self._execute_agent(data)
        if node_type == "condition":
            return self._execute_condition(data)
        if node_type == "integration":
            return self._execute_integration(data)
        return {
            "status": "skipped",
            "message": f"Unsupported node type: {node_type}",
        }

    def _execute_trigger(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "event": "workflow_started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": data.get("payload") or self.context.get("input_data", {}),
        }

    def _execute_agent(self, data: dict[str, Any]) -> dict[str, Any]:
        from .langchain_coordinator import execute_agent_task

        label = str(data.get("label", "")).lower()
        agent_type = data.get("agent_type") or data.get("agentType")
        if not agent_type:
            if "vision" in label:
                agent_type = "vision"
            elif "reasoning" in label:
                agent_type = "reasoning"
            elif "action" in label:
                agent_type = "action"
            elif "memory" in label:
                agent_type = "memory"
            else:
                agent_type = "orchestrator"

        task_desc = data.get("description") or data.get("prompt") or "Analyse the provided context."
        system_prompt = data.get("system_prompt") or data.get("systemPrompt")
        enabled_tools = data.get("enabled_tools") or data.get("enabledTools")
        context_payload = {
            **self.context,
            "system_prompt": system_prompt,
            "enabled_tools": enabled_tools,
        }
        context_str = json.dumps(context_payload, default=str)

        try:
            return execute_agent_task.invoke(
                {
                    "agent_type": agent_type,
                    "task_description": task_desc,
                    "context_json": context_str,
                }
            )
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "error": str(e)}

    def _execute_condition(self, data: dict[str, Any]) -> dict[str, Any]:
        expression = (
            data.get("expression")
            or data.get("condition")
            or data.get("description")
            or ""
        )
        if not expression:
            return {"condition_met": True, "details": "Empty condition defaults to true"}

        try:
            met = bool(self._eval_expression(str(expression), self.context))
            return {"condition_met": met, "expression": expression, "details": "ok"}
        except Exception as e:  # noqa: BLE001
            logger.warning("Condition eval failed (%s); defaulting false", e)
            return {
                "condition_met": False,
                "expression": expression,
                "error": str(e),
            }

    def _eval_expression(self, expr: str, ctx: dict[str, Any]) -> Any:
        """Safe-ish eval for simple boolean/comparison expressions over context."""
        # Allow dotted lookups like node_abc.result.status via a flat namespace
        flat: dict[str, Any] = {"context": ctx, "input_data": ctx.get("input_data", {})}
        for key, value in ctx.items():
            flat[key] = value
            if isinstance(value, dict):
                for k2, v2 in value.items():
                    flat[f"{key}_{k2}"] = v2

        tree = ast.parse(expr, mode="eval")

        def _eval(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                if node.id in flat:
                    return flat[node.id]
                raise NameError(node.id)
            if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARY:
                return _SAFE_UNARY[type(node.op)](_eval(node.operand))
            if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINOPS:
                return _SAFE_BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.BoolOp):
                values = [_eval(v) for v in node.values]
                if isinstance(node.op, ast.And):
                    return all(values)
                if isinstance(node.op, ast.Or):
                    return any(values)
            if isinstance(node, ast.Compare):
                left = _eval(node.left)
                for op, comparator in zip(node.ops, node.comparators, strict=False):
                    right = _eval(comparator)
                    fn = _SAFE_CMPOPS.get(type(op))
                    if not fn or not fn(left, right):
                        return False
                    left = right
                return True
            if isinstance(node, ast.Subscript):
                value = _eval(node.value)
                key = _eval(node.slice)
                return value[key]
            if isinstance(node, ast.Attribute):
                value = _eval(node.value)
                return getattr(value, node.attr) if not isinstance(value, dict) else value[node.attr]
            raise ValueError(f"Unsupported expression: {ast.dump(node)}")

        return _eval(tree)

    def _execute_integration(self, data: dict[str, Any]) -> dict[str, Any]:
        tool_name = data.get("tool_name")
        params = data.get("params", {})

        from .external_tools import (
            calculate,
            fetch_url_content,
            get_current_datetime,
            web_search,
        )

        tools = {
            "web_search": web_search,
            "calculate": calculate,
            "fetch_url_content": fetch_url_content,
            "get_current_datetime": get_current_datetime,
        }

        if tool_name in tools:
            try:
                return tools[tool_name].invoke(params)
            except Exception as e:  # noqa: BLE001
                return {"error": str(e)}
        return {"status": "unsupported_tool", "tool": tool_name}
