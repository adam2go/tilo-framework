# Social Launch Posts for Tilo

This file contains draft posts for launching and continuously sharing Tilo on X.

Project message:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

Repo:

```text
https://github.com/adam2go/tilo-framework
```

---

## 1. Launch Post

I’m building Tilo, an open-source framework for AI-native SaaS agents.

The core idea:

Chat is the entry.
Surface is the workspace.
Interaction becomes memory.

Agents should not only reply in text. They should render interactive product surfaces, observe human actions, act safely, and memorize confirmed learning.

GitHub: https://github.com/adam2go/tilo-framework

---

## 2. Demo Screenshot Post

Tilo now has a Telegram-like demo running with a real LLM mode.

Left: chat-like task entry  
Center: rich ROAM surface  
Right: developer inspector

The demo shows contract review as an AI-native SaaS workflow:

Render risk surface → observe approval → act on revision → memorize preference.

GitHub: https://github.com/adam2go/tilo-framework

---

## 3. ROAM Loop Post

Most agent loops treat observation as tool output.

Tilo extends this:

Human interaction with generated UI is also observation.

ROAM Loop:

Render → Observe → Act → Memorize

This makes UI part of the agent runtime, not just a display layer.

---

## 4. Why Not Just Chat Post

I don’t think AI-native SaaS will be just chat windows.

Chat is great for intent.
But complex work needs surfaces:

- review panels
- approval cards
- editable drafts
- dashboards
- comparison matrices
- memory review

Tilo explores this pattern:

Chat starts the task. Surfaces deliver the work.

---

## 5. Interaction Contract Post

A missing layer in agent apps:

When should the agent ask the user?
What UI should appear?
What happens after approval/edit/reject?
What should become memory?

Tilo calls this a ROAM Interaction Contract.

It’s a lightweight declarative layer, not a new standard.

---

## 6. Interoperability Post

Tilo is not trying to replace existing agent frameworks.

My mental model:

MCP connects tools.
A2A connects agents.
Skills package capabilities.
LangGraph/LlamaIndex/etc. orchestrate logic.
Tilo connects agents, UI, humans, observations, and memory.

---

## 7. LLM Mode Post

Tilo’s demo now supports two modes:

1. deterministic mode
   runs locally without an API key

2. LLM mode
   uses OpenAI-compatible providers

That means you can clone it and run the demo immediately, or connect your own model gateway.

---

## 8. Contract Review Demo Thread

1/ I’m using contract review as Tilo’s first showcase demo.

Why?

Because it naturally requires:
- analysis
- risk review
- human approval
- document revision
- memory

Perfect for proving AI-native SaaS interaction.

2/ In a normal chatbot, contract review becomes a long text answer.

In Tilo, the agent renders a rich surface:

- risk summary
- active risk node
- recommended revision
- approval actions
- memory candidate

3/ The user approves a revision.

That click is not just a frontend event.

It becomes a durable observation that can trigger actions and memory.

That’s the ROAM idea:

Render → Observe → Act → Memorize

4/ The UI is not outside the agent loop.

The UI is part of the loop.

This is the part I think many AI SaaS products will need.

GitHub: https://github.com/adam2go/tilo-framework

---

## 9. Developer-Focused Post

If you’re building agent apps, one hard problem is not only tool calling.

It’s interaction design:

- when to ask for approval
- when to show a rich surface
- how to capture user decisions
- how to connect actions back to memory

Tilo is an attempt to make this explicit.

---

## 10. Daily Build Log Template

Today’s Tilo build log:

- Improved: [what changed]
- Learned: [one insight]
- Next: [what I’m building next]

Current thesis:

Chat is the entry. Surface is the workspace. Interaction becomes memory.

GitHub: https://github.com/adam2go/tilo-framework

---

## 11. Short Post Variants

Chat is the entry.
Surface is the workspace.
Interaction becomes memory.

That’s the whole Tilo thesis.

---

Agents should not only call tools.
They should render interfaces, observe how humans use them, act safely, and learn from confirmed decisions.

---

The next frontier for agent frameworks might not be another planner.

It might be the interaction layer.

---

A button click can be more than a UI event.

In an agent system, it can be an observation.

---

I’m building Tilo because I think AI-native SaaS needs a new loop:

Render → Observe → Act → Memorize

---

## 12. Chinese Posts

我在做一个开源项目 Tilo。

核心想法很简单：

聊天是入口，Surface 是工作区，交互成为记忆。

未来的 AI 原生 SaaS 不应该只是聊天框，而应该让 Agent 生成可交互的业务界面，并把用户确认过的动作沉淀成长期记忆。

GitHub: https://github.com/adam2go/tilo-framework

---

很多 Agent 框架都在讲工具调用、工作流、多 Agent。

但我觉得还有一层很重要：

Agent 如何和人交互？
什么时候需要审批？
什么时候需要展示页面？
用户点击后如何继续执行？
哪些东西应该进入记忆？

Tilo 想探索的就是这层。

---

我给 Tilo 定义了一个 ROAM Loop：

Render → Observe → Act → Memorize

渲染界面，观察用户动作，继续执行任务，沉淀长期记忆。

这个思路的关键是：

用户和 UI 的交互，本身也是 Agent 的 Observation。

---

Tilo 现在已经有一个 Telegram-like Demo。

左侧是聊天入口，
中间是 LLM 生成的合同审查 Surface，
右侧是开发者 Inspector。

它想证明一件事：

复杂业务交互不应该硬塞进聊天气泡，而应该进入 Rich Surface。

---

## 13. Posting Rhythm

Recommended rhythm:

### Week 1: Explain the concept

- Day 1: launch post
- Day 2: ROAM Loop post
- Day 3: why not just chat
- Day 4: demo screenshot
- Day 5: interaction contract
- Day 6: interoperability
- Day 7: build log

### Week 2: Show implementation details

- contract review demo
- LLM mode
- UIInteractionEvent
- artifact_spec.v1
- memory candidate flow
- Telegram-like entry
- deterministic local mode

### Week 3: Invite builders

- ask for contributors
- ask for use cases
- ask agent builders what UI problems they face
- invite legal/sales/HR demo contributors
- share roadmap

---

## 14. Reminder

For X, post screenshots or short videos whenever possible.

The strongest visual is:

```text
Left: chat-like entry
Center: LLM-generated ROAM surface
Right: developer inspector
```

Use the screenshot to make the concept obvious before people read the thread.
