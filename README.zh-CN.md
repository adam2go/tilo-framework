# Tilo Framework

<p align="center">
  <strong>围绕 ROAM Loop 构建 AI 原生 SaaS Agent：渲染、观察、行动、记忆。</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./docs/ROAM_LOOP.md">ROAM Loop</a> ·
  <a href="./docs/CONVERSATION_RUNTIME.md">Conversation Runtime</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/BUILD_YOUR_FIRST_TILO_APP.md">构建 App</a> ·
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

很多 Agent 框架关注推理、工具调用、工作流编排或多智能体协作。Tilo 更关注缺失的产品层：

> 如果用户界面本身也成为 Agent Runtime 的一部分，会发生什么？

Tilo 不是聊天机器人外壳，而是一个 **AI 原生 SaaS 交互 Runtime**。

---

## 快速开始

运行本地 Demo：

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

打开类 Telegram 的 ROAM demo：

```text
http://localhost:3000/demo/telegram
```

检查后端健康状态：

```bash
curl http://localhost:8000/api/health
```

Demo 默认支持确定性本地模式。你也可以在 `.env` 中配置 OpenAI-compatible provider 启用后端 LLM 模式；API key 只保存在后端，不会暴露到前端。

---

## 可以构建什么？

Tilo 适合这样的 agent app：对话是入口，但当用户决策需要结构化表达时，UI 会自然出现。

| 示例 | Tilo 会渲染什么 |
|---|---|
| **合同审查 Agent** | 风险面板、修改建议、审批卡片、完整审查 Artifact、记忆候选 |
| **销售跟进 Agent** | 跟进建议、决策卡片、草稿动作、可复用语气偏好 |
| **竞品分析 Agent** | 对比矩阵、证据卡片、方案选择、后续动作 |

示例 prompt：

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

```text
Which customers should sales follow up with this week?
```

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

---

## 工作原理

```text
Render -> Observe -> Act -> Memorize
渲染 -> 观察 -> 行动 -> 记忆
```

- **Render**：Agent 渲染交互式 Artifact 或组件界面。
- **Observe**：用户点击、编辑、审批、选择、反馈和工具结果成为结构化观察。
- **Act**：Agent 更新 Artifact、调用工具、追问问题、创建确认项或启动后续任务。
- **Memorize**：被确认的决策、偏好、项目事实和可复用流程进入长期记忆。

核心运行时链路：

```text
Agent App Manifest -> Interaction Policy -> Mini / Rich Surface
-> UIInteractionEvent -> ConversationTurn(observation)
-> AgentContextBuilder -> PromptBuilder -> Agent Runtime
-> Memory Candidate -> Human Confirmation -> Confirmed Memory
```

---

## 构建一个 Agent App

一个 Tilo app 是一个很小的声明式目录：

```text
app.yaml
interaction.policy.yaml
fixtures or sample inputs
optional README
```

可以从这里开始：

```text
examples/apps/contract-review-agent/
examples/apps/sales-followup-agent/
```

创建新 app：

```bash
python scripts/create_app.py my-agent
```

然后编辑 `app.yaml` 和 `interaction.policy.yaml`。Policy 决定 Agent 何时静默继续、何时追问、何时展示 mini surface、何时打开 rich surface。

开发者参考：

- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`docs/APP_MANIFEST.md`](./docs/APP_MANIFEST.md)
- [`docs/INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)
- [`examples/apps/README.md`](./examples/apps/README.md)

---

## 当前能力

- Conversation sessions 和 turns
- Web demo 通过 `session_id` 恢复会话
- Telegram 文本 / callback 映射基础
- 后端 interaction policy evaluation
- Mini surfaces 和 rich surface links
- `artifact_spec.v1` Artifact 渲染基础
- Memory candidates 和确认后持久化
- ORID-inspired context reflection plan
- 声明式 example apps 和 scaffold script

---

## Roadmap

| Milestone | Focus |
|---|---|
| v0.5 | 持久 conversation runtime、rich surface escalation、Telegram mapping、第二个 app |
| v0.6 | ConversationService、typed runtime primitives、centralized observation linkage、developer DX |
| v0.7 | Run-to-session closure、conversation-native message endpoint、ORID reflection、explainable memory candidates |
| Future | MCP、browser/GUI automation、更多渠道适配、权限、skill marketplace primitives |

---

## 仓库结构

```text
backend/       FastAPI 后端、Runtime services、Memory、Tools、Artifacts
frontend/      Next.js Console、Artifact Renderer、Memory/Trace/Inbox 面板
docs/          产品原则、ROAM Loop、架构、指南、实现计划
evals/         本地评测脚手架
examples/      声明式 agent app examples 和 fixtures
scripts/       开发者工具
```

---

## 文档

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md)
- [`docs/CONVERSATION_RUNTIME.md`](./docs/CONVERSATION_RUNTIME.md)
- [`docs/MEMORY.md`](./docs/MEMORY.md)
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md)
- [`docs/SKILLS.md`](./docs/SKILLS.md)
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md)
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md)

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
