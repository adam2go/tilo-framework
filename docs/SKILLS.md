# Skill System

This document defines the skill system for Tilo Framework.

## 1. Skill Philosophy

A Tilo Skill is not just a prompt.

A Skill is a reusable capability package that can include instructions, input/output schemas, templates, examples, artifact templates, tool requirements, and optional executable code.

Skills should help agents perform repeated work more reliably.

## 2. Skill Goals

Skills should:

- encode reusable methods
- reduce repeated prompting
- improve output consistency
- connect to artifact templates
- connect to tool requirements
- support future self-improvement

## 3. Skill Package Structure

Future file-based skills can use this structure:

```text
skills/
  contract-review/
    skill.yaml
    instructions.md
    examples/
    templates/
    artifact.schema.json
    evals/
    scripts/
```

For v0.1, skills can be stored in the database first, but the model should anticipate file-based import later.

## 4. Skill Fields

Skill should include:

- id
- workspace_id
- name
- description
- trigger_description
- instructions_markdown
- input_schema_json
- output_schema_json
- artifact_template_json nullable
- required_tool_ids nullable
- version
- created_at
- updated_at

## 5. Skill Selection

For v0.1, skill selection can be simple:

1. Get enabled skills for the agent.
2. Match task input against skill name, description, and trigger description.
3. Include relevant skills in PromptBuilder.

Future versions may use embeddings and evaluations.

## 6. Skill and Artifact

Skills can define preferred artifact templates.

Example:

Contract Review Skill should prefer `contract_review` artifact.

Competitive Analysis Skill should prefer `document` + `table` artifact.

Sales Follow-up Skill should prefer `dashboard` + `confirmation_action` artifact.

## 7. Skill and Memory

Skills should specify what kind of memory should be extracted after execution.

Examples:

- Contract Review Skill: remember user risk tolerance and preferred clause style.
- Competitive Analysis Skill: remember preferred analysis dimensions.
- Sales Follow-up Skill: remember preferred tone and customer priority rules.

## 8. Skill Improvement

After task completion, the runtime may propose skill improvements.

For v0.1, this can be a placeholder:

- generate skill improvement candidates
- store them as unapproved suggestions
- do not auto-update skills without user confirmation

## 9. Default Skills for v0.1

Create these built-in skills as seed data or examples:

### Contract Review

Purpose:
- review contract text
- identify risks
- generate suggested revisions
- produce contract_review artifact

### Sales Follow-up

Purpose:
- analyze mock CRM/customer data
- recommend follow-up actions
- produce dashboard artifact
- create confirmation items for outbound messages

### Competitive Analysis

Purpose:
- generate competitor comparison
- summarize market landscape
- produce document/table artifact

## 10. Do Not Do

Do not:

- implement skills as only a prompt string forever
- let skills execute arbitrary code without permissions
- auto-install untrusted skills
- auto-update skills without user visibility
- duplicate demo logic outside skills and runtime
