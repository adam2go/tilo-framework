# Tilo Framework

<p align="center">
  <strong>围绕 ROAM Loop 构建 AI 原生 SaaS Agent：渲染、观察、行动、记忆。</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./docs/ROAM_LOOP.md">ROAM Loop</a> ·
  <a href="./docs/ROAM_INTERACTION_CONTRACT.md">Interaction Contract</a> ·
  <a href="./docs/INTEROPERABILITY.md">互操作性</a> ·
  <a href="./docs/AI_NATIVE_INTERACTION_COMPONENTS.md">AI 原生交互组件</a> ·
  <a href="./docs/USER_GUIDE.md">使用指南</a> ·
  <a href="./docs/V0_2_CODEX_PLAN.md">v0.2 开发计划</a> ·
  <a href="./evals/README.md">Evals</a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/adam2go/tilo-framework" />
  <img alt="Stars" src="https://img.shields.io/github/stars/adam2go/tilo-framework?style=social" />
  <img alt="Forks" src="https://img.shields.io/github/forks/adam2go/tilo-framework?style=social" />
  <img alt="Issues" src="https://img.shields.io/github/issues/adam2go/tilo-framework" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/adam2go/tilo-framework" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-frontend-black" />
</p>

---

## Tilo 是什么？

**Tilo 是一个开源框架，用于构建 AI 原生 SaaS Agent：它可以渲染交互式产品界面，观察用户行为，继续执行任务，并把确认后的经验沉淀为长期记忆。**

Tilo 提出了一个核心框架：**ROAM Loop**。

```text
Render -> Observe -> Act -> Memorize
渲染 -> 观察 -> 行动 -> 记忆
```

很多 Agent 框架关注推理、工具调用、工作流编排或多智能体协作。Tilo 更关注另一个问题：

> 如果用户界面本身也成为 Agent Loop 的一部分，会发生什么？

在 Tilo 中，Agent 不只是返回文本或调用工具。它可以渲染类 SaaS 的交互式 Artifact，观察用户如何审批、编辑、选择、拒绝和修正这些 Artifact，再基于这些观察继续行动，并把确认后的信息变成长期记忆。

Tilo 不是聊天机器人外壳，而是一个 **AI 原生 SaaS 交互框架**。

---

## ROAM Loop

传统 ReAct 类 Agent Loop 通常把 Observation 理解成工具结果或环境反馈。

Tilo 扩展了这个观点：

> 用户与生成界面的交互，本身也是 Observation。

```text
Render
  Agent 渲染一个交互式 Artifact 或组件界面。

Observe
  系统把用户点击、编辑、审批、选择、反馈和工具结果记录为结构化观察。

Act
  Agent 基于观察继续行动：更新 Artifact、调用工具、创建确认项、追问澄清问题或启动后续任务。

Memorize
  被确认的决策、偏好、项目事实和可复用流程沉淀为可检查的长期记忆。
```

ROAM 让 UI 不再只是展示层，而成为 Agent Runtime 的一部分。

| 传统 Agent Loop | Tilo ROAM Loop |
|---|---|
| Observation 多来自工具结果 | Observation 也来自用户和 UI 的交互 |
| 输出通常是文本或工具结果 | 输出是可交互的 Artifact 页面 |
| UI 在 Loop 外部 | UI 是 Loop 的一部分 |
| Human-in-the-loop 多数是审批 | 用户交互成为结构化 Observation |
| Memory 是可选能力 | Memory 是闭环的一部分 |

更多说明见：[`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md)

---

## 为什么需要 Tilo？

传统 SaaS 让用户操作软件：

```text
打开系统 -> 找功能 -> 填表单 -> 点按钮 -> 看结果 -> 再判断下一步
```

Tilo 探索的是 AI 原生 SaaS 交付：

```text
描述目标 -> Agent 渲染 Artifact -> 用户交互 -> Agent 行动 -> 记忆让下次更好
```

这意味着很多传统 SaaS 组件都可以被 Agent 生成的 AI 原生交互组件替代：

| 传统 SaaS | Tilo AI 原生替代 |
|---|---|
| 表单 | 对话目标 + 澄清组件 |
| 表格 | DecisionTable / ComparisonMatrix |
| 仪表盘 | 带下一步动作的 MetricDashboard |
| 确认弹窗 | 持久化 Confirmation / ApprovalCard |
| 工作流步骤条 | Agent Run Progress + ActionQueue |
| 设置页 | Memory / Tool / Skill review components |
| 报告页 | 可交互 Artifact 页面 |
| 通知中心 | 待处理决策 Inbox |
| CRUD 编辑器 | 带版本历史的 EditableArtifact |

更多说明见：[`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md)

---

## ROAM Interaction Contract

Tilo 提供一个轻量的声明式 interaction contract 层，用来连接 AI 原生 SaaS Agent、界面、人类操作、结构化观察和长期记忆。Contract 描述 Agent 应该渲染什么、哪些用户动作需要被观察、哪些动作需要确认，以及哪些结果可以进入记忆候选。

它是 Tilo 内部可落地的连接层，不把自己包装成通用标准，也不替代现有 Agent 协议。

- Contract 设计：[`docs/ROAM_INTERACTION_CONTRACT.md`](./docs/ROAM_INTERACTION_CONTRACT.md)
- 具体示例：[`examples/interaction-contracts/contract-review.roam.yaml`](./examples/interaction-contracts/contract-review.roam.yaml)

---

## 互操作性

Tilo 设计上应该兼容更大的 Agent 生态，而不是把自己做成孤岛：

- MCP 连接工具和资源。
- A2A 风格协议可以连接 Agent 之间的交接与协作。
- Skills 封装可复用能力。
- LangGraph、LlamaIndex、CrewAI、AutoGen 或自定义 Runtime 仍然可以负责编排与检索。
- Tilo 通过 ROAM 连接 Agent、UI、人类、观察和记忆。

更多说明见：[`docs/INTEROPERABILITY.md`](./docs/INTEROPERABILITY.md)

---

## 核心能力

### 1. ROAM-native 交互层

Tilo 把交互组件作为运行时原语。

- ApprovalCard
- RiskReviewPanel
- ComparisonMatrix
- MetricDashboard
- MemoryCandidateCard
- ToolCallPreview
- ActionQueue
- EditableDocument placeholder
- UIInteractionEvent 模型方向

### 2. AI 原生 Artifact 交付

Agent 的输出不应该只是一段 Markdown，而应该是可用的产品界面。

- `artifact_spec.v1`
- Schema-driven 渲染
- Renderer Registry
- Artifact Actions
- State Bindings
- 与 Confirmation 关联的动作
- 持久化 Artifact 页面

### 3. 长期记忆

Tilo 把记忆作为一等公民，而不是简单保存聊天记录。

- 结构化记忆
- 记忆候选
- 用户确认后才进入长期记忆
- Workspace / Project 级别召回
- 记忆召回事件
- 记忆写入事件
- 为 embedding / rerank 预留扩展空间

### 4. Agent 自我改进

Tilo 内置安全的自我改进原语。

- Run Metrics
- Feedback Records
- Skill Candidates
- Skill 晋升前需要人类审核
- Eval 脚手架
- 默认不允许危险的自动自我修改

### 5. 人类决策 Inbox

人不应该操作每一步流程，而应该确认关键决策。

- 持久化 Confirmation
- Approve / Reject / Edit 流程
- 高风险工具调用拦截
- 待处理决策队列

### 6. 可追踪 Runtime

每次运行都会产生安全、可见的执行轨迹。

- Task / Run 生命周期
- Trace Steps
- Trace 输出脱敏
- 失败运行处理
- Tool Invocation Ledger

---

## 架构

```text
┌─────────────────────────────────────────────────────────┐
│                    Tilo Console                         │
│ Conversation / Artifact Surface / Context / Inbox       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    ROAM Runtime                         │
│      Render -> Observe -> Act -> Memorize               │
└──────────────┬─────────────┬───────────────┬────────────┘
               │             │               │
┌──────────────▼───┐ ┌───────▼───────┐ ┌────▼─────────────┐
│ Artifact Engine  │ │ Observation   │ │ Agent Runtime    │
│ Spec / Registry  │ │ UI Events     │ │ Planner/Executor │
└──────────────┬───┘ └───────┬───────┘ └────┬─────────────┘
               │             │              │
┌──────────────▼─────────────▼──────────────▼─────────────┐
│ Memory Engine / Skill System / Tool Registry / Inbox    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│              PostgreSQL + pgvector + Redis              │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- 如果手动运行前端，需要 Node.js 18+
- 如果手动运行后端，需要 Python 3.11+

### 使用 Docker Compose 启动

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

检查后端健康状态：

```bash
curl http://localhost:8000/api/health
```

打开前端控制台：

```text
http://localhost:3000
```

### 运行本地 Evals

```bash
python3 evals/runners/run_memory_recall_eval.py
python3 evals/runners/run_artifact_schema_eval.py
python3 evals/runners/run_runtime_loop_eval.py
```

---

## 如何使用当前 Console？

当前 UI 是一个早期单页 ROAM Console。

1. 打开 `http://localhost:3000`。
2. 选择一个 Demo Prompt，或者输入自己的任务。
3. 点击 **Send Message**。
4. Tilo 会创建 Task 和 Run。
5. Agent 在中间区域渲染 Artifact。
6. 右侧区域可以查看 Trace、Memory、Skills、Files 和 Inbox。
7. 与生成组件交互：审批动作、确认记忆、审查建议。
8. 这些交互会成为后续运行的 Observation。
9. 被确认的记忆可以在下次任务中被召回。

当前内置 Demo：

- 合同审查
- 销售跟进
- 竞品分析

更详细说明见 [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md)。

---

## 示例场景

### 合同审查 Agent

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Tilo 应该渲染合同审查界面，包括风险面板、修改建议、审批卡片和记忆候选。

### 销售跟进 Agent

```text
Which customers should sales follow up with this week?
```

Tilo 应该渲染销售仪表盘和决策表，并生成待审批动作。

### 竞品分析 Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo 应该渲染对比矩阵、方案选择、证据卡片和后续动作。

---

## 当前状态

Tilo 目前处在早期 v0.2/v0.3 设计与实现阶段。

| 模块 | 状态 |
|---|---|
| Runtime loop | 已有基础闭环 |
| ROAM Loop concept | 已文档化 |
| AI-native interaction components | 已设计，待实现 |
| Artifact spec v1 | 已有基础能力 |
| Renderer registry | 已有基础能力 |
| Memory candidates | 已有基础能力 |
| Recall / write events | 已有基础能力 |
| Human confirmation | 已有基础能力 |
| Tool permission gate | 已有基础能力 |
| Self-improvement primitives | 早期基础能力 |
| Evals | 本地脚手架 |
| UI polish | 需要大幅优化 |

当前 UI 能跑通功能，但还不足以作为公开展示。下一优先级是实现 ROAM-native interaction components。

---

## Roadmap

### v0.3: ROAM Interaction Layer

- 把 ROAM 写入 README 和产品文档
- 增加 UIInteractionEvent 模型
- 扩展 Artifact actions 和 state bindings
- 建立交互组件注册表
- 实现 ApprovalCard、RiskReviewPanel、ComparisonMatrix、MetricDashboard、MemoryCandidateCard、ToolCallPreview、ActionQueue
- 围绕 conversation + generated interaction surface 重构 Console
- 让组件动作写入持久化后端状态

### v0.4: Memory and Self-improvement

- Hybrid semantic memory recall
- Memory conflict resolver
- Skill candidate review and promotion
- Feedback-driven improvement loop
- 更强的 eval benchmarks

### v0.5+

- MCP integration
- Browser and GUI automation
- Artifact 分享与发布
- Telegram / Slack / Discord / 微信风格适配器
- 多用户 Workspace 权限
- Skill Marketplace 原语

---

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date&theme=dark" />
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date" />
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date" />
</picture>

---

## 仓库结构

```text
backend/       FastAPI 后端、领域模型、Runtime、Memory、Tools、Artifacts
frontend/      Next.js Console、Artifact Renderer、Memory/Trace/Inbox 面板
docs/          产品原则、ROAM Loop、架构、使用指南、实现计划
evals/         Memory、Artifact、Runtime loop 本地评测脚手架
```

---

## 文档

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md) — Tilo 的核心交互循环
- [`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md) — AI 原生 SaaS 组件体系
- [`docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md`](./docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md) — ROAM 的 Codex 执行计划
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md) — 项目宪法
- [`docs/PRODUCT_PRINCIPLES.md`](./docs/PRODUCT_PRINCIPLES.md) — 产品原则
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — 系统架构
- [`docs/MEMORY.md`](./docs/MEMORY.md) — 记忆系统设计
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — Artifact 协议
- [`docs/SKILLS.md`](./docs/SKILLS.md) — Skill 系统
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API 契约
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md) — 使用指南

---

## 贡献

Tilo 还很早期，欢迎参与贡献。

贡献前请阅读：

- [`AGENTS.md`](./AGENTS.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)
- [`docs/QUALITY_BAR.md`](./docs/QUALITY_BAR.md)

最重要的一条：

> 不要把 Tilo 做成简单聊天机器人。请始终保留 ROAM Loop：Render、Observe、Act、Memorize。

---

## License

Apache License 2.0
