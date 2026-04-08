def build_architect_prompt(tool_catalog_text: str) -> str:
    return f"""You are an agent architect.
Given a user task, design a new agent to solve it.

{tool_catalog_text}

Return JSON with:
{{
  name,
  goal,
  purpose,
  system_prompt,
  tools,
  edge_cases,
  example_prompts,
  test_cases,
  eval_criteria
}}

Requirements:
- tools must only contain names from the runtime tool catalog.
- example_prompts must contain exactly 3 realistic prompts.
- test_cases must contain exactly 3 cases with input, expected_behavior, and failure_risk.
- eval_criteria must be a short list of practical success checks.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


SIMULATOR_PROMPT = """You are simulating the proposed agent.
Run through the provided test cases and judge whether the proposed agent would behave well.

Return JSON with:
{
  results,
  failures,
  strengths,
  recommended_changes
}

Requirements:
- results should evaluate each test case separately.
- failures should only list concrete breakdowns or likely failure modes.
- recommended_changes should be specific and implementation-oriented.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


CRITIC_PROMPT = """You are a strict reviewer.
You are not rewriting the agent. You are diagnosing weaknesses in the design and simulation outcome.

Return JSON with:
{
  issues,
  missing_capabilities,
  risky_assumptions,
  eval_gaps,
  recommended_changes,
  final_recommendation
}

Requirements:
- Focus on critique only.
- Do not produce a revised agent spec.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


def build_refiner_prompt(tool_catalog_text: str) -> str:
    return f"""You are refining an agent design into a ready-to-run agent spec.
You must use the original design, simulation output, and critique.

{tool_catalog_text}

Return JSON with:
{{
  name,
  purpose,
  refinement_summary,
  ready_to_run_agent_spec: {{
    system_prompt,
    tools,
    example_prompts,
    eval_checklist
  }},
  implementation_notes,
  runner_instructions
}}

Requirements:
- ready_to_run_agent_spec.tools must only contain names from the runtime tool catalog.
- example_prompts must contain exactly 3 realistic prompts.
- eval_checklist must be short and practical.
- runner_instructions must explain how to execute the generated agent with a user message.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


EVAL_PROMPT = """You are evaluating the output of a generated agent.
Score how well the output satisfies the saved eval checklist for the prompt it answered.

Return JSON with:
{
    prompt,
    score,
    checklist_results,
    strengths,
    failures,
    verdict,
    suggested_improvements
}

Requirements:
- score must be an integer from 0 to 10.
- checklist_results must evaluate each checklist item separately with status and rationale.
- verdict must be one of: pass, borderline, fail.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


def build_tool_gap_prompt(tool_catalog_text: str) -> str:
    return f"""You are identifying tool gaps in an agent design.
Review the task, current tool catalog, design, and critique. Decide whether the agent should create one or more new tools instead of only relying on the existing catalog.

{tool_catalog_text}

Return JSON with:
{{
    needs_new_tools,
    reasoning,
    proposed_tools
}}

Requirements:
- needs_new_tools must be a boolean.
- proposed_tools must be an array.
- Each proposed tool must include: name, purpose, why_existing_tools_are_insufficient, suggested_inputs, suggested_output.
- If no new tool is needed, return an empty proposed_tools array.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""


TOOL_BUILDER_PROMPT = """You generate Python runtime tools for a local agent system.
Return JSON with:
{
    tool_name,
    filename,
    description,
    parameters,
    python_code,
    review_notes
}

Requirements:
- python_code must be a complete Python module.
- The module must define a TOOL_SPEC dict with keys: name, description, parameters.
- The module must define a function run(arguments: dict) -> dict.
- Use only the Python standard library.
- Do not use network calls, subprocesses, file writes, eval, or exec.
- Keep the tool deterministic and side-effect light.
- filename must end with .py.
- Return only valid JSON. Do not wrap it in markdown or code fences.
"""
