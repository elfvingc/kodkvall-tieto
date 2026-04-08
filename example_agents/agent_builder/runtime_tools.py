import ast
import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prompts import TOOL_BUILDER_PROMPT
from utils import extract_json_payload, write_json


GENERATED_TOOLS_DIR = Path(__file__).resolve().parent / "generated_tools"

AVAILABLE_TOOLS = {
    "summarize_input": {
        "description": "Summarize raw notes or long text into a concise brief.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The source text to summarize."},
                "focus": {"type": "string", "description": "Optional focus area for the summary."},
                "max_points": {
                    "type": "integer",
                    "description": "Maximum number of bullet points to return.",
                    "default": 5,
                },
            },
            "required": ["text"],
        },
    },
    "extract_key_points": {
        "description": "Extract goals, risks, questions, and constraints from unstructured input.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The source text to analyze."},
            },
            "required": ["text"],
        },
    },
    "generate_checklist": {
        "description": "Generate a practical checklist from a goal and supporting items.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The overall goal."},
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Supporting items to turn into checklist actions.",
                },
            },
            "required": ["goal", "items"],
        },
    },
    "brainstorm_scenarios": {
        "description": "Generate realistic scenarios, examples, or edge cases for planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The goal or topic to brainstorm around."},
                "count": {
                    "type": "integer",
                    "description": "Number of scenarios to generate.",
                    "default": 3,
                },
            },
            "required": ["goal"],
        },
    },
    "draft_structured_brief": {
        "description": "Turn raw notes into a structured brief with sections, priorities, and open questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic or meeting title."},
                "notes": {"type": "string", "description": "Unstructured notes to organize."},
            },
            "required": ["topic", "notes"],
        },
    },
    "compare_options": {
        "description": "Compare options against explicit criteria and surface tradeoffs.",
        "parameters": {
            "type": "object",
            "properties": {
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Options to compare.",
                },
                "criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Decision criteria.",
                },
            },
            "required": ["options", "criteria"],
        },
    },
    "identify_followups": {
        "description": "Extract follow-up actions, owners, and open questions from text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Source text to inspect."},
            },
            "required": ["text"],
        },
    },
    "prioritize_actions": {
        "description": "Prioritize actions by urgency and impact.",
        "parameters": {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Candidate actions to rank.",
                },
            },
            "required": ["actions"],
        },
    },
}


def ensure_generated_tools_dir() -> Path:
    GENERATED_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    return GENERATED_TOOLS_DIR


def load_generated_tool_modules() -> dict[str, dict[str, Any]]:
    modules: dict[str, dict[str, Any]] = {}
    for path in ensure_generated_tools_dir().glob("*.py"):
        if path.name.startswith("_"):
            continue

        spec = importlib.util.spec_from_file_location(f"generated_tool_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue

        tool_spec = getattr(module, "TOOL_SPEC", None)
        run_function = getattr(module, "run", None)
        if not isinstance(tool_spec, dict) or not callable(run_function):
            continue

        tool_name = tool_spec.get("name")
        description = tool_spec.get("description")
        parameters = tool_spec.get("parameters")
        if not tool_name or not description or not isinstance(parameters, dict):
            continue

        modules[tool_name] = {
            "description": description,
            "parameters": parameters,
            "module": module,
            "path": str(path),
        }

    return modules


def get_tool_registry() -> dict[str, dict[str, Any]]:
    registry = {name: dict(tool_info) for name, tool_info in AVAILABLE_TOOLS.items()}
    for tool_name, tool_info in load_generated_tool_modules().items():
        registry[tool_name] = {
            "description": tool_info["description"],
            "parameters": tool_info["parameters"],
            "path": tool_info["path"],
        }
    return registry


def render_tool_catalog_text() -> str:
    lines = ["Available runtime tools. The generated agent may only use tools from this catalog.", ""]
    for tool_name, tool_info in get_tool_registry().items():
        lines.append(f"- {tool_name}: {tool_info['description']}")
    lines.extend(["", "When returning the tools field, return an array of tool names from this catalog only."])
    return "\n".join(lines)


def build_runtime_tool_definitions(tool_names: list[str]) -> list[dict[str, Any]]:
    tool_registry = get_tool_registry()
    tool_definitions = []
    for tool_name in tool_names:
        if tool_name not in tool_registry:
            continue
        tool_info = tool_registry[tool_name]
        tool_definitions.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": tool_info["parameters"],
                },
            }
        )
    return tool_definitions


def list_tools_payload() -> dict[str, Any]:
    built_in_tools = []
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        built_in_tools.append(
            {
                "name": tool_name,
                "source": "built-in",
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            }
        )

    generated_tools = []
    for tool_name, tool_info in load_generated_tool_modules().items():
        generated_tools.append(
            {
                "name": tool_name,
                "source": "generated",
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
                "path": tool_info["path"],
            }
        )

    return {
        "built_in_tools": built_in_tools,
        "generated_tools": generated_tools,
        "tool_count": len(built_in_tools) + len(generated_tools),
    }


def run_local_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "summarize_input":
        text = arguments["text"].strip()
        focus = arguments.get("focus", "").strip()
        max_points = max(1, min(int(arguments.get("max_points", 5)), 8))
        sentences = [segment.strip(" -") for segment in arguments["text"].replace(".", "\n").splitlines() if segment.strip()]
        summary_points = sentences[:max_points]
        if focus:
            summary_points.insert(0, f"Focus: {focus}")
        return {"summary": summary_points}

    if name == "extract_key_points":
        text = arguments["text"]
        lines = [line.strip(" -*") for line in text.splitlines() if line.strip()]
        goals = [line for line in lines if any(token in line.lower() for token in ["goal", "want", "need", "target"])]
        risks = [line for line in lines if any(token in line.lower() for token in ["risk", "blocker", "concern", "issue"])]
        questions = [line for line in lines if "?" in line]
        constraints = [line for line in lines if any(token in line.lower() for token in ["deadline", "budget", "constraint", "limit"])]
        return {
            "goals": goals[:5],
            "risks": risks[:5],
            "questions": questions[:5],
            "constraints": constraints[:5],
        }

    if name == "generate_checklist":
        goal = arguments["goal"].strip()
        items = [item.strip() for item in arguments.get("items", []) if str(item).strip()]
        checklist = [f"Confirm {goal.lower()}"]
        checklist.extend(f"Prepare: {item}" for item in items[:7])
        checklist.append("Verify output against the goal before delivery")
        return {"goal": goal, "checklist": checklist}

    if name == "brainstorm_scenarios":
        goal = arguments["goal"].strip()
        count = max(1, min(int(arguments.get("count", 3)), 5))
        scenarios = [
            f"Baseline scenario for {goal}",
            f"Edge-case scenario for {goal}",
            f"High-stakes scenario for {goal}",
            f"Low-context scenario for {goal}",
            f"Time-constrained scenario for {goal}",
        ]
        return {"scenarios": scenarios[:count]}

    if name == "draft_structured_brief":
        topic = arguments["topic"].strip()
        notes = [line.strip(" -*") for line in arguments["notes"].splitlines() if line.strip()]
        priorities = notes[:3]
        open_questions = [line for line in notes if "?" in line][:3]
        return {
            "topic": topic,
            "brief": {
                "summary": notes[:4],
                "priorities": priorities,
                "open_questions": open_questions,
                "recommended_next_step": f"Prepare a concrete plan for {topic}",
            },
        }

    if name == "compare_options":
        options = [option.strip() for option in arguments["options"] if str(option).strip()]
        criteria = [criterion.strip() for criterion in arguments["criteria"] if str(criterion).strip()]
        comparisons = []
        for index, option in enumerate(options, start=1):
            strengths = [f"Strong on {criterion}" for criterion in criteria[:2]]
            tradeoffs = [f"Needs validation on {criterion}" for criterion in criteria[2:4]]
            comparisons.append(
                {
                    "option": option,
                    "rank": index,
                    "strengths": strengths,
                    "tradeoffs": tradeoffs,
                }
            )
        return {"criteria": criteria, "comparisons": comparisons}

    if name == "identify_followups":
        text = arguments["text"]
        lines = [line.strip(" -*") for line in text.splitlines() if line.strip()]
        followups = [line for line in lines if any(token in line.lower() for token in ["follow up", "next", "send", "prepare", "schedule"])]
        questions = [line for line in lines if "?" in line]
        owners = [line for line in lines if any(token in line.lower() for token in ["owner", "responsible", "team", "rep"])]
        return {
            "followups": followups[:5],
            "open_questions": questions[:5],
            "owners_or_stakeholders": owners[:5],
        }

    if name == "prioritize_actions":
        actions = [action.strip() for action in arguments["actions"] if str(action).strip()]
        prioritized = []
        for index, action in enumerate(actions, start=1):
            priority = "high" if index <= 2 else "medium" if index <= 4 else "low"
            prioritized.append(
                {
                    "action": action,
                    "priority": priority,
                    "reason": f"Ranked {priority} based on sequence and likely impact.",
                }
            )
        return {"prioritized_actions": prioritized}

    generated_tools = load_generated_tool_modules()
    generated_tool = generated_tools.get(name)
    if generated_tool:
        return generated_tool["module"].run(arguments)

    raise ValueError(f"Unsupported tool: {name}")


def normalize_generated_tool_filename(filename: str, tool_name: str) -> str:
    candidate = (filename or f"{tool_name}.py").strip().lower()
    candidate = "".join(char if char.isalnum() or char in "_- ." else "_" for char in candidate).replace(" ", "_")
    if not candidate.endswith(".py"):
        candidate = f"{candidate}.py"
    return candidate


def validate_generated_tool_code(python_code: str) -> None:
    tree = ast.parse(python_code, filename="<generated_tool>")
    compile(python_code, "<generated_tool>", "exec")

    allowed_import_roots = {
        "collections",
        "datetime",
        "functools",
        "itertools",
        "json",
        "math",
        "re",
        "statistics",
        "string",
        "typing",
    }
    banned_modules = {
        "asyncio",
        "builtins",
        "http",
        "importlib",
        "os",
        "pathlib",
        "pickle",
        "requests",
        "shutil",
        "socket",
        "subprocess",
        "sys",
        "urllib",
    }
    banned_calls = {"eval", "exec", "compile", "open", "input", "__import__", "breakpoint"}
    banned_attribute_roots = {"os", "sys", "subprocess", "socket", "shutil", "pathlib", "importlib"}

    tool_spec_found = False
    run_found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                if root_name in banned_modules or root_name not in allowed_import_roots:
                    raise ValueError(f"Generated tool imports disallowed module: {alias.name}")

        if isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".", 1)[0]
            if module_name in banned_modules or module_name not in allowed_import_roots:
                raise ValueError(f"Generated tool imports disallowed module: {node.module}")

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TOOL_SPEC":
                    tool_spec_found = True

        if isinstance(node, ast.FunctionDef) and node.name == "run":
            run_found = True

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in banned_calls:
                raise ValueError(f"Generated tool uses banned function call: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in banned_attribute_roots:
                    raise ValueError(
                        f"Generated tool uses banned module attribute: {node.func.value.id}.{node.func.attr}"
                    )

    if not tool_spec_found:
        raise ValueError("Generated tool must define TOOL_SPEC.")
    if not run_found:
        raise ValueError("Generated tool must define a run function.")


def generate_tool_module(request: str, call_mistral_fn) -> dict[str, Any]:
    response = call_mistral_fn(
        [
            {"role": "system", "content": TOOL_BUILDER_PROMPT},
            {"role": "user", "content": request},
        ]
    )
    payload = extract_json_payload(response.choices[0].message.content)

    python_code = payload.get("python_code")
    tool_name = payload.get("tool_name")
    if not isinstance(python_code, str) or not python_code.strip():
        raise ValueError("Generated tool response did not include valid python_code.")
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("Generated tool response did not include a valid tool_name.")

    validate_generated_tool_code(python_code)
    return payload


def save_generated_tool(payload: dict[str, Any]) -> dict[str, str]:
    tool_name = payload["tool_name"].strip()
    filename = normalize_generated_tool_filename(payload.get("filename", ""), tool_name)
    tool_dir = ensure_generated_tools_dir()
    code_path = tool_dir / filename
    metadata_path = tool_dir / f"{Path(filename).stem}.json"

    code_path.write_text(payload["python_code"].rstrip() + "\n", encoding="utf-8")
    metadata = {
        "tool_name": tool_name,
        "description": payload.get("description"),
        "parameters": payload.get("parameters"),
        "review_notes": payload.get("review_notes"),
        "saved_at": datetime.now(UTC).isoformat(),
        "python_file": str(code_path),
    }
    write_json(metadata_path, metadata)

    return {
        "tool_name": tool_name,
        "python_file": str(code_path),
        "metadata_file": str(metadata_path),
    }
