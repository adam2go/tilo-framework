"""LangChain → Tilo AIP adapter.

Provides a callback handler that captures LangChain chain output
and converts it into a Tilo AIP spec.

Usage (callback — integrates with any LangChain chain):
    from tilo.adapters.langchain import TiloCallbackHandler

    handler = TiloCallbackHandler(run_id="my-tilo-run")
    chain.invoke(input, config={"callbacks": [handler]})
    spec = handler.to_spec()            # → Tilo AIP v1 dict

Usage (direct conversion — convert a chain output dict):
    from tilo.adapters.langchain import langchain_result_to_spec

    spec = langchain_result_to_spec("MyChain", outputs)

Design notes:
- No hard dependency on langchain at import time (duck-typed interface).
  The handler works with any object that calls these methods.
- Structured output (dict / list-of-dicts) maps to metric / table blocks.
- Tool calls map to tool_preview blocks with success / error status.
- on_chain_end is a fallback: if finer-grained callbacks already captured
  output, it is skipped to avoid duplication.
"""

from __future__ import annotations

import json
import uuid
from typing import Any


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _new_id(prefix: str = "lc") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _text_to_block(text: str, block_id: str | None = None) -> dict[str, Any]:
    return {
        "id": block_id or _new_id("lc_text"),
        "type": "markdown",
        "title": None,
        "props": {"content": text.strip()},
    }


def _tool_result_to_block(
    tool_name: str,
    output: str,
    block_id: str | None = None,
    *,
    is_error: bool = False,
) -> dict[str, Any]:
    return {
        "id": block_id or _new_id("lc_tool"),
        "type": "tool_preview",
        "title": tool_name,
        "props": {
            "tool_name": tool_name,
            "status": "error" if is_error else "success",
            "output": str(output)[:2000],
        },
    }


def _structured_output_to_blocks(
    data: Any,
    block_id_prefix: str = "lc_struct",
) -> list[dict[str, Any]]:
    """Convert a structured value (dict / list) to appropriate block types.

    - Flat dict with ≤8 numeric/short-string values → metric blocks.
    - List of dicts → table block.
    - Anything else → markdown with JSON pretty-print.
    """
    if isinstance(data, dict):
        is_metrics = (
            len(data) <= 8
            and all(
                isinstance(v, (int, float))
                or (isinstance(v, str) and len(v) < 40)
                for v in data.values()
            )
        )
        if is_metrics:
            return [
                {
                    "id": f"{block_id_prefix}_{i}",
                    "type": "metric",
                    "title": key.replace("_", " ").title(),
                    "props": {
                        "label": key.replace("_", " ").title(),
                        "value": str(value),
                    },
                }
                for i, (key, value) in enumerate(data.items())
            ]
        return [_text_to_block(
            f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```",
            f"{block_id_prefix}_json",
        )]

    if isinstance(data, list) and data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        rows = [[str(row.get(col, "")) for col in columns] for row in data]
        return [{
            "id": f"{block_id_prefix}_table",
            "type": "table",
            "title": None,
            "props": {
                "columns": [{"key": c, "label": c.replace("_", " ").title()} for c in columns],
                "rows": rows,
            },
        }]

    return [_text_to_block(
        json.dumps(data, indent=2, ensure_ascii=False),
        f"{block_id_prefix}_fallback",
    )]


def _parse_message_content(content: str | list[Any]) -> str:
    """Extract plain text from a LangChain message content field.

    Content can be a plain string or a list of typed dicts
    (e.g. [{"type": "text", "text": "…"}, {"type": "image_url", …}]).
    """
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif item.get("type") == "image_url":
                parts.append("[image]")
        elif isinstance(item, str):
            parts.append(item)
    return "\n".join(parts)


def _spec(
    blocks: list[dict[str, Any]],
    title: str,
    run_id: str | None,
    provenance_id: str,
) -> dict[str, Any]:
    effective_blocks = blocks or [_text_to_block("No output captured.", "lc_empty")]
    result: dict[str, Any] = {
        "version": "tilo/aip/v1",
        "title": title,
        "status": "ready",
        "blocks": effective_blocks,
        "views": [
            {
                "id": "result",
                "label": "Result",
                "block_ids": [b["id"] for b in effective_blocks],
            }
        ],
        "actions": [],
        "provenance": [{"type": "langchain_chain", "id": provenance_id}],
        "memory_refs": [],
        "follow_ups": [],
    }
    if run_id:
        result["run_id"] = run_id
    return result


# --------------------------------------------------------------------------- #
# Public: direct conversion                                                    #
# --------------------------------------------------------------------------- #

def langchain_result_to_spec(
    chain_name: str,
    outputs: dict[str, Any],
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Convert a LangChain chain output dict directly into a Tilo AIP v1 spec.

    Args:
        chain_name: Name of the chain (used as spec title and provenance).
        outputs:    The dict returned by ``chain.invoke()``.
        run_id:     Optional Tilo run_id to embed in the spec.

    Returns:
        A Tilo AIP v1 spec dict ready for use with ArtifactSpecV1.model_validate().
    """
    blocks: list[dict[str, Any]] = []
    for key, value in outputs.items():
        if isinstance(value, str):
            if value.strip():
                blocks.append(_text_to_block(value, f"lc_out_{key}"))
        elif isinstance(value, (dict, list)):
            blocks.extend(_structured_output_to_blocks(value, f"lc_out_{key}"))
        else:
            blocks.append(_text_to_block(str(value), f"lc_out_{key}"))

    return _spec(blocks, chain_name, run_id, chain_name)


# --------------------------------------------------------------------------- #
# Public: callback handler                                                     #
# --------------------------------------------------------------------------- #

class TiloCallbackHandler:
    """LangChain callback handler that accumulates output as Tilo AIP blocks.

    Duck-typed — no langchain import required. Compatible with:
    - LangChain v0.1+ (``BaseCallbackHandler`` interface)
    - LangGraph nodes that emit callbacks
    - Any object that calls these methods

    Example:
        handler = TiloCallbackHandler(run_id="tilo-run-123")
        chain.invoke(input, config={"callbacks": [handler]})
        spec = handler.to_spec()
        validated = ArtifactSpecV1.model_validate(spec)
    """

    def __init__(
        self,
        run_id: str | None = None,
        title: str = "LangChain Result",
    ) -> None:
        self.run_id = run_id
        self.title = title
        self.blocks: list[dict[str, Any]] = []
        self._tool_names: dict[str, str] = {}  # callback run_id → tool name

    # ------------------------------------------------------------------ #
    # LLM callbacks                                                        #
    # ------------------------------------------------------------------ #

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[Any],
        **kwargs: Any,
    ) -> None:
        """No-op — output captured in on_llm_end."""

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Capture LLM text output as a markdown block."""
        try:
            generation = response.generations[0][0]
            text: str = getattr(generation, "text", "") or ""
            if not text and hasattr(generation, "message"):
                text = _parse_message_content(
                    getattr(generation.message, "content", "")
                )
            if text.strip():
                self.blocks.append(_text_to_block(text, _new_id("lc_llm")))
        except (AttributeError, IndexError):
            pass

    # ------------------------------------------------------------------ #
    # Tool callbacks                                                       #
    # ------------------------------------------------------------------ #

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Record tool name so on_tool_end can label the block."""
        cb_run_id = str(kwargs.get("run_id", ""))
        tool_name = serialized.get("name", "tool")
        if cb_run_id:
            self._tool_names[cb_run_id] = tool_name

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """Capture tool output as a tool_preview block."""
        cb_run_id = str(kwargs.get("run_id", ""))
        tool_name = self._tool_names.pop(cb_run_id, "tool")
        self.blocks.append(
            _tool_result_to_block(tool_name, str(output), _new_id("lc_tool"))
        )

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Capture tool error as a tool_preview block with error status."""
        cb_run_id = str(kwargs.get("run_id", ""))
        tool_name = self._tool_names.pop(cb_run_id, "tool")
        self.blocks.append(
            _tool_result_to_block(
                tool_name, str(error), _new_id("lc_tool_err"), is_error=True
            )
        )

    # ------------------------------------------------------------------ #
    # Agent callbacks                                                      #
    # ------------------------------------------------------------------ #

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Capture the final agent answer, avoiding duplicates from on_llm_end."""
        try:
            return_values: dict[str, Any] = getattr(finish, "return_values", {})
            output = return_values.get("output", "") if isinstance(return_values, dict) else ""
            if not (output and isinstance(output, str)):
                return
            already = any(
                b.get("props", {}).get("content", "").strip() == output.strip()
                for b in self.blocks
                if b.get("type") == "markdown"
            )
            if not already:
                self.blocks.append(_text_to_block(output, _new_id("lc_agent")))
        except AttributeError:
            pass

    # ------------------------------------------------------------------ #
    # Chain callbacks                                                      #
    # ------------------------------------------------------------------ #

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Fallback: capture structured chain output if no blocks exist yet."""
        if self.blocks:
            return  # finer-grained callbacks already captured content
        if not isinstance(outputs, dict):
            return
        for key, value in outputs.items():
            if isinstance(value, str) and value.strip():
                self.blocks.append(_text_to_block(value, f"lc_chain_{key}"))
            elif isinstance(value, (dict, list)):
                self.blocks.extend(
                    _structured_output_to_blocks(value, f"lc_chain_{key}")
                )

    # ------------------------------------------------------------------ #
    # Output                                                               #
    # ------------------------------------------------------------------ #

    def to_spec(self) -> dict[str, Any]:
        """Assemble all captured blocks into a Tilo AIP v1 spec dict."""
        return _spec(self.blocks, self.title, self.run_id, self.title)

    def reset(self) -> None:
        """Clear all captured state. Allows reuse across multiple chain runs."""
        self.blocks.clear()
        self._tool_names.clear()


# --------------------------------------------------------------------------- #
# Full AIP generation (recommended entry point)                                #
# --------------------------------------------------------------------------- #

def generate_aip_spec(
    llm: Any,
    goal: str,
    *,
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
) -> Any:
    """Generate a full Tilo AIP spec using any LangChain chat model.

    Unlike ``TiloCallbackHandler`` which captures existing chain output,
    this function prompts the LLM with the full AIP format so it generates
    a rich, structured spec — including chart, diff, confirmation, and
    memory_card blocks organised into views with follow-up suggestions.

    Args:
        llm:       Any LangChain chat model (ChatOpenAI, ChatAnthropic, etc.).
        goal:      What the artifact should address.
        skill:     "auto" to detect from goal, or one of:
                   "contract_review", "code_review", "sales_dashboard",
                   "trip_planning", "competitive_analysis", "data_analysis".
        document:  Optional document text (contract, PR diff, etc.).
        memories:  Optional list of recalled user preference strings.
        language:  "en" to force English, "zh" for Chinese output.

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Example:
        from langchain_openai import ChatOpenAI
        from tilo.adapters.langchain import generate_aip_spec

        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        spec = generate_aip_spec(
            llm=llm,
            goal="Analyse Q3 sales pipeline and recommend follow-up actions.",
            skill="sales_dashboard",
        )
        print([b.type for b in spec.blocks])
        # → ["metric", "metric", "card", "list", "tool_preview", "memory_card"]
    """
    from tilo.generate import generate_with_langchain
    return generate_with_langchain(
        llm, goal,
        skill=skill, document=document,
        memories=memories, language=language,
    )
