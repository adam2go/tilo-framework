# Tilo User Guide / 使用指南

This guide explains how to run and use the current Tilo Console.

本文档说明如何启动和使用当前版本的 Tilo Console。

---

## 1. Start Tilo / 启动 Tilo

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

Open:

```text
http://localhost:3000
```

Backend health check:

```bash
curl http://localhost:8000/api/health
```

---

## 2. What You See / 当前页面结构

The current Console has three main areas:

当前 Console 主要分为三个区域：

```text
Left   : Agent Task input and demo prompts
Center : Generated Artifact result
Right  : Context panel: Trace / Memory / Skills / Files + Inbox
```

### Left Panel: Agent Task

Use this panel to send a task to the agent.

左侧用于输入任务或点击内置 Demo。

You can:

- click a demo prompt
- edit the prompt manually
- click `Send Message`

### Center Panel: Artifact

This is where Tilo renders the final result.

中间区域是结果交付区，也就是 Tilo 的 Artifact 页面。

Depending on the prompt, it may render:

- contract review artifact
- dashboard artifact
- competitive analysis table
- document artifact

### Right Panel: Context

The right panel helps you understand and control the run.

右侧区域用于理解和控制 Agent 运行过程。

Tabs:

- `Trace`: visible execution steps
- `Memory`: confirmed memories and memory candidates
- `Skills`: skills and skill candidates
- `Files`: reserved for future file-backed runs

The `Inbox` section shows pending human decisions.

---

## 3. First Run / 第一次运行

Try this prompt:

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Click `Send Message`.

Expected result:

1. Tilo creates a Task.
2. Tilo creates a Run.
3. Tilo recalls memory.
4. Tilo selects skills.
5. Tilo generates an artifact.
6. Tilo creates confirmations if needed.
7. Tilo creates memory candidates.
8. The UI shows artifact, trace, inbox, and memory.

---

## 4. Confirm Memory / 确认长期记忆

Open the `Memory` tab in the right panel.

You may see memory candidates.

Click `Confirm` to turn a candidate into confirmed long-term memory.

Why this matters:

- Candidate memory is not trusted by default.
- Confirmed memory can be recalled in future tasks.
- This is how Tilo starts to become personalized and project-aware.

---

## 5. Approve Confirmations / 审批确认项

The `Inbox` section shows pending decisions.

Click `Approve` to approve a confirmation.

Examples:

- approve a high-risk contract revision suggestion
- approve a recommended follow-up action
- approve a tool action in future versions

Tilo's philosophy is: agents execute, humans decide.

---

## 6. Try Built-in Demos / 内置 Demo

### Contract Review

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Expected output:

- contract review artifact
- risk items
- suggested revisions
- confirmation action

### Sales Follow-up

```text
Which customers should sales follow up with this week?
```

Expected output:

- dashboard artifact
- follow-up recommendations
- confirmation items

### Competitive Analysis

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Expected output:

- comparison table
- structured insight artifact
- memory candidate

---

## 7. Current Limitations / 当前限制

Tilo is still early.

Current limitations:

- UI is functional but not polished.
- Demo data is partly mocked.
- File upload is not fully implemented.
- Browser/MCP/real external tools are not production-ready yet.
- Memory recall is still evolving.
- Artifact pages are early but already schema-driven.

---

## 8. Recommended Next Product Improvements / 推荐下一步产品优化

For product experience, the next UI improvements should be:

1. Add onboarding cards on first load.
2. Make demo prompts more obvious.
3. Add step-by-step run progress.
4. Improve Artifact visual hierarchy.
5. Separate Inbox into a clearer decision center.
6. Add Memory Review page.
7. Add Skill Candidate Review page.
8. Add empty states and tooltips.
9. Add screenshot/GIF to README.
10. Add file-backed contract review flow.

See [`docs/UI_IMPROVEMENT_PLAN.md`](./UI_IMPROVEMENT_PLAN.md).

---

## 9. Mental Model / 使用心智模型

Do not use Tilo like a normal chatbot.

不要把 Tilo 当成普通聊天机器人。

Use it like this:

```text
I give a goal.
Tilo creates a task.
The agent runs.
The result becomes an artifact.
I approve key decisions.
Useful context becomes memory.
Next time, Tilo works better.
```

This is the key product loop.
