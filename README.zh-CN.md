# Tilo Framework

<p align="center">
  <strong>构建会记忆、会改进、能交付 AI 原生应用的 Agent 框架。</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./docs/USER_GUIDE.md">使用指南</a> ·
  <a href="./docs/V0_2_RELEASE_NOTES.md">v0.2 更新说明</a> ·
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

**Tilo 是一个开源框架，用于构建具备长期记忆、自我改进能力，并能交付类 SaaS 交互式结果页面的 AI Agent。**

很多 Agent 框架的重点是工具调用、工作流编排或多智能体协作。Tilo 更关注另一个问题：

> 如果一个 Agent 能长期理解用户和项目，能从历史任务中学习，能真正执行工作，并把最终结果交付成一个可交互的产品页面，而不是一段聊天文本，会发生什么？

Tilo 不是聊天机器人外壳，而是一个 **AI 原生 SaaS Agent 框架**。

```text
对话输入
  -> 创建任务
  -> 创建运行
  -> 召回记忆
  -> 选择技能
  -> 调用工具
  -> 生成 Artifact
  -> 人类确认
  -> 更新记忆
  -> 后续持续改进
```

---

## 为什么需要 Tilo？

传统 SaaS 的交互模式是：

```text
打开系统 -> 找功能 -> 填表单 -> 点按钮 -> 看结果 -> 再判断下一步
```

Tilo 想探索的是 AI 原生软件的模式：

```text
描述目标 -> Agent 执行 -> 生成结果页面 -> 人只确认关键决策
```

这并不是说未来没有界面，而是界面的角色变了：

- Chat 是指令入口。
- Agent Runtime 是执行层。
- Memory 是连续性和个性化层。
- Artifact 页面是最终结果交付层。
- Inbox 是人类决策层。

---

## 核心能力

### 1. 长期记忆

Tilo 把记忆作为一等公民，而不是简单保存聊天记录。

- 结构化记忆
- 记忆候选
- 用户确认后才进入长期记忆
- Workspace / Project 级别召回
- 记忆召回事件
- 记忆写入事件
- 为 embedding / rerank 预留扩展空间

### 2. Agent 自我改进

Tilo 内置安全的自我改进原语。

- Run Metrics
- Feedback Records
- Skill Candidates
- Skill 晋升前需要人类审核
- Eval 脚手架
- 默认不允许危险的自动自我修改

### 3. AI 原生结果交付

Agent 的输出不应该只是一段 Markdown，而应该是可用的产品结果。

- `artifact_spec.v1`
- Schema-driven 渲染
- 持久化 Artifact 页面
- Renderer Registry
- Artifact Actions
- 与 Confirmation 关联的动作
- Provenance 和 Memory References

### 4. 人类决策 Inbox

人不应该操作每一步流程，而应该确认关键决策。

- 持久化 Confirmation
- Approve / Reject / Edit 流程
- 高风险工具调用拦截
- 待处理决策队列

### 5. 可追踪 Runtime

每次运行都会产生安全、可见的执行轨迹。

- Task / Run 生命周期
- Trace Steps
- Trace 输出脱敏
- 失败运行处理
- Tool Invocation Ledger

### 6. 本地优先开发体验

Tilo 优先保证本地能跑起来。

- Docker Compose
- FastAPI 后端
- Next.js 前端
- PostgreSQL + pgvector
- Redis
- 本地 Eval runners

---

## 架构

```text
┌─────────────────────────────────────────────────────────┐
│                    Tilo Console                         │
│  Chat / Artifact / Memory / Trace / Skills / Inbox      │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                      API Layer                          │
│ Workspaces / Projects / Agents / Messages / Runs        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                    Agent Runtime                        │
│ RunManager / StateMachine / Planner / Executor          │
└──────────────┬─────────────┬───────────────┬────────────┘
               │             │               │
┌──────────────▼───┐ ┌───────▼───────┐ ┌────▼─────────────┐
│ Memory Engine    │ │ Skill System  │ │ Tool Registry    │
│ Recall / Events  │ │ Candidates    │ │ Permission Gate  │
└──────────────┬───┘ └───────┬───────┘ └────┬─────────────┘
               │             │              │
┌──────────────▼─────────────▼──────────────▼─────────────┐
│                  Artifact + Inbox Layer                  │
│ ArtifactSpec v1 / Renderer Registry / Confirmations      │
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

当前 UI 是一个单页 AI 原生控制台。

1. 打开 `http://localhost:3000`。
2. 选择一个 Demo Prompt，或者输入自己的任务。
3. 点击 **Send Message**。
4. Tilo 会创建 Task 和 Run。
5. 中间区域会渲染生成的 Artifact。
6. 右侧区域可以查看 Trace、Memory、Skills、Files 和 Inbox。
7. 在 **Memory** 中确认有价值的记忆候选。
8. 在 **Inbox** 中审批待确认动作。
9. 再次运行任务时，已确认记忆可以被召回。

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

Tilo 会生成一个合同审查 Artifact，包含风险项、修改建议和需要确认的动作。

### 销售跟进 Agent

```text
Which customers should sales follow up with this week?
```

Tilo 会生成 Dashboard 类型 Artifact，并为推荐动作创建确认项。

### 竞品分析 Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo 会生成结构化对比 Artifact，而不是只返回一段文本。

---

## 当前状态

Tilo 目前处在早期 v0.2 阶段。

| 模块 | 状态 |
|---|---|
| Runtime loop | 已有基础闭环 |
| Memory candidates | 已有基础能力 |
| Recall / write events | 已有基础能力 |
| Artifact spec v1 | 已有基础能力 |
| Renderer registry | 已有基础能力 |
| Human confirmation | 已有基础能力 |
| Tool permission gate | 已有基础能力 |
| Self-improvement primitives | 早期基础能力 |
| Evals | 本地脚手架 |
| UI polish | 需要大幅优化 |

当前 UI 能跑通功能，但视觉和引导还比较早期。见 [`docs/UI_IMPROVEMENT_PLAN.md`](./docs/UI_IMPROVEMENT_PLAN.md)。

---

## Roadmap

### v0.2

- 强化 Memory Governance
- 改进 Artifact 结果页
- Skill Candidate Review Flow
- Run Metrics 和 Feedback Loop
- Tool Invocation Ledger
- 本地 Eval Baseline
- UI onboarding 和视觉优化

### v0.3

- Hybrid semantic memory recall
- Artifact version history 和 patching
- 更完善的 Skill Package
- MCP tool integration
- 文件驱动的合同审查
- 更真实的垂直场景 Demo

### v0.4+

- Telegram / Slack / Discord / 微信风格适配器
- Browser / GUI automation
- Artifact 分享与发布
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
docs/          产品原则、架构、v0.2 计划、使用指南、实现规则
evals/         Memory、Artifact、Runtime loop 本地评测脚手架
```

---

## 文档

- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md) — 项目宪法
- [`docs/PRODUCT_PRINCIPLES.md`](./docs/PRODUCT_PRINCIPLES.md) — 产品原则
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — 系统架构
- [`docs/MEMORY.md`](./docs/MEMORY.md) — 记忆系统设计
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — Artifact 协议
- [`docs/SKILLS.md`](./docs/SKILLS.md) — Skill 系统
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API 契约
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md) — 使用指南
- [`docs/UI_IMPROVEMENT_PLAN.md`](./docs/UI_IMPROVEMENT_PLAN.md) — UI 改进计划

---

## 贡献

Tilo 还很早期，欢迎参与贡献。

贡献前请阅读：

- [`AGENTS.md`](./AGENTS.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)
- [`docs/QUALITY_BAR.md`](./docs/QUALITY_BAR.md)

最重要的一条：

> 不要把 Tilo 做成简单聊天机器人。请始终保留：记忆 + 执行 + Artifact + 确认 + 改进闭环。

---

## License

Apache License 2.0
