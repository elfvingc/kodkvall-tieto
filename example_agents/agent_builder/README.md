# Agent Builder

This script builds a meta-agent pipeline with four explicit stages:

1. architect
2. simulate
3. critique
4. refine

It saves each stage as JSON so you can rerun only one step later, and it can also run the saved ready-to-run agent spec.

Running the script without arguments defaults to the full pipeline using a built-in demo task.

It can also use Mistral to generate Python tool modules that are saved locally and become callable by future generated agents.

## File Layout

- `main.py`: the main demo flow and core concepts: pipeline orchestration, tool-calling loop, final agent execution
- `prompts.py`: prompt templates for architect, simulator, critic, refiner, evaluator, and tool-gap review
- `runtime_tools.py`: built-in tools, generated tool loading, and generated tool validation
- `utils.py`: Mistral client setup, JSON extraction, and artifact helpers

## Setup

```bash
cd <repo>/agent_builder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MISTRAL_API_KEY="..."
```

Optional:

```bash
export MISTRAL_MODEL="mistral-small-latest"
```

The agent builder uses the same import style as [python/example_v1.py](<repo>/python/example_v1.py): `from mistralai import Mistral`, so the pinned requirement targets that SDK shape.

## Full Pipeline

```bash
python main.py pipeline \
  --task "Build an agent that helps sales reps prepare for customer meetings" \
  --run-id sales-meeting-demo \
  --run-agent
```

You can also evaluate the generated agent immediately:

```bash
python main.py pipeline \
  --task "Build an agent that helps sales reps prepare for customer meetings" \
  --run-id sales-meeting-demo \
  --run-agent \
  --eval
```

If you run with no arguments, the script behaves like:

```bash
python main.py pipeline --task "Build an agent that helps sales reps prepare for customer meetings"
```

Artifacts are saved under `agent_builder/artifacts/<run-id>/`:

- `00_manifest.json`
- `01_design.json`
- `02_simulation.json`
- `03_critique.json`
- `04_ready_to_run.json`
- `08_final_agent.json` with the standalone runnable final agent
- `05_agent_run.json` if you run the generated agent
- `06_eval.json` if you run evaluation
- `07_tool_opportunities.json` with suggested missing tools for the task

## Run Only One Step

Example: rerun only the refine step after editing earlier JSON files.

```bash
python main.py step \
  --step refine \
  --artifact-dir <repo>/agent_builder/artifacts/sales-meeting-demo
```

You can run any of these steps:

- `architect` with `--task`
- `simulate`
- `critique`
- `refine`
- `suggest-tool`

## Run the Saved Agent

```bash
python main.py run-agent \
  --artifact-dir <repo>/agent_builder/artifacts/sales-meeting-demo \
  --user-input "Prepare me for a meeting with a CFO at a mid-sized manufacturing company."
```

You can also run the standalone final agent file directly:

```bash
python main.py run-agent \
  --agent-file <repo>/agent_builder/artifacts/sales-meeting-demo/08_final_agent.json \
  --user-input "Prepare me for a meeting with a CFO at a mid-sized manufacturing company."
```

If `--user-input` is omitted, the script uses the first prompt from `example_prompts` in `04_ready_to_run.json`.

The practical final agent artifact is `08_final_agent.json`. That is the cleanest file to keep or hand off if you want to run the generated agent later without depending on the whole pipeline result shape.

## Evaluate the Saved Agent

```bash
python main.py eval \
  --artifact-dir <repo>/agent_builder/artifacts/sales-meeting-demo
```

This runs the saved agent against its `example_prompts`, scores each output against `eval_checklist`, and writes the result to `06_eval.json`.

You can also override prompts:

```bash
python main.py eval \
  --artifact-dir <repo>/agent_builder/artifacts/sales-meeting-demo \
  --prompt "Prepare me for a procurement meeting with a skeptical CFO." \
  --prompt "Summarize the likely objections for a VP of Sales."
```

## Generate a New Tool

```bash
python main.py create-tool \
  --request "Create a tool named build_account_brief that turns CRM notes into a structured account brief with risks, opportunities, and next actions."
```

This saves files under `agent_builder/generated_tools/`:

- `<tool-name>.py` with the runtime module
- `<tool-name>.json` with metadata about the generated tool

On the next pipeline run, the architect and refiner stages can include that tool in the generated agent spec, and the runtime can call it.

Review generated tool code before relying on it. The generator is constrained to a fixed module contract, but the code is still model-written Python.

Generated tool code is also validated before saving. The validator rejects disallowed imports and risky calls such as `subprocess`, `socket`, `eval`, `exec`, and file I/O patterns.

## List Available Tools

```bash
python main.py list-tools
```

This prints both built-in tools and any generated tools currently loaded from `generated_tools/`.

## Suggest Missing Tools Only

```bash
python main.py suggest-tool \
  --artifact-dir <repo>/agent_builder/artifacts/sales-meeting-demo
```

You can also point it at explicit files:

```bash
python main.py suggest-tool \
  --task "Build an agent that helps sales reps prepare for customer meetings" \
  --design-file <repo>/agent_builder/artifacts/sales-meeting-demo/01_design.json \
  --critique-file <repo>/agent_builder/artifacts/sales-meeting-demo/03_critique.json
```

## Critique vs Refine

- `critique` diagnoses problems, gaps, risky assumptions, and evaluation weaknesses.
- `refine` synthesizes a new ready-to-run spec from the design, simulation, and critique outputs.

That separation makes it easier to iterate on only the refining behavior by keeping `01_design.json`, `02_simulation.json`, and `03_critique.json` fixed while rerunning `refine`.

## Runtime Tools

The generated agent is limited to a built-in tool catalog so it is actually runnable:

- `summarize_input`
- `extract_key_points`
- `generate_checklist`
- `brainstorm_scenarios`
- `draft_structured_brief`
- `compare_options`
- `identify_followups`
- `prioritize_actions`

Generated tools saved under `generated_tools/` are also loaded automatically if they expose:

- `TOOL_SPEC`
- `run(arguments)`

The full pipeline now also runs a tool-gap review and writes `07_tool_opportunities.json`, which suggests when a new tool should be created instead of only selecting from the current catalog.

If you need richer tools later, extend the tool registry in `main.py` and allow the architect/refiner prompts to use them.