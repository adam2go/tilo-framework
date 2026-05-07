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
  <a href="./docs/CONVERSATION_RUNTIME.md">Conversation Runtime</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/USER_GUIDE.md">使用指南</a>
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

<p align="center">
  <img alt="Tilo Framework 项目总览：围绕 ROAM Loop 构建 AI 原生 SaaS Agent Runtime" src="./docs/assets/tilo-framework-overview.svg" />
</p>

---

## Tilo 是什么？

**Tilo 是一个开源框架，用于构建 AI 原生 SaaS Agent：它可以渲染交互式产品界面，观察用户决策，继续调用工具行动，并把确认后的经验沉淀为长期记忆。**

很多 Agent 框架关注推理、工具调用、工作流编排或多智能体协作。Tilo 更关注另一个问题：

> 如果用户界面本身也成为 Agent Runtime 的一部分，会发生什么？

在 Tilo 中，Agent 不只是返回文本或调用工具。它可以渲染类 SaaS 的 Artifact，观察用户如何审批、编辑、选择、拒绝和修正这些 Artifact，再基于这些观察继续行动，并把确认后的信息变成长期记忆。

Tilo 不是聊天机器人外壳，而是一个 **AI 原生 SaaS 交互 Runtime**。

---

## 核心思想：ROAM Loop

Tilo 提出了 **ROAM Loop**：

```text
Render -> Observe -> Act -> Memorize
渲染 -> 观察 -> 行动 -> 记忆
```

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

## Runtime 架构

```text
Agent App Manifest
        ↓
Interaction Policy
        ↓
Mini / Rich Surface
        ↓
UIInteractionEvent
        ↓
ConversationTurn(observation)
        ↓
AgentContextBuilder
        ↓
PromptBuilder
        ↓
Agent Runtime
        ↓
Memory Candidate -> Human Confirmation -> Confirmed Memory
```

Tilo 围绕几个核心运行时原语构建：

- **Agent App Manifest**：声明式定义应用身份、入口 prompt、可用 surfaces、样例输入、工具和渠道。
- **Interaction Policy**：后端决策源，决定 Agent 何时继续静默执行、何时追问、何时展示 mini surface、何时打开 rich surface。
- **Mini Surface Registry**：渲染在对话中的轻量决策卡片。
- **Rich Surface Link**：按需打开完整 Artifact 页面、抽屉或 WebView。
- **Conversation Runtime**：跨 Web、Telegram 和未来渠道的持久会话与 turns。
- **UI Observations**：用户动作会变成结构化运行时观察。
- **Context Reflection**：通过 ORID 风格反思，把原始交互转成可解释的下一步动作和记忆候选。
- **Memory Lifecycle**：观察不会自动成为长期记忆，必须经过用户确认。

---

## 当前能力

### Conversation-first runtime

- `ConversationSession` 和 `ConversationTurn`
- Web demo 通过 `session_id` 恢复会话
- Telegram 文本 / callback 映射
- Append-only 持久 turns
- Channel-friendly runtime model

### ROAM-native 交互层

- 对话内 mini surfaces
- Rich surface escalation
- UIInteractionEvent 持久化
- Observation turns 与交互事件关联
- 后端 interaction policy evaluation

### Artifact 交付

- `artifact_spec.v1`
- Schema-driven 渲染
- Renderer registry
- Artifact actions
- State bindings
- 与 Confirmation 关联的动作

### 记忆与上下文

- 结构化 Memory records
- Memory candidates
- 用户确认后才进入长期记忆
- Workspace / Project 级别召回
- Memory recall / write events
- ORID-inspired context reflection plan

### 开发者体验

- 声明式 example apps
- App manifest loader
- Policy surface validation
- Sales Follow-up 第二个示例应用
- 极简 app scaffold script
- 本地 eval scaffolding

---

## 公开 Demo

运行类 Telegram 的 ROAM showcase：

```bash
docker compose up --build
```

然后打开：

```text
http://localhost:3000/demo/telegram
```

Demo 支持确定性本地模式，也支持通过 OpenAI-compatible 配置启用后端 LLM 模式。API key 只保存在后端 `.env`，不会暴露到前端。

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

## 构建一个 Agent App

Tilo app 可以用声明式方式定义，而不是硬编码在某个 demo 里。

可以从合同审查示例开始：

```text
examples/apps/contract-review-agent/app.yaml
examples/apps/contract-review-agent/interaction.policy.yaml
```

一个 Tilo app 通常包含：

```text
app.yaml
interaction.policy.yaml
fixtures or sample inputs
optional README
```

Manifest 定义 app 的入口 prompt、运行时 fallback 行为、允许的 mini/rich surfaces、样例输入、工具和渠道。Policy 决定 Agent 何时 `no_ui`、展示 `mini_surface`、打开 `rich_surface` 或 `ask_text`。

添加新 app：

1. 复制 `examples/apps/contract-review-agent/`，或运行 `python scripts/create_app.py my-agent`。
2. 修改 `app.yaml` 中的 identity、entry prompt、surfaces、sample inputs、tools 和 channels。
3. 修改 `interaction.policy.yaml`，让 UI 只在真正有决策价值时出现。
4. 打开 `GET /api/apps` 确认 manifest 加载成功。
5. 复用或新增 frontend mini surface registry 中的组件。

开发者参考：

- [`docs/APP_MANIFEST.md`](./docs/APP_MANIFEST.md)
- [`docs/INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)
- [`docs/MINI_SURFACE_REGISTRY.md`](./docs/MINI_SURFACE_REGISTRY.md)
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`examples/apps/README.md`](./examples/apps/README.md)

---

## 示例场景

### 合同审查 Agent

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Tilo 会渲染合同审查界面，包括风险面板、修改建议、审批卡片和记忆候选。

### 销售跟进 Agent

```text
Which customers should sales follow up with this week?
```

Tilo 会渲染客户跟进建议、决策卡片、草稿动作和偏好记忆候选。

### 竞品分析 Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo 可以渲染对比矩阵、方案选择、证据卡片和后续动作。

---

## 当前状态

Tilo 还很早期，但正在从 demo 走向真正的开源 agent app runtime。

| 模块 | 状态 |
|---|---|
| ROAM Loop concept | 已文档化 |
| Artifact spec v1 | 已有基础能力 |
| Conversation runtime | 已有基础能力 |
| UI observations | 已有基础能力 |
| Agent context bridge | 已有基础能力 |
| Interaction policy | 已有基础能力 |
| Rich surface escalation | 已有基础能力 |
| Memory candidates | 已有基础能力 |
| Telegram mapping | 早期基础能力 |
| ORID context reflection | 规划 / 开发中 |
| UI polish | 需要继续优化 |

---

## Roadmap

### v0.5: Conversation Runtime and Multi-app

- 持久会话 sessions 和 turns
- Session-aware agent context
- Rich surface escalation
- Telegram mapping
- Sales Follow-up 示例 app

### v0.6: Runtime Hardening and Developer Experience

- ConversationService
- Typed runtime primitives
- Centralized observation linkage
- 更清晰的 prompt context shape
- 开发者 app guide 和 scaffold script

### v0.7: ORID Context Reflection and Runtime Closure

- Run-to-session context closure
- Conversation-native message endpoint
- UIInteractionEvent to observation turn automation
- ORID-style context reflection
- Explainable memory candidates

### Future

- MCP integration
- Browser and GUI automation
- Artifact 分享与发布
- Slack / Discord / 微信风格适配器
- 多用户 Workspace 权限
- Skill marketplace primitives

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
examples/      声明式 agent app examples 和 fixtures
scripts/       小型开发者工具
```

---

## 文档

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md) — Tilo 的核心交互循环
- [`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md) — AI 原生 SaaS 组件体系
- [`docs/ROAM_INTERACTION_CONTRACT.md`](./docs/ROAM_INTERACTION_CONTRACT.md) — ROAM interaction contract
- [`docs/CONVERSATION_RUNTIME.md`](./docs/CONVERSATION_RUNTIME.md) — Conversation runtime
- [`docs/MEMORY.md`](./docs/MEMORY.md) — 记忆系统设计
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — Artifact 协议
- [`docs/SKILLS.md`](./docs/SKILLS.md) — Skill 系统
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API 契约
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md) — 构建你的第一个 Tilo app
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
