import uuid
from pathlib import Path
from typing import Any, Callable, Sequence, TypedDict

import yaml
from langchain.tools import BaseTool, tool
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI


SKILLS_ROOT = Path("./skills")


class Skill(TypedDict):
    name: str
    description: str
    content: str
    path: str
    metadata: dict[str, Any]


def parse_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    """
    Parse Claude-style YAML frontmatter from SKILL.md.

    Returns:
        (metadata, markdown_body)
    """
    if not md_text.startswith("---"):
        return {}, md_text.strip()

    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, md_text.strip()

    closing_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    if closing_index is None:
        return {}, md_text.strip()

    frontmatter_text = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1:]).strip()

    metadata = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    return metadata, body


def _extract_first_paragraph(markdown_body: str) -> str | None:
    """
    Claude-style fallback: use the first non-heading paragraph if description
    is not provided in frontmatter.
    """
    paragraphs = [p.strip() for p in markdown_body.split("\n\n") if p.strip()]
    for paragraph in paragraphs:
        if not paragraph.startswith("#"):
            return " ".join(paragraph.split())
    return None


def load_skills_from_claude_directory(skills_root: Path) -> list[Skill]:
    """
    Load skills from:
      .claude/skills/<skill_name>/SKILL.md
    """
    if not skills_root.exists():
        return []

    skills: list[Skill] = []

    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        raw_text = skill_file.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)

        folder_name = skill_file.parent.name
        skill_name = metadata.get("name") or folder_name
        description = (
            metadata.get("description")
            or _extract_first_paragraph(body)
            or "No description provided."
        )

        skills.append(
            {
                "name": skill_name,
                "description": description,
                "content": body,
                "path": str(skill_file),
                "metadata": metadata,
            }
        )

    return skills


def get_skills(skills_root: Path = SKILLS_ROOT) -> list[Skill]:
    return load_skills_from_claude_directory(skills_root)


@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a Claude-format skill into the agent context."""
    skills = get_skills()

    for skill in skills:
        if skill["name"] == skill_name:
            return (
                f"Loaded skill: {skill['name']}\n"
                f"Source: {skill['path']}\n"
                f"Metadata: {skill['metadata']}\n\n"
                f"{skill['content']}"
            )

    available = ", ".join(s["name"] for s in skills) if skills else "(none found)"
    return f"Skill '{skill_name}' not found. Available skills: {available}"


class SkillMiddleware(AgentMiddleware):
    tools = [load_skill]

    def __init__(self, skills_root: Path = SKILLS_ROOT):
        self.skills_root = skills_root

    def _build_skills_prompt(self) -> str:
        skills = get_skills(self.skills_root)
        if not skills:
            return "- No Claude-format skills were found in `.claude/skills/`."

        return "\n".join(
            f"- **{skill['name']}**: {skill['description']}"
            for skill in skills
        )

    def _build_system_message(self, request: ModelRequest) -> SystemMessage:
        skills_prompt = self._build_skills_prompt()

        skills_addendum = (
            "\n\n## Available Skills\n\n"
            f"{skills_prompt}\n\n"
            "Skills are loaded from Claude-style `.claude/skills/<name>/SKILL.md` files. "
            "Use the `load_skill` tool when you need the full instructions."
        )

        original_content = ""
        if request.system_message is not None:
            content = request.system_message.content
            if isinstance(content, str):
                original_content = content
            else:
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        parts.append(item)
                original_content = "\n".join(parts).strip()

        return SystemMessage(content=(original_content + skills_addendum).strip())

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        modified_request = request.override(
            system_message=self._build_system_message(request)
        )
        return handler(modified_request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler,
    ) -> ModelResponse:
        modified_request = request.override(
            system_message=self._build_system_message(request)
        )
        return await handler(modified_request)


def create_sql_agent(
    *,
    model: Any | None = None,
    skills_root: Path | str = SKILLS_ROOT,
    system_prompt: str | None = None,
    extra_tools: Sequence[BaseTool] | None = None,
    mcp_tools: Sequence[BaseTool] | None = None,
    checkpointer: Any | None = None,
):
    """
    Create the SQL assistant agent.

    Args:
        model:
            LangChain chat model instance. Defaults to ChatOpenAI(model="gpt-4").
        skills_root:
            Root directory for Claude-style skills.
        system_prompt:
            Optional override for the agent system prompt.
        extra_tools:
            Any additional LangChain tools to attach.
        mcp_tools:
            Tools created from MCP servers and exposed to the agent.
        checkpointer:
            Optional LangGraph checkpointer. Defaults to InMemorySaver().

    Returns:
        A configured agent instance.
    """
    resolved_skills_root = Path(skills_root)

    if model is None:
        model = ChatOpenAI(model="gpt-4")

    if system_prompt is None:
        system_prompt = (
            "You are a SQL query assistant that helps users "
            "write queries against business databases."
        )

    all_tools: list[BaseTool] = []
    if extra_tools:
        all_tools.extend(extra_tools)
    if mcp_tools:
        all_tools.extend(mcp_tools)

    return create_agent(
        model,
        tools=all_tools,
        system_prompt=system_prompt,
        middleware=[SkillMiddleware(resolved_skills_root)],
        checkpointer=checkpointer or InMemorySaver(),
    )


async def create_sql_agent_with_mcp(
    *,
    mcp_servers: dict[str, dict[str, Any]],
    model: Any | None = None,
    skills_root: Path | str = SKILLS_ROOT,
    system_prompt: str | None = None,
    extra_tools: Sequence[BaseTool] | None = None,
    checkpointer: Any | None = None,
):
    """
    Create the SQL assistant agent and load tools from MCP servers.

    This helper expects `langchain-mcp-adapters` to be installed.

    Example mcp_servers:
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            },
            "postgres": {
                "transport": "sse",
                "url": "http://localhost:8000/sse"
            }
        }
    """
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError as exc:
        raise ImportError(
            "MCP support requires `langchain-mcp-adapters`. "
            "Install it before calling create_sql_agent_with_mcp()."
        ) from exc

    client = MultiServerMCPClient(mcp_servers)
    mcp_tools = await client.get_tools()

    return create_sql_agent(
        model=model,
        skills_root=skills_root,
        system_prompt=system_prompt,
        extra_tools=extra_tools,
        mcp_tools=mcp_tools,
        checkpointer=checkpointer,
    )