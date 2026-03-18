import json
from typing import Any, Dict, List

def _safe_getattr(obj: Any, attr: str, default=None):
    return getattr(obj, attr, default) if obj is not None else default

def _shorten(text: str, max_len: int = 300) -> str:
    if text is None:
        return ""
    text = str(text).strip()
    return text if len(text) <= max_len else text[:max_len] + " ..."

def _extract_tool_payload(content: Any) -> str:
    """
    ToolMessage.content is often a list like:
    [{'type': 'text', 'text': '...json...', 'id': '...'}]
    """
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(item["text"])
                else:
                    parts.append(json.dumps(item, indent=2, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    if isinstance(content, dict):
        return json.dumps(content, indent=2, ensure_ascii=False)

    return str(content)

def _pretty_json_if_possible(text: str) -> str:
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        return text

def summarize_agent_run(agent_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert raw agent output into a structured list of timeline events.
    """
    rows = []

    for i, msg in enumerate(agent_output.get("messages", []), start=1):
        msg_type = msg.__class__.__name__

        row = {
            "step": i,
            "type": msg_type,
            "content": "",
            "tool_name": None,
            "tool_calls": None,
            "token_total": None,
            "model": None,
        }

        if msg_type == "HumanMessage":
            row["content"] = _safe_getattr(msg, "content", "")

        elif msg_type == "AIMessage":
            row["content"] = _safe_getattr(msg, "content", "")

            tool_calls = _safe_getattr(msg, "tool_calls", [])
            if tool_calls:
                row["tool_calls"] = [
                    {
                        "name": tc.get("name"),
                        "args": tc.get("args"),
                        "id": tc.get("id"),
                    }
                    for tc in tool_calls
                ]

            usage_metadata = _safe_getattr(msg, "usage_metadata", {}) or {}
            response_metadata = _safe_getattr(msg, "response_metadata", {}) or {}

            row["token_total"] = (
                usage_metadata.get("total_tokens")
                or (response_metadata.get("token_usage") or {}).get("total_tokens")
            )
            row["model"] = response_metadata.get("model_name")

        elif msg_type == "ToolMessage":
            row["tool_name"] = _safe_getattr(msg, "name", None)
            raw = _extract_tool_payload(_safe_getattr(msg, "content", ""))
            row["content"] = _pretty_json_if_possible(raw)

        else:
            row["content"] = str(_safe_getattr(msg, "content", ""))

        rows.append(row)

    return rows

def print_agent_timeline(agent_output: Dict[str, Any], max_content_len: int = 500) -> None:
    """
    Pretty console visualization of the agent run.
    """
    rows = summarize_agent_run(agent_output)

    print("\n" + "=" * 100)
    print("AGENT RUN TIMELINE")
    print("=" * 100)

    for row in rows:
        print(f"\n[{row['step']}] {row['type']}")

        if row["model"]:
            print(f"Model      : {row['model']}")
        if row["token_total"] is not None:
            print(f"Tokens     : {row['token_total']}")
        if row["tool_name"]:
            print(f"Tool       : {row['tool_name']}")

        if row["tool_calls"]:
            print("Tool Calls :")
            for tc in row["tool_calls"]:
                print(f"  - {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")

        content = row["content"]
        if content:
            print("Content    :")
            print(_shorten(content, max_content_len))

    print("\n" + "=" * 100)

def to_dataframe(agent_output: Dict[str, Any]):
    """
    Optional: return a pandas DataFrame for notebook exploration.
    """
    import pandas as pd

    rows = summarize_agent_run(agent_output)

    flat_rows = []
    for row in rows:
        flat_rows.append({
            "step": row["step"],
            "type": row["type"],
            "model": row["model"],
            "token_total": row["token_total"],
            "tool_name": row["tool_name"],
            "tool_calls": json.dumps(row["tool_calls"], ensure_ascii=False, indent=2) if row["tool_calls"] else None,
            "content": row["content"],
        })

    return pd.DataFrame(flat_rows)