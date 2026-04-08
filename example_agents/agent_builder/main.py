"""Main orchestration file for the agent builder demo.

This file keeps the most important concepts visible:
- the self-improvement pipeline: architect -> simulate -> critique -> refine
- the final agent tool-calling loop
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prompts import (
    CRITIC_PROMPT,
    EVAL_PROMPT,
    SIMULATOR_PROMPT,
    build_architect_prompt,
    build_refiner_prompt,
    build_tool_gap_prompt,
)
from runtime_tools import (
    build_runtime_tool_definitions,
    generate_tool_module,
    get_tool_registry,
    list_tools_payload,
    render_tool_catalog_text,
    run_local_tool,
    save_generated_tool,
)
from utils import (
    DEFAULT_TASK,
    MODEL,
    call_mistral,
    ensure_artifact_dir,
    extract_json_payload,
    extract_text_content,
    load_required_json,
    print_step,
    read_json,
    save_pipeline_artifacts,
    slugify,
)


TOOL_CATALOG_TEXT = render_tool_catalog_text()
ARCHITECT_PROMPT = build_architect_prompt(TOOL_CATALOG_TEXT)
REFINER_PROMPT = build_refiner_prompt(TOOL_CATALOG_TEXT)
TOOL_GAP_PROMPT = build_tool_gap_prompt(TOOL_CATALOG_TEXT)
KNOWN_COMMANDS = {"pipeline", "step", "run-agent", "eval", "create-tool", "suggest-tool", "list-tools"}


def parse_tool_arguments(raw_arguments: Any) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if isinstance(raw_arguments, str):
        return extract_json_payload(raw_arguments)
    return extract_json_payload(str(raw_arguments))


def normalize_message_for_history(message: Any) -> dict[str, Any]:
    if isinstance(message, dict):
        return message

    normalized = {
        "role": getattr(message, "role", "assistant"),
        "content": extract_text_content(getattr(message, "content", "")),
    }

    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        normalized_calls = []
        for tool_call in tool_calls:
            function_obj = getattr(tool_call, "function", None)
            normalized_calls.append(
                {
                    "id": getattr(tool_call, "id", None),
                    "type": getattr(tool_call, "type", "function"),
                    "function": {
                        "name": getattr(function_obj, "name", None),
                        "arguments": getattr(function_obj, "arguments", None),
                    },
                }
            )
        normalized["tool_calls"] = normalized_calls

    return normalized


def get_tool_calls(message: Any) -> list[Any]:
    if isinstance(message, dict):
        return message.get("tool_calls") or []
    return getattr(message, "tool_calls", None) or []


def run_architect(task: str) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": ARCHITECT_PROMPT},
            {"role": "user", "content": task},
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


def run_simulator(design: dict[str, Any]) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": SIMULATOR_PROMPT},
            {"role": "user", "content": json.dumps(design, ensure_ascii=False)},
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


def run_critic(design: dict[str, Any], simulation: dict[str, Any]) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": CRITIC_PROMPT},
            {"role": "user", "content": json.dumps({"design": design, "simulation": simulation}, ensure_ascii=False)},
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


def run_refiner(design: dict[str, Any], simulation: dict[str, Any], critique: dict[str, Any]) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": REFINER_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"design": design, "simulation": simulation, "critique": critique},
                    ensure_ascii=False,
                ),
            },
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


def suggest_missing_tools(task: str, design: dict[str, Any], critique: dict[str, Any]) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": TOOL_GAP_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": task,
                        "design": design,
                        "critique": critique,
                        "current_tools": list(get_tool_registry().keys()),
                    },
                    ensure_ascii=False,
                ),
            },
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


# Concept: tool-calling loop for the final runnable agent.
def run_generated_agent(agent_spec: dict[str, Any], user_input: str, max_rounds: int = 5) -> dict[str, Any]:
    tool_registry = get_tool_registry()
    tool_names = [name for name in agent_spec.get("tools", []) if name in tool_registry]
    tool_definitions = build_runtime_tool_definitions(tool_names)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": agent_spec["system_prompt"]},
        {"role": "user", "content": user_input},
    ]

    for _ in range(max_rounds):
        response = call_mistral(
            messages,
            tools=tool_definitions or None,
            tool_choice="auto" if tool_definitions else "none",
            parallel_tool_calls=bool(tool_definitions),
        )
        message = response.choices[0].message
        tool_calls = get_tool_calls(message)

        if not tool_calls:
            return {
                "messages": messages,
                "final_output": extract_text_content(getattr(message, "content", "")),
            }

        messages.append(normalize_message_for_history(message))

        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                function_data = tool_call.get("function", {})
                tool_name = function_data.get("name")
                raw_arguments = function_data.get("arguments", {})
                tool_call_id = tool_call.get("id")
            else:
                function_data = getattr(tool_call, "function", None)
                tool_name = getattr(function_data, "name", None)
                raw_arguments = getattr(function_data, "arguments", {})
                tool_call_id = getattr(tool_call, "id", None)

            if not tool_name:
                continue

            arguments = parse_tool_arguments(raw_arguments)
            result = run_local_tool(tool_name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("The generated agent exceeded the maximum number of tool rounds.")


def build_final_agent_payload(ready_to_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": ready_to_run.get("name"),
        "purpose": ready_to_run.get("purpose"),
        "refinement_summary": ready_to_run.get("refinement_summary"),
        "implementation_notes": ready_to_run.get("implementation_notes"),
        "runner_instructions": ready_to_run.get("runner_instructions"),
        "agent_spec": ready_to_run["ready_to_run_agent_spec"],
    }


def export_final_agent(artifact_dir: Path, ready_to_run: dict[str, Any]) -> dict[str, Any]:
    final_agent = build_final_agent_payload(ready_to_run)
    save_pipeline_artifacts(artifact_dir, "08_final_agent.json", final_agent)
    return final_agent


def load_agent_spec(artifact_dir: Path | None = None, agent_file: Path | None = None) -> dict[str, Any]:
    if agent_file is not None:
        payload = read_json(agent_file)
        if "agent_spec" in payload:
            return payload["agent_spec"]
        if "ready_to_run_agent_spec" in payload:
            return payload["ready_to_run_agent_spec"]
        raise ValueError(f"Could not find agent spec in file: {agent_file}")

    if artifact_dir is None:
        raise ValueError("Either artifact_dir or agent_file must be provided.")

    final_agent_path = artifact_dir / "08_final_agent.json"
    if final_agent_path.exists():
        return read_json(final_agent_path)["agent_spec"]

    ready_to_run = load_required_json(artifact_dir, "04_ready_to_run.json")
    return ready_to_run["ready_to_run_agent_spec"]


# Concept: the self-improving meta-agent flow from design to final agent.
def run_pipeline(task: str, artifact_dir: Path) -> dict[str, Any]:
    print_step("Architect")
    design = run_architect(task)
    save_pipeline_artifacts(artifact_dir, "01_design.json", design)
    print(json.dumps(design, indent=2, ensure_ascii=False))

    print_step("Simulator")
    simulation = run_simulator(design)
    save_pipeline_artifacts(artifact_dir, "02_simulation.json", simulation)
    print(json.dumps(simulation, indent=2, ensure_ascii=False))

    print_step("Critic")
    critique = run_critic(design, simulation)
    save_pipeline_artifacts(artifact_dir, "03_critique.json", critique)
    print(json.dumps(critique, indent=2, ensure_ascii=False))

    print_step("Refiner")
    ready_to_run = run_refiner(design, simulation, critique)
    save_pipeline_artifacts(artifact_dir, "04_ready_to_run.json", ready_to_run)
    print(json.dumps(ready_to_run, indent=2, ensure_ascii=False))

    print_step("Export Final Agent")
    final_agent = export_final_agent(artifact_dir, ready_to_run)
    print(json.dumps(final_agent, indent=2, ensure_ascii=False))

    print_step("Tool Gap Review")
    tool_opportunities = suggest_missing_tools(task, design, critique)
    save_pipeline_artifacts(artifact_dir, "07_tool_opportunities.json", tool_opportunities)
    print(json.dumps(tool_opportunities, indent=2, ensure_ascii=False))

    manifest = {
        "task": task,
        "model": MODEL,
        "artifact_dir": str(artifact_dir),
        "created_at": datetime.now(UTC).isoformat(),
        "files": {
            "design": "01_design.json",
            "simulation": "02_simulation.json",
            "critique": "03_critique.json",
            "ready_to_run": "04_ready_to_run.json",
            "final_agent": "08_final_agent.json",
            "tool_opportunities": "07_tool_opportunities.json",
        },
    }
    save_pipeline_artifacts(artifact_dir, "00_manifest.json", manifest)

    return {
        "manifest": manifest,
        "design": design,
        "simulation": simulation,
        "critique": critique,
        "ready_to_run": ready_to_run,
        "final_agent": final_agent,
        "tool_opportunities": tool_opportunities,
    }


def run_single_step(step: str, artifact_dir: Path, task: str | None = None) -> Any:
    if step == "architect":
        if not task:
            raise ValueError("The architect step requires --task.")
        result = run_architect(task)
        save_pipeline_artifacts(artifact_dir, "01_design.json", result)
        return result

    if step == "simulate":
        design = load_required_json(artifact_dir, "01_design.json")
        result = run_simulator(design)
        save_pipeline_artifacts(artifact_dir, "02_simulation.json", result)
        return result

    if step == "critique":
        design = load_required_json(artifact_dir, "01_design.json")
        simulation = load_required_json(artifact_dir, "02_simulation.json")
        result = run_critic(design, simulation)
        save_pipeline_artifacts(artifact_dir, "03_critique.json", result)
        return result

    if step == "refine":
        design = load_required_json(artifact_dir, "01_design.json")
        simulation = load_required_json(artifact_dir, "02_simulation.json")
        critique = load_required_json(artifact_dir, "03_critique.json")
        result = run_refiner(design, simulation, critique)
        save_pipeline_artifacts(artifact_dir, "04_ready_to_run.json", result)
        export_final_agent(artifact_dir, result)
        return result

    if step == "suggest-tool":
        design = load_required_json(artifact_dir, "01_design.json")
        critique = load_required_json(artifact_dir, "03_critique.json")
        manifest_path = artifact_dir / "00_manifest.json"
        task_value = task
        if manifest_path.exists() and task_value is None:
            task_value = read_json(manifest_path).get("task")
        if not task_value:
            raise ValueError("The suggest-tool step requires --task or an existing 00_manifest.json with a task.")
        result = suggest_missing_tools(task_value, design, critique)
        save_pipeline_artifacts(artifact_dir, "07_tool_opportunities.json", result)
        return result

    raise ValueError(f"Unsupported step: {step}")


def run_saved_agent(
    artifact_dir: Path | None = None,
    user_input: str | None = None,
    agent_file: Path | None = None,
) -> dict[str, Any]:
    agent_spec = load_agent_spec(artifact_dir=artifact_dir, agent_file=agent_file)
    if user_input is None:
        prompts = agent_spec.get("example_prompts", [])
        if not prompts:
            raise ValueError("No example prompts found in ready-to-run spec. Provide --user-input.")
        user_input = prompts[0]

    if user_input is None:
        raise ValueError("User input could not be resolved.")

    result = run_generated_agent(agent_spec, user_input)
    payload = {
        "agent_source": str(agent_file) if agent_file is not None else str(artifact_dir),
        "user_input": user_input,
        "result": result,
    }
    if artifact_dir is not None:
        save_pipeline_artifacts(artifact_dir, "05_agent_run.json", payload)
    return payload


def evaluate_agent_output(agent_spec: dict[str, Any], prompt: str, output: str, checklist: list[str]) -> dict[str, Any]:
    response = call_mistral(
        [
            {"role": "system", "content": EVAL_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "system_prompt": agent_spec["system_prompt"],
                        "prompt": prompt,
                        "output": output,
                        "eval_checklist": checklist,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
    )
    return extract_json_payload(response.choices[0].message.content)


def run_saved_agent_eval(artifact_dir: Path, prompts: list[str] | None = None) -> dict[str, Any]:
    ready_to_run = load_required_json(artifact_dir, "04_ready_to_run.json")
    agent_spec = ready_to_run["ready_to_run_agent_spec"]
    eval_checklist = agent_spec.get("eval_checklist", [])
    example_prompts = prompts or agent_spec.get("example_prompts", [])
    if not example_prompts:
        raise ValueError("No example prompts found for evaluation.")

    evaluations = []
    for prompt in example_prompts:
        agent_run = run_generated_agent(agent_spec, prompt)
        judged = evaluate_agent_output(agent_spec, prompt, agent_run["final_output"], eval_checklist)
        evaluations.append(
            {
                "prompt": prompt,
                "agent_output": agent_run["final_output"],
                "evaluation": judged,
            }
        )

    scores = [item["evaluation"].get("score", 0) for item in evaluations]
    verdicts = [item["evaluation"].get("verdict", "fail") for item in evaluations]
    payload = {
        "overall_score": round(sum(scores) / len(scores), 2),
        "overall_verdict": "pass" if all(v == "pass" for v in verdicts) else "fail" if any(v == "fail" for v in verdicts) else "borderline",
        "examples_evaluated": len(evaluations),
        "evaluations": evaluations,
    }
    save_pipeline_artifacts(artifact_dir, "06_eval.json", payload)
    return payload


def run_tool_gap_analysis(
    artifact_dir: Path | None = None,
    task: str | None = None,
    design_file: Path | None = None,
    critique_file: Path | None = None,
) -> dict[str, Any]:
    if artifact_dir is not None:
        design_file = design_file or artifact_dir / "01_design.json"
        critique_file = critique_file or artifact_dir / "03_critique.json"
        manifest_path = artifact_dir / "00_manifest.json"
        if task is None and manifest_path.exists():
            task = read_json(manifest_path).get("task")

    if design_file is None or critique_file is None:
        raise ValueError("Tool-gap analysis requires design and critique JSON inputs.")
    if task is None:
        raise ValueError("Tool-gap analysis requires a task, either directly or through 00_manifest.json.")

    result = suggest_missing_tools(task, read_json(design_file), read_json(critique_file))
    if artifact_dir is not None:
        save_pipeline_artifacts(artifact_dir, "07_tool_opportunities.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and run a meta-agent pipeline with reusable JSON artifacts.")
    subparsers = parser.add_subparsers(dest="command")

    pipeline_parser = subparsers.add_parser("pipeline", help="Run the full architect -> simulate -> critique -> refine pipeline.")
    pipeline_parser.add_argument("--task", required=True, help="The user task for the meta-agent.")
    pipeline_parser.add_argument("--run-id", help="Artifact directory name. Defaults to a slug based on the task.")
    pipeline_parser.add_argument("--run-agent", action="store_true", help="Run the generated agent after refinement.")
    pipeline_parser.add_argument("--eval", action="store_true", help="Evaluate the generated agent on its saved example prompts.")
    pipeline_parser.add_argument("--user-input", help="Optional input for the generated agent.")

    step_parser = subparsers.add_parser("step", help="Run a single pipeline step against saved JSON artifacts.")
    step_parser.add_argument("--step", choices=["architect", "simulate", "critique", "refine", "suggest-tool"], required=True)
    step_parser.add_argument("--artifact-dir", required=True, help="Directory containing the JSON artifacts for this run.")
    step_parser.add_argument("--task", help="Required for the architect step.")

    run_parser = subparsers.add_parser("run-agent", help="Run the saved final agent.")
    run_parser.add_argument("--artifact-dir", help="Directory containing 08_final_agent.json or 04_ready_to_run.json.")
    run_parser.add_argument("--agent-file", help="Path to a saved final agent JSON file such as 08_final_agent.json.")
    run_parser.add_argument("--user-input", help="Optional user input. Defaults to the first example prompt.")

    eval_parser = subparsers.add_parser("eval", help="Run the saved ready-to-run agent against its example prompts and score the outputs.")
    eval_parser.add_argument("--artifact-dir", required=True, help="Directory containing 04_ready_to_run.json.")
    eval_parser.add_argument("--prompt", action="append", help="Optional prompt override. Can be provided multiple times.")

    create_tool_parser = subparsers.add_parser("create-tool", help="Use Mistral to generate a Python tool module that the agent runtime can call.")
    create_tool_parser.add_argument("--request", required=True, help="Describe the tool to generate.")

    suggest_tool_parser = subparsers.add_parser("suggest-tool", help="Run only the tool-gap analysis without executing the whole pipeline.")
    suggest_tool_parser.add_argument("--artifact-dir", help="Directory containing design and critique artifacts.")
    suggest_tool_parser.add_argument("--task", help="Task to analyze. Required if no artifact directory is provided or manifest is missing.")
    suggest_tool_parser.add_argument("--design-file", help="Optional path to a design JSON file. Defaults to 01_design.json in --artifact-dir.")
    suggest_tool_parser.add_argument("--critique-file", help="Optional path to a critique JSON file. Defaults to 03_critique.json in --artifact-dir.")

    subparsers.add_parser("list-tools", help="List built-in and generated runtime tools.")
    return parser


def has_task_argument(arguments: list[str]) -> bool:
    return "--task" in arguments


def parse_args() -> argparse.Namespace:
    parser = build_parser()
    if len(sys.argv) == 1:
        return parser.parse_args(["pipeline", "--task", DEFAULT_TASK])
    if sys.argv[1] in {"-h", "--help"}:
        return parser.parse_args()
    if not sys.argv[1] in KNOWN_COMMANDS:
        pipeline_args = ["pipeline", *sys.argv[1:]]
        if not has_task_argument(pipeline_args):
            pipeline_args.extend(["--task", DEFAULT_TASK])
        return parser.parse_args(pipeline_args)
    return parser.parse_args()


def main() -> None:
    parser = build_parser()
    args = parse_args()

    if args.command == "pipeline":
        artifact_dir = ensure_artifact_dir(args.run_id or slugify(args.task))
        run_pipeline(args.task, artifact_dir)
        if args.run_agent:
            print_step("Run Final Agent")
            print(json.dumps(run_saved_agent(artifact_dir=artifact_dir, user_input=args.user_input), indent=2, ensure_ascii=False))
        else:
            print(f"\nArtifacts saved in: {artifact_dir}")
        if args.eval:
            print_step("Evaluate Generated Agent")
            print(json.dumps(run_saved_agent_eval(artifact_dir), indent=2, ensure_ascii=False))
        return

    if args.command == "step":
        print(json.dumps(run_single_step(args.step, Path(args.artifact_dir), args.task), indent=2, ensure_ascii=False))
        return

    if args.command == "run-agent":
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else None
        agent_file = Path(args.agent_file) if args.agent_file else None
        if artifact_dir is None and agent_file is None:
            parser.error("run-agent requires --artifact-dir or --agent-file")
        print(json.dumps(run_saved_agent(artifact_dir=artifact_dir, agent_file=agent_file, user_input=args.user_input), indent=2, ensure_ascii=False))
        return

    if args.command == "eval":
        print(json.dumps(run_saved_agent_eval(Path(args.artifact_dir), args.prompt), indent=2, ensure_ascii=False))
        return

    if args.command == "create-tool":
        payload = generate_tool_module(args.request, call_mistral)
        print(json.dumps({"generated_tool": payload, "saved_files": save_generated_tool(payload)}, indent=2, ensure_ascii=False))
        return

    if args.command == "suggest-tool":
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else None
        design_file = Path(args.design_file) if args.design_file else None
        critique_file = Path(args.critique_file) if args.critique_file else None
        print(
            json.dumps(
                run_tool_gap_analysis(
                    artifact_dir=artifact_dir,
                    task=args.task,
                    design_file=design_file,
                    critique_file=critique_file,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.command == "list-tools":
        print(json.dumps(list_tools_payload(), indent=2, ensure_ascii=False))
        return

    parser.error("Unknown command")


if __name__ == "__main__":
    main()
