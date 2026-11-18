# 号脉（How Am I）× Reporter × Worker Workforce — V1 技术合同

Status: **Trusted Stage Reporter implemented and negative-path real E2E observed; successful Candidate→Verify→Delivery E2E and Live Heartbeat not yet accepted**  
Review date: 2026-11-17  
Protocol owner: uichat-mira/.github  
Target: Mira External Worker / paid Worker callers / Worker Workforce / Control Room

**Ownership boundary:** current External Worker lifecycle/role semantics are owned by [`external-worker-lifecycle.md`](external-worker-lifecycle.md). This document owns 号脉, Reporter, Workforce and Control Room integration contracts only; it must not redefine Candidate/Verify/Delivery/Recovery semantics.

> **维护者已确定的方向**：产品名「号脉」，英文名「How Am I」，技术代号 `how-am-i`。V1 **只接 Mira 的赛博施工队**，这是首家上报方而非永久唯一上报方；后续可支持为线上临时 Debug 授权的短期上报方，但**不属于 V1**。本期不做组织级通用应用日志，**不增加 Cloudflare 费用**。本合同不是施工授权，也不代表代码、Cloudflare 部署或真运行验收已完成。

## 0. 决策记录与边界

### 0.1 已确定（2026-11-17 评审结束）

1. 「号脉（How Am I）」是 **轻量运行观测服务**；Worker Workforce / External Worker Reporter 是**V1 第一家、唯一实际接入的上报方**，不是对未来来源的永久排他限制。「Mira Logs」退役为历史工作名称，不再是产品名。
2. 只接 Mira External Worker 的可信 Reporter。Cloud Auth、Mobile、Desktop 仓库**中的施工 Run**可以上报，三个产品自己的认证、客户端或服务端生产日志**不属于号脉 V1**。
3. **号脉观测基础设施新增费用为 0**：最多增加一个 Cloudflare Workers Free HTTP 接收 Worker，借助其自身 Workers Logs 实现短期事件查询；不增服务器、D1、R2、KV、DO、Queues、日志 SaaS 账单或自建数据库。**这不是禁止调用付费模型**：在现有权限和模型路由内，真实 Worker/Reporter 端到端验证可以使用付费 Provider，调用与费用按原施工体系单独记账。
4. 号脉只收脱敏的关键阶段、异常、运行状态和限量诊断事件，不收原始终端输出、完整 Agent trajectory、Prompt、模型回答、源码和每个 Token。
5. GitHub Issue/Actions/Artifact/PR 继续分别拥有任务、运行、Candidate 和交付事实；Workforce 管理调度，Control Room/血汗工厂 TV 做观察，均不能维护第二套任务与恢复真相。
6. 首批产品 caller 接入目标是 Cloud Auth、Mobile、Desktop；复用**同一个**组织共享 External Worker 引擎，不在各产品里重复造记者。
7. 在真正验证独立凭据隔离、持续事件来源和传输时延之前，不能把阶段性 Reporter 宣传成“模型逐工具实时直播”。
8. **未来扩展方向（明确非 V1）**：允许维护者为线上临时 Debug 授予有明确来源、期限、权限和自动失效条件的**临时上报方**。本期不实现临时上报方注册、凭据签发/撤销、跨应用事件协议、生产日志采集或相应 UI，也不为未来做提前通用化。

### 0.2 已核实的当前工程现实

- uichat-mira/.github main 当前共享工作流保留 worker_capture、verify、delivery、recovery_index 四个既有 Job，并从 PR #82 起增加**独立的 trusted_reporter Job**；具备隔离凭据和真实失败报道，尚未完成成功交付全链路 E2E；不等于 Live/heartbeat。
- AGT-056～059 已提供可恢复 Candidate、干净 Runner 验证、独立交付、跨 Run 恢复。恢复索引是 Issue 中 `mira-recovery-candidate:v1` 机器注释，原始证据仍须从 Actions Artifact/manifest/verify evidence 校验。
- AGT-059 的 caller 新权限要求 `actions: read`（历史 Artifact）与 `issues: write`（隔离 Recovery Index）。产品 caller 对历史 SHA 的 pin 尚需逐仓核查/升级，不能把 Org main 更新等于生产已经启用。
- Cloud Auth 默认分支为 dev；Desktop/Mobile 默认为 prod。`issue_comment` 实际入口读取默认分支工作流，dev 分支的修改不自动令评论派工生效。
- Control Room 现有系统是只读 GitHub/Cloudflare 投影，已有独立 Cloudflare Worker；V1 不把它改造成通用日志数据库或第二任务系统。
- [Worker v2 历史设计 PR #69](https://github.com/uichat-mira/.github/pull/69) 是设计草案，而不是 Reporter/Foreman 已实现的证明。

### 0.3 已实现的真实证据（2026-11-18；不改变本合同要求）

- [组织共享 Reporter PR #82](https://github.com/uichat-mira/.github/pull/82) 已合并，可信 `trusted_reporter` 在独立 Runner 上运行；只读当前 Run 的 GitHub Jobs/Artifacts/PR，以既有 `haomai.telemetry.v1` 白名单生成 HMAC 事件；Reporter 故障不阻断原有交付。7/7 Reporter 测试及原有 Candidate/Verify/Delivery/Recovery 回归均通过。
- 号脉 [PR #10](https://github.com/uichat-mira/how-am-i/pull/10) 已按 `dev → test → prod` 迁移并部署。Cloudflare 生产设置实查为 `observability.logs.enabled=true`、`invocation_logs=false`，避免平台自动请求日志采集自定义签名头；结构化日志仍可通过受控查询获取。
- [真实独立 GitHub Reporter Run #44209088849](https://github.com/uichat-mira/how-am-i/actions/runs/44209088849)：通过 `issue_number=999999` 故意触发未经授权 Issue 的入口校验失败；OpenCode 未启动，Verify/Delivery/Recovery 跳过；Reporter Job 仍成功，Cloudflare 受控 Query API 按真实 Run ID 查回 **`worker.failed` 和 `run.finished: failure` 两条事件**。这是实际失败报道链路，而非合成 Runner 的输出。
- [号脉 #11](https://github.com/uichat-mira/how-am-i/pull/11)、[Cloud Auth #155](https://github.com/uichat-mira/cloud-auth/pull/155)、[Mobile #325](https://github.com/uichat-mira/mira-mobile/pull/325)、[Desktop #480](https://github.com/uichat-mira/mira-desktop/pull/480) 均已将 `dev` 调用入口指向同一组织 Reporter 固定 SHA；四仓库的独立 Actions Secret 已配置，且无密钥进入源码或模型 Shell。各仓库 `test/prod` 的分支与默认分支派工行为不能据此推断为自动晋级。
- **待验收**：真实成功施工中的 Candidate 捕获、可信 Verify、Draft PR 与 Reporter 对应事件；明确的默认分支生产入口晋级；账号级 Cloudflare 账单与留存期实证；Live Reporter/heartbeats/TV。不得用本次故意失败的 Run 冒称这些能力已通过。

## 1. Cloudflare Free：本项目的预算与限制

### 1.1 2026-11-17 查到的规则

| 指标 | 2026-11-30 及以前 | 2026-12-01 起 |
| --- | --- | --- |
| Workers Free HTTP invocations | 100,000/day / account | 不变 |
| Workers Free CPU | 10ms/request | 不变 |
| Workers Logs 免费额度 | 200,000 events/day | **0.5GB/day** account-level observability ingestion |
| Workers Logs 保留 | 3 天 | **7 天** included |
| Free 额外付费摄入 | 不自动提供 | 不自动提供 |
| Logs 查询收费 | 无单独查询费 | 查询/仪表盘/告警不单独收费 |

来源（访问 2026-11-17）：
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- https://developers.cloudflare.com/observability/pricing/

**0.5GB 是 Cloudflare 账号共享额度，不是号脉专享**：同账号其他 Workers Logs、Traces、AI Gateway logs 等会分享额度。新增号脉 Worker 的 HTTP 请求也与同账号其他 Free Workers 分享 100,000/day 的额度。12 月 1 日后必须以当时 Dashboard 与官方政策复核实际口径。

### 1.2 容量估算与降级

估算例子：100 个施工 Run/天 × 20 条受控事件/Run × 每条 1 KiB ≈ **1.95 MiB/day 原始业务事件**；Cloudflare invocation logs、字段开销、其他账户使用均**不包含在估算里**。这是预算示例，不代表当前实测用量、完整摄入量或总账单。

施工进度和失败诊断属于**可降级的观察能力**，不影响 GitHub Worker 本身：
- 首先停掉诊断/debug，保留终态、失败与 Candidate/Verify/Delivery 的关键阶段；
- 其次减少心跳/中间过程事件，保留 GitHub 原始证据；
- 如果免费资源不可用，不“默默开通付费”也不改动 GitHub 执行语义，明确号脉不可用、回退 Actions/Artifacts 排障；
- 号脉不存长期事实；留存期后在 TV 上显示“现场日志已过期”，但仍可按 GitHub Run/PR/Artifact 继续追溯（Artifact 自身过期另行说明）。

### 1.3 关键能力门禁

Workers Logs 可以索引 Worker **自身**运行产生的结构化日志，支持 Query Builder 和 Workers Observability REST Query API。它**不是外部客户端可直接写入的通用数据库**；Worker 事件必须先经我们自己的 HTTP 接收 Worker，由它产生结构化日志。

Cloudflare API 文档目前对 `POST /accounts/{account_id}/workers/observability/telemetry/query` 标注权限 **Workers Observability Write**，不能当成低权限公开读接口。V1 先在 Cloudflare 控制台与受控 API 客户端验证 `run_id` 检索、延迟、权限、索引和免费计划可达性；达不到条件不能对 Control Room/TV 宣称已经拥有可用的自定义查询 API。

官方查询 API：https://developers.cloudflare.com/api/resources/workers/subresources/observability/subresources/telemetry/methods/query/

## 2. 体系架构与真相源

~~~text
GitHub Issue (task contract)
      |
 Enrollment --> Worker/Capture --> Verify --> Delivery --> Recovery index
                        |             |          |
                 immutable Candidate / verified evidence / Draft PR
      |                                        |
      +---------------- trusted GitHub facts --+
                                               |
                              separate Reporter job / bridge
                                (no model-readable secret)
                                               |
                                  HMAC bounded signed batch
                                               |
                                    号脉 / How Am I
                            ONE new Workers Free ingest Worker
                                               |
                                 structured Workers Logs
                                               |
                       Cloudflare controlled query (T4 gate)
                                               |
                    Control Room / Worker Workforce / TV
                    + existing GitHub read-only projection
~~~

| 层 | 负责什么 | 不能成为 |
| --- | --- | --- |
| GitHub Issue | 任务合同、修订、最终 outcome | 任意日志生成器 |
| GitHub Actions | 执行身份、job/run 终态 | 模型自述的替身 |
| Candidate/Verify/Delivery Artifacts & PR | 代码恢复、验证和交付证据 | Reporter 的口头叙述 |
| Reporter | 从可信 Job/evidence 形成阶段报道，从受限流形成 telemetry | 验收/合并/发布者 |
| 号脉 | V1 短期施工现场、异常诊断、短留存事件查询；未来可扩展受控临时 Debug 上报 | 永久证据库、V1 通用多应用日志平台 |
| Worker Workforce | Worker 能力/负荷/显式调度/续工选择 | 第二个 Issue/Run 台账 |
| Control Room / TV | 读模型、直播/回放展示 | 拥有工单/密钥/未经许可的远程执行 |

Reporter 的 “pipeline verified” 必须源自 trusted Verify 而非 OpenCode 文字。Logs 丢失不代表 Run 没执行，出现在 Logs 的 PASS 也不覆盖 GitHub Verify FAIL。

## 3. 号脉 V1 接入与事件合同

### 3.1 V1 接口只开放给受信任 Reporter

- `POST /v1/events`：HTTPS + JSON，**V1 只授权一个 Reporter 服务身份**（首期固定 `app_id = mira-worker-reporter`），不开放通用注册、租户/App 管理、客户端 SDK 或任何 Mobile/Desktop 直连写入。该 app_id 是首期来源标识，不能被实现成永久只允许这一来源的不可演进协议假设。
- `GET /health`：只返回基础服务存活/schema 版本，不泄漏内部来源、凭据或日志。
- V1 **没有**通用 `GET /events` / `SQL` / 公共搜索 API；按 Run 查询先通过 Cloudflare 原生后台与受控 API 实测，Control Room 的受控投影另做一张卡。
- `202 Accepted` 仅表示接收端完成校验并尝试写日志，不承诺“已持久化”“可按 Run 检索”或 exactly-once。不可用/校验失败须明确 4xx/5xx/429，不虚报成功。
- 单批最大 16 条事件/32KiB、单事件最大 2KiB（**建议的应用层上限，需实测 Free CPU**）；越界拒绝，不静默截断后称完整。

### 3.2 版本化 JSON（样例而非真实事件）

~~~json
{
  "schema": "haomai.telemetry.v1",
  "batch_id": "c647a4b7-8a66-4e88-a13e-c203188ba985",
  "events": [
    {
      "event_id": "5279291f-386a-4930-96e3-bd302e4161c1",
      "occurred_at": "2026-11-17T13:00:00Z",
      "kind": "candidate.captured",
      "level": "info",
      "repository": "uichat-mira/cloud-auth",
      "issue_number": 123,
      "run_id": "44000000000",
      "run_attempt": 1,
      "stage": "capture",
      "outcome": "captured",
      "evidence_ref": {
        "type": "actions-run",
        "id": "44000000000"
      }
    }
  ]
}
~~~

接收端附加 `received_at`、受信 `app_id`、`trust_class`；客户端不能自己声明 trusted。`run_id` 始终保存为字符串，所有 Run / Artifact URL 必须有同源性和字段白名单校验。事件为可重放的诊断通知，`event_id` 并不自动获得存储层 exactly-once 语义。

首期事件白名单：
- `pipeline.enrolled`、`worker.started`、`worker.stopped`、`worker.failed`；
- `candidate.captured`、`candidate.unavailable`；
- `verify.passed`、`verify.failed`、`delivery.draft_pr_created`、`delivery.failed`；
- `recovery.detected`、`recovery.failed`、`run.finished`。

任何 Tool 事件、heartbeat、provider retry 属于 Live Reporter **受控扩展**，不自动开启。禁收完整 stdout/stderr、trajectory、Prompt、推理或工具参数、变更代码、环境变量、HTTP auth/cookie 和包含用户数据的任意 metadata。仅允许固定 error_code + stage + 短脱敏摘要。

### 3.3 HMAC：V1 只有 Reporter 机器身份，不预建多 App 产品体系

头字段：
- `X-Haomai-App-Id` = `mira-worker-reporter`；
- `X-Haomai-Timestamp`；
- `X-Haomai-Nonce`；
- `X-Haomai-Signature`。

固定签名串：`v1 + LF + METHOD + LF + PATH + LF + TIMESTAMP + LF + NONCE + LF + SHA256(raw_body_hex)`。HMAC-SHA-256，hex 传输，恒定时间对比。签名用**原始请求字节**而不是重新序列化 JSON；允许时间窗建议 +/-90 秒，签名前先拒绝明显超大 payload。Secret 只在 Cloudflare Worker Secrets 与可信独立 Reporter Job secrets，不写仓库代码。

**必须写明限制**：没有 KV/DO/D1 的 V1 无法在全球边缘强制“一次使用 nonce”，因此仅具有限时窗口和身份完整性保护、并不强保证 anti-replay 或事件唯一性。event_id 可做读取端去重，不得用于财务、权限或交付侧写操作。

本期不用泛用 AppID 目录、多租户密钥发放、客户端 Token 交换、移动端 SDK、跨应用日志方案。轮换时允许受控双密钥短窗口和吊销旧密钥；仅可信维护者配置。未来临时上报方应采用独立短期授权与隔离、可到期/撤销、来源与事件范围约束、量级/脱敏限制；是否沿用同一 HMAC 或采用其他短期凭据，留给届时的独立技术合同与真实威胁模型裁决，**V1 不实现**。

## 4. Reporter：有事件，更要有独立权限边界

### 4.1 阶段 Reporter V1（必须）

- 新增**独立** Reporter GitHub Job，在不同可信 Runner 中读取受信 Actions Job/Artifact/Recovery Evidence，发布阶段事实。
- 使用模型施工 Shell 的 `worker_capture` **不得**读取号脉 AppSecret 或 GH Issue 写入令牌。不同 step/子进程不等于不同安全边界。
- 记者事件区分 `trusted_pipeline`（服务端事实）、`observed_tool`（不受信工具动态）、`derived_summary`（自然语言叙述）、`unavailable`（缺失/延迟）。
- Reporter 可在后续扩展一条单独的 human-readable Issue sticky comment，但不得修改 `mira-recovery-candidate:v1` 机器指针，亦不得写任务 outcome。V1 完成标准只要求号脉里查到**真实阶段事件**，不要求再增加 Issue 写入表面。
- Reporter 不可用必须清晰可诊断，但不阻断 Worker 的 Candidate/Verify/Delivery。若产品确实要强制观察成功才准派工，需要新的维护者裁决。

### 4.2 Live Reporter POC（不得伪称已接）

阶段 Reporter 不等于“正干什么的实时转播”。Live 必须证明**在 Worker Run 尚未结束时**，有至少两条可追溯的阶段内事件从**另一个安全边界**可读，且上报凭据没有暴露给 model shell。要证明去重、顺序、取消、停滞检测/不再有事件与 Worker 真实状态之间的区分。

禁止以以下手段充数：把长期或短期可写号脉凭证塞进模型进程；在同 Runner 后台运行带秘钥旁路；等 Run 完成后用轨迹文件假装实时。独立事件观察如果不可行，V1 诚实退化为 **GitHub Run 状态 + 可信阶段终态 + 号脉最近日志**，不增加数据库补洞。

## 5. Worker Workforce V1：劳动力而非新框架

Worker Workforce 是调度与可观察控制面，底层执行仍由 GitHub Actions + OpenCode + Candidate Pipeline 完成。

| 能力 | V1 接口/数据来源 |
| --- | --- |
| Registry | 有版本的受信 Worker profiles：worker_id、harness、repo allowlist、能力、模型 route_ref、权限边界。复用现有 Provider Registry，不复制第三套 Provider 配置 |
| Availability | 从真实 Actions Run/Job 与 caller 资格派生 `eligible/busy/unavailable/unknown`，不声称某个大模型实例“在线” |
| Dispatch | 只针对有授权的开放 Issue；V1 可以做资格检查、维护者显式 dispatch，不自动跨仓库批量派工 |
| Recovery | 使用 AGT-059 的 `fresh/recoverable/contract_drift/recovery_failed/delivery_retry_only/delivery_complete` 和原 Candidate Artifact，不能重建恢复数据库 |
| Capacity / cost | 排队数、真实 Run 时长、可用的 model usage；没有 usage/成本数据就标 unknown，不推定精确花费 |
| Escalation | **Planned under AGT-068:** 同卡两轮返工仍失败，第三轮起交由维护者亲自接手；当前 shared Worker 尚未实现自动 Return-to-Worker / 自动 escalation |

Foreman/Workforce 派工前必须核对 Issue 合同与授权、caller 是否在实际默认分支注册、当前活跃 Run、能力/模型 route 是否允许、密钥是否可用（只读可用性、不暴露值）、历史 Candidate/Verify 状态、返工升级和预算。任何 `recovery_failed`、冲突或未核实的权限必须 fail closed。

**不做**：自研 Agent Runtime、多 Agent debate、第二套任务数据库、复杂模型择优、自动合并、自动验收关卡、生产晋级、自动 release、触发未经授权的跨仓库施工。

## 6. Control Room / 血汗工厂 TV

Control Room 继续负责只读投影；其现有 Worker 可以另行增加**受控查询适配**，但不能把 Cloudflare Observability API 的高权限 token 给公开用户。V1 不接入 Cloud Auth/Mobile/Desktop 生产日志，不扩大现有 Public API 的匿名读取范围。公开 TV 如需展示具体路径、错误或代码活动，须有独立隐私/可见范围裁决；可先做维护者可见版本。

历史 Run：若号脉短保留日志已过期，仍显示 GitHub Run/Issue/PR 的事实与存档链接；Artifact 自身过期则提示无法恢复。不能靠 7 天日志冒充永久回放。

## 7. V1 验收及小卡边界

| 交付片段 | 最低真实证据 |
| --- | --- |
| A. 号脉 Free POC | 单 Worker HMAC 正/反例、字段/敏感信息拒绝、32KiB batch 上限、Cloudflare Free 账号真实可写入并按 run_id 查回事件；证明凭据权限和 CPU/免费请求/摄入成本 |
| B. Trusted Reporter | 独立 Job、Stage 可信 evidence 引用、至少一条真实 Run 的 Candidate/Verify/Delivery 事件可查，模型 Runner 确实无法读取 Reporter Secret；重复/缺失不产生假 PASS |
| C. Workforce Read Model | 真实仓库 caller Profile + Actions Run/Recovery 状态投影；活跃冲突、未授权派工与第三轮接管判定；无 usage 时标 unknown |
| D. 产品灰度接入 | Cloud Auth → Mobile → Desktop 分别按实际 pin 与 caller 权限升级，真实 Run 的事件链/证据链通过；默认分支工作流派工入口单独验收 |
| E. Live Reporter POC | Worker 仍运行时另一可信 Runner 可见事件，隔离凭据/延迟/乱序/runner loss 可说明；若失败，不把阶段报道冒充 Live |
| F. Control Room/TV | 仅受控读取 Run 事件，真实 GitHub 状态为准，日志过期与 Reporter 失联有明确状态，不泄漏高权日志查询 token |

T1/T2 合同测试：HMAC 原文绑定、错误密钥、重复事件、过期时间戳、恶意 JSON、超长字符串、签名比较、非法 event kind、隐私字段与注入；T3 Worker runtime 完成一次受限接收；T4 **必须在真实 Cloudflare 免费账号测试**查询、CPU、凭据、费额与可见范围。未有 T4，不能称号脉“已可查、可直播”。

限量诊断事件如 Run 启动/结束、Candidate/Verify/Delivery 等只在 POC 验证流中启用。**允许在 B/E 真实端到端验证中调用现有已授权的付费模型**，以证明实际施工路径、Reporter 事件源和时间顺序；但 A 的纯日志接收/验签/查询验证无需为形式消耗模型额度。付费 Run 要记录 Provider/model route、真实调用次数与可得 usage/费用，缺失项标 unknown；禁止无界重复调用。真实模型费用与 GitHub Actions 运行成本均与“号脉 Cloudflare 新增费用为 0”的基础设施预算分开核算。

## 8. 实施门禁 / 非目标

1. **号脉 Cloudflare 基础设施不接受付费前提**。若日志存储/查询等基础能力只有付费 Cloudflare 服务可达，报告阻塞，由维护者决定降级合同；不得自动采购、开户、开通付费 Cloudflare 产品。**已授权的付费模型调用不受此条禁止**，但不得因此无界增加模型调用或把新增基础设施费用混入模型预算。
2. **不接受伪查询**。号脉若只能在 Dashboard 看而无法安全用 API 按 Run 检索，必须区分“控制台可排障”与“TV 可编程查询”；不能偷偷引入数据库。
3. **不接受假直播**。模型 Runtime 无法证明安全实时观察时，保留阶段性 Reporter，不向施工进程下发秘密上报 Token。
4. **不接受任务真相漂移**。Workforce/TV 与 GitHub 状态冲突时显示来源并以 GitHub 为准；不能自动合并、关闭、晋级或发布。
5. **不接受大爆炸式上线**。A～F 逐一有证据后再推广。产品 caller 升级、GitHub permissions、额外日志读取权限、Cloudflare 生产部署都需要单独明确授权。
6. **不承诺永久存储**。号脉只用于短期排障与受控事件观察，失效/过期/限流不得造成 Worker 主线失败。
7. **合同本身非验收结果**。方向已经评审，技术 POC、真实安全边界、运行成本和 Cloudflare Query API 权限仍待证据确定。
8. **保留未来上报方入口，不扩大 V1 范围**。任何线上临时 Debug 上报方都必须另立协议与授权，包括明确生效/过期时间、可撤销凭据、隔离、数据分类、频率与成本预算；未授权时不得接收，更不得把临时上报提升为系统运行事实。

## 9. 上游参考

- Organization current instructions: https://github.com/uichat-mira/.github/blob/main/AGENTS.md
- Source-of-truth: https://github.com/uichat-mira/.github/blob/main/docs/governance/source-of-truth.md
- External Worker lifecycle (current): https://github.com/uichat-mira/.github/blob/main/docs/engineering/external-worker-lifecycle.md
- Worker v2 historical design background (superseded as current runtime description): https://github.com/uichat-mira/.github/pull/69
- AGT-056: https://github.com/uichat-mira/.github/issues/70
- AGT-057: https://github.com/uichat-mira/.github/issues/71
- AGT-058: https://github.com/uichat-mira/.github/issues/72
- AGT-059 + Recovery spec: https://github.com/uichat-mira/.github/issues/73 ; https://github.com/uichat-mira/.github/blob/main/docs/governance/external-worker-recovery.md
- Shared Worker runtime: https://github.com/uichat-mira/.github/blob/main/.github/workflows/mira-external-worker.yml
- Control Room current read model: https://github.com/uichat-mira/control-room/blob/prod/README.md

**一句话：** 号脉专为牛马号脉；Reporter 记录可信现场；Workforce 决定如何组织劳动力；GitHub 保存工程事实；Control Room 展示观察结果。零新增费用是上线门槛，不是降低证据或安全标准的借口。
