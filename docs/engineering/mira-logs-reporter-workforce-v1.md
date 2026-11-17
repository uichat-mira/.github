# Mira Logs × Reporter × Worker Workforce — V1 技术合同

Status: **Proposed / design-only / awaiting maintainer review**  
Date: 2026-11-17  
Owner: uichat-mira/.github (Organization-level protocol)  
Scope: Mira External Worker v2, one Cloudflare Free Worker for Mira Logs, Reporter, Workforce, existing Control Room projection

> 目标不是再造一个 Agent 框架，而是让 Mira 的施工任务有可信现场、有可恢复的成果、有可解释的调度权。此文是后续实施卡的上游设计约束，不代表代码、部署、账号权限或验收已完成。

## 0. 已有事实、既定约束与待验证事项

### 0.1 经仓库核实的事实（2026-11-17）

- uichat-mira/.github main 的共享 mira-external-worker.yml 已包含 worker_capture、verify、delivery、recovery_index 四个独立 Job；**没有** Reporter Job 或 Live Reporter Bridge。
- AGT-056 至 AGT-059 已交付 Candidate Contract、失败保全、干净 Runner Verify/Delivery 与同 Issue 跨 Run Recovery。AGT-059 的可运行结果不能代替产品调用方接入证明。
- 当前 Recovery 以 **Issue 上 github-actions[bot] 的 mira-recovery-candidate:v1 marker** 作索引，以 Actions Artifact、manifest、digest、exact base SHA、contract fingerprint、Verify/Delivery evidence 证明真相；不能另建 Recovery ledger。
- 原有 Desktop、Mobile、Relay、Cloud Auth 等付费 caller 在核对时仍 pin 历史 engine SHA 1380017dbedd147fdfec4c5b2404443e12967182。Cloud Auth 默认分支为 dev；Desktop 和 Mobile 默认分支为 prod（Issue Comment 调度依赖默认分支）。
- Control Room 当前是只读的 GitHub / Cloudflare / Runtime 投影，已有独立 Cloudflare Worker；不是调度数据库或敏感原始日志公开查询 API。
- Draft PR #69 的 Worker v2 架构研究包含 Reporter / Foreman 提议，尚未合并。该研究的 Reporter 与 Foreman 目标不能写成运行现实。

### 0.2 已有维护者约束（本合同必须遵守）

- Mira Logs **月新增成本 0**；只新增 **一个** Cloudflare Workers Free 接收 Worker；不买服务器，不增 D1、R2、KV、Queues、Durable Objects、独立数据库或常驻容器。
- Logs 只收脱敏错误、异常、关键生命周期事件及低频状态摘要；**不采集**全量 stdout、Prompt、Token 流、源码、终端原始输出或无限逐工具调用流。
- 可信服务端使用 AppID + AppSecret / HMAC；长期密钥仅在服务端及可信执行边界，不写浏览器、Mobile 安装包、Desktop Renderer 或模型可读的 Worker shell。
- GitHub Issue 继续是任务合同/outcome 唯一真相源；GitHub Actions、Artifacts 和 PR 是执行/交付证据；Workforce 与 Reporter 均不能私自合并、验收、关闭、晋级或发布。
- Control Room 保持只读投影；“血汗工厂 TV”消费可验证事件，不代替原始证据。
- 三个产品（Cloud Auth / Mobile / Desktop）是核心落地目标，但旧 caller pin 升级、权限授予和生产调度烟测属于独立实施/推广决策。

### 0.3 Cloudflare 官方能力与变更窗口

- Workers Free 当前每账户每天 100,000 次请求；HTTP Request CPU 10 ms 限额。所有同账户 Workers 共享额度，不应假设 Mira Logs 独占配额。
- Workers Logs 记录 Worker 自身的 invocation/custom console logs，支持 JSON 字段索引、Query Builder 和 Workers Observability REST Query API；**不能直接视为任意外部客户端可写的日志数据库**。外部事件应先到自建接收 Worker，再由 Worker 生成经过校验的结构化 console event。
- 截至 2026-11-17，Workers Free Logs 为 200,000 条/日、保留 3 天。2026-12-01 起将切换共享 Observability Free 规则：每日 0.5 GB 摄入、含 7 天保留；超量 Free 不提供自动收费的额外摄入。该时点须以届时控制台/官方文档再次核验；不能把旧计数额度延用到新计费周期。
- Workers Observability Query API 是真实 API，但当前 Cloudflare API 文档对 POST /accounts/{account_id}/workers/observability/telemetry/query 标注的 token permission 为 **Workers Observability Write**。不能凭端点名推断只要 Read，也不能把该 token 暴露给公开 API。
- 这些是文档事实，不是已在 Mira Cloudflare Free 账号上跑通的 T4 证据。Free 账号对 API、索引字段、查询延迟、日志完整性、配额的具体表现必须先实测。

官方参考：
- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- https://developers.cloudflare.com/workers/observability/query-builder/
- https://developers.cloudflare.com/api/resources/workers/subresources/observability/subresources/telemetry/methods/query/
- https://developers.cloudflare.com/observability/pricing/

## 1. 系统职责与唯一真相源

| 层 | 责任 | 权威/非权威 |
| --- | --- | --- |
| GitHub Issue | 任务合同、维护者修订、任务结果 | 权威 |
| Actions Run / Job | 执行身份、步骤与 Job 终态 | 权威 |
| Candidate + Verify/Delivery Artifacts | 可恢复代码、验证/交付证据与 exact identity | 权威 |
| Repository workflow / Provider registry | 能力、验证命令、模型路由配置 | 权威 |
| Mira Logs | 短期诊断、脱敏事件、近实时投影数据 | **非权威**，可延迟、采样或丢失 |
| Reporter | 采集、分类、发布“可信事实”与“未受信 telemetry” | 投影，无 outcome 权 |
| Workforce | Worker profile、可调度性、建议/授权后的调度、成本观察 | 不创建第二套 Issue/Run/PR 台账 |
| Control Room / TV | 只读、默认私有的现场展示；受许可的公开摘要另行裁决 | 投影，无执行授权 |

原则：**事件不是事实的替代品。** 若 Logs 显示 PASS 而 Verify Job / Artifact 为 FAIL，必须展示冲突并以 Verify 为准。Logs 消失不代表 Run 未执行；Run 结束不等于 Issue 验收完成。

## 2. 首期部署拓扑

~~~text
GitHub Issue (task contract)
       |
   caller / Enrollment
       |
 trusted Actions pipeline --> immutable Candidate / Verify / Delivery evidence
       |                               |
       | terminal trusted stage facts  | GitHub API
       v                               v
   separate Reporter Job        Worker Workforce reader
       |                              |
       | signed bounded batch         | GitHub source-of-truth projection
       v                              v
Mira Logs Ingest Worker         Control Room / Workforce / TV
(ONLY new Cloudflare Worker)          ^
       |                              |
  structured console.log              | bounded query / projection
       v                              |
Cloudflare Workers Logs -- controlled query adapter (future integration gate)
~~~

- Mira Logs 服务仅做 POST 接入与校验。V1 不增加自建 SQL/存储、登录系统、公开查询接口、后台 Worker、动态 Worker 注册数据库。
- Control Room 已有的 Worker 可以在后续扩展 **受权的只读查询投影**；这不是第二个新增 Worker。不能在未验证凭据、权限和访问控制前接通原始日志到公开 API。
- 不能将 Worker stdout 中的原始工具事件误认为来自可信 Reporter Job。Live Reporter 受独立技术门禁约束（见第 5 节）。

## 3. Mira Logs V1 — 写入协议

### 3.1 API

- POST /v1/events：唯一 V1 写入口，HTTPS，Content-Type application/json；返回 202 只表示 **请求通过检查并调用了日志输出**，不表示持久化、可查询或 exactly-once。
- GET /health：仅返回匿名存活与 schema version，不返回 App 清单、配额、签名材料、上报量、IP 或事件内容。
- V1 **不开放** GET /v1/events 或通用 SQL/search 接口；Cloudflare 查询由受控适配层/控制台承担，需先通过 T4。
- 非法/过期签名、非白名单 app_id、非法 schema：4xx；体积超限：413；限额：429；依赖不可用明确报错，不能静默返回“已持久化”。

### 3.2 V1 数据结构（示例，不是真实事件）

~~~json
{
  "schema": "mira.telemetry.v1",
  "batch_id": "17cbed36-d858-4603-8b47-4bf3d0661b84",
  "events": [{
    "event_id": "7eebd096-b8f8-407a-b401-2e799561a5aa",
    "occurred_at": "2026-11-17T08:00:00Z",
    "source": "github-worker",
    "kind": "pipeline.candidate.captured",
    "level": "info",
    "repository": "uichat-mira/example",
    "issue_number": 123,
    "run_id": "44000000000",
    "run_attempt": 1,
    "stage": "capture",
    "outcome": "captured",
    "evidence_ref": {
      "type": "actions-run",
      "id": "44000000000"
    }
  }]
}
~~~

实现由可信接收端填充 received_at、resolved app_id、trust_class、schema 和校验结果；客户端不得自行宣称 trust_class=trusted。run_id 作为 **字符串** 保留原值，禁止把 GitHub Run / Attempt、Issue 状态、Provider 自述混成一个生命周期字段。

最低维度：schema、event_id、occurred_at、received_at、app_id、source、kind、level、repository、issue_number、run_id、run_attempt、stage、outcome、trust_class、evidence_ref。非 GitHub 服务允许省略 GitHub 专属字段，但必须携带自己的可追溯 correlation_id。

事件白名单（首期）：pipeline.enrolled、worker.started、worker.stopped、worker.failed、candidate.captured、candidate.unavailable、verify.passed、verify.failed、delivery.draft_pr_created、delivery.failed、recovery.detected、recovery.failed、run.finished、service.error。工具生命周期/heartbeat 属 Reporter Live POC 扩展，不默认收高频输出。

写入数据必须**字段白名单**，拒绝任意 metadata、trace dump、HTTP headers、Prompt/Message、Token、API Key、Cookie、原始 URL query、完整文件/源码、用户内容。错误仅含固定 error_code、stage 与安全短摘要；路径/文件名需要泄漏风险评审，首期不发完整路径。

### 3.3 体积/频率预算（设计目标，非平台承诺）

- 单请求不超过 32 KiB；每批不超过 16 事件；单事件序列化不超过 2 KiB。所有超限明确拒绝而非截断后冒称完整。
- 优先将同一阶段的事件批量上报，默认每 Run 只发阶段边界及错误；不按 token、stdout 行或每条 git diff 发日志。
- 原型验收阶段 head_sampling_rate = 1 以证明事件可查询，确认成本与量级后再调整。抽样导致的缺口必须在消费端说明；不能将未查询到事件当作没有失败。
- 目标每批处理占用 Free 10ms CPU 预算内，必须以真实 Worker/Free 账号测得的 CPU、日志量与错误比率证实。超量优先停收非关键日志，不改变 GitHub 执行/交付事实。

## 4. Mira Logs V1 — 认证、安全与反滥用

### 4.1 服务端 HMAC

- 每个可信 App 独立 app_id / app_secret。app_id 注册表存版本化配置，secret 存 Cloudflare Worker Secrets / 可信 GitHub Actions secret；不得提交源码。
- 推荐头：X-Mira-App-Id、X-Mira-Timestamp、X-Mira-Nonce、X-Mira-Signature。
- 固定 UTF-8 签名串：version + LF + uppercase HTTP method + LF + path + LF + timestamp + LF + nonce + LF + lowercase hex SHA-256(raw body)。签名算法 HMAC-SHA-256，hex 编码；先验证体积/字段长度，再对**原始 body bytes**验签，不重新 JSON 序列化。
- 接收端按 app_id 查唯一有效密钥；验证 +/- 90 秒时间窗、固定版本、长度、签名 constant-time compare；不同 app_id 严禁混用密钥/授权 scope。
- 静态 HMAC 在无 KV/D1/DO 的条件下**不能强保证 nonce 的全局一次性消费**。因此 V1 只保证短时窗抗过期重放、不保证 exactly-once。event_id + batch_id 支持消费端去重，重复上报不能成为重复 Task/Run 事实。
- 密钥轮换允许 app_id 下短期双密钥窗口并显式失效旧密钥；不得实现未登记来源的自助注册。

### 4.2 Worker Shell 与 Reporter 的硬隔离

- 拥有 OpenCode/shell 的 worker_capture 只能持它原本授权的 Provider 凭据与最小 GitHub 权限；**不能**持 AppSecret、Cloudflare 读/写令牌、Issue 发布凭据或可用于签名的永久凭据。
- 可信 Reporter 放在**不同 GitHub Runner/Job 或独立受控服务**；它从 Actions API、可信 Job outputs/Artifacts 读取证据，再用独立 AppSecret 上报。
- 在同一 Runner 上把凭据放在另一进程、环境变量、晚执行的 step，**不视为安全隔离**。绝不为“实时感”向模型 shell 注入 AppSecret 或具有等价权限的短期日志写 Token。
- Browser/Mobile/Desktop renderer 禁止直接拥有 AppSecret。未来设备端如确需写入，先由可信服务颁发受限短效 token，另行评审身份、撤销、滥用预算；V1 不做。
- 签名证明“某受信上报通道发过此 payload”，不证明 payload 中 worker narrative 真实；真实 stage facts 必须在 Reporter 内重新绑定 GitHub server-side state/evidence。

### 4.3 资源滥用与泄漏

- Cloudflare 请求流量/CPU、接收批次、事件数、超限与错误数必须有预算和观测；限制来源并非认证，Origin/IP/UA 不能替代签名。
- 每个 app_id 设计上报配额与固定允许 kind；配额若依赖全局持久计数/强去重，Free 无存储架构无法保证，必须把限制描述为**最优努力的速率/体积上限**并通过 Cloudflare 可用能力实测。
- 返回正文不能包含签名、请求原文、token、内部密钥名、错误堆栈或 Cloudflare 账号数据。
- Worker 代码和日志两处都要保持敏感字段负面测试；任何凭据出现在日志即验收失败。

## 5. Reporter V1 — 可信阶段报道，Live 独立门禁

### 5.1 首期 Reporter 的实际能力

V1 增加独立 Reporter Job（不是 worker_capture 内改名的 step），从 GitHub server-side Run/Job state、Candidate/Verify/Delivery Artifact 和已有 Recovery marker 形成阶段事实：

- enrolled / worker terminal / candidate captured or unavailable；
- verify pass/fail/skip；
- delivery pass/fail / exact Draft PR；
- recoverable / contract_drift / recovery_failed / delivery_retry_only / delivery_complete；
- run finalized / evidence unavailable。

每条含 run_id、run_attempt、occurred_at、原始证据链接与 origin。Reporter 可以按事件去重重发，失败不得阻断 Worker Delivery，也不得把 reporter failure 隐藏成 Worker PASS。

**Important:** 由于 GitHub Jobs 是异步独立执行，V1 按阶段完成/独立读取的事实发表；不能将它包装成“模型每一步都能直播”。

### 5.2 Trusted facts / Untrusted telemetry / Narrative

| trust_class | 来源 | 允许显示为 |
| --- | --- | --- |
| trusted_pipeline | Actions API + 匹配的可信 Artifact/manifest | 可信阶段事实 |
| observed_tool | 非可信 Worker stream/stdout/Agent 报告 | 未经独立核验的现场动态 |
| derived_summary | 受控模板或模型润色 | 可读摘要，不能提升事实可信级别 |
| unavailable | 缺失/延迟/冲突/来源不可达 | 明确未知，不假装 idle 或 success |

Reporter 可维护一条人类可读的 Issue 状态评论，但必须与 mira-recovery-candidate:v1 **机器指针**分离；不能修改/伪造 Recovery marker；评论含 deterministic marker、run identity，复用相同评论而不是每个 event 新发一条。其 Issue 评论写权限仅在独立可信 Reporter Job 使用，不给 Worker。

### 5.3 Live Reporter POC（不能跳过）

近实时观察模型工具活动需要证明**独立可信观察通道**确实能在 Worker 运行期间读取增量事件，并且不把发布凭据交给 model shell。

可研究 GitHub Actions 正在运行时的日志可读性、独立 Reporter Bridge、受限单向遥测，但以下都**不能直接宣称已经成立**：

- 在同一个模型 Runner 开第二进程并拿长期 AppSecret；
- 向 model shell 传短期可写日志 Token 后声称模型无上报权限；
- 在 Actions Run 结束后读取 trajectory.jsonl 再冒充实时直播；
- 没有证据来源的“施工中”状态或虚构的具体 tool 调用。

Live POC 最低证据：真实运行中产生两条按时间排序的事件；另一安全边界在 Run 尚未结束时读到；密钥未出现在 model runtime/env/workspace/log；断线、重复、乱序、取消、Run 消失时状态可解释。若失败，V1 保留可信阶段报道 + Actions 运行中状态投影，**不承诺工具级直播**。

## 6. Worker Workforce V1 — 劳动力控制平面

### 6.1 职责，不做重复数据库

Workforce 的职责是“有哪些可用执行能力、何时有资格派给哪个 Issue、当前由哪个 Run 执行、出错后怎么接续、应否让维护者接管”；不是重建 GitHub Project，也不是自研 Agent Runtime。

| 能力 | V1 语义与真相源 |
| --- | --- |
| Worker Profile | 由受信 Organization/repository workflow 配置声明逻辑 worker_id、执行 harness、模型策略、适用仓库、权限能力；Provider endpoint/model route 继续复用既有 registry，不能复制一份 |
| Availability | 根据实际 Actions 排队/运行、授权和配额事实推断 eligible/busy/unavailable/unknown；Actions 没有永久在线“空闲工人”，禁止虚构在线状态 |
| Assignment | 输入仅为明确授权开放 Issue；由 caller dispatch 产生 server-side Run ID。V1 先提供建议/受权显式触发，不自动扩大权限 |
| Recovery | 直接复用 AGT-059 机器 state / Candidate identity；不复制 Artifact 到 Workforce DB |
| Capacity & cost | 当前/队列并发、Run 时长、模型实际 usage（若可用）、失败/重试；缺失时标 unknown，不猜 tokens 或真实金额 |
| Escalation | 同一卡两轮返工仍不解决，第三轮起标明维护者接管，不无限给同一 Worker 重派 |

Worker Profile 是**逻辑执行配置**，不是常驻机器人账户。不同厂商/模型可复用同一执行 harness，但保留 route、secret、能力和风险边界。组织共享 Workflow 的修改不自动 repin 各产品调用方。

### 6.2 调度前置条件

Foreman/Workforce 必须在调度前验证：

1. Issue 开放、有效合同、实际执行授权、仓库范围与维护者评论修订；
2. 对应仓库 worker caller 真实存在、默认分支/入口真实可触发；
3. 当前该 Issue 无其他冲突中的活跃 Run，遵循现有串行与并发规则；
4. Profile/Model route 在可用白名单内，provider key 可用性由可信边界判断（不把密钥值暴露出来）；
5. 同 Issue Recovery 机器状态允许继续；recovery_failed / contract_drift 不能被调度层静默重试成 fresh；
6. 依赖和返回次数没有触发显式 blocker/人工接管；
7. 预算守卫：工作负荷/预期费用可能超限时拒绝或提示，而不是静默换模型、增加成本。

调度层禁止单凭 Reporter “通过”就合并、关闭 Issue、晋级或部署。自动派卡、跨 Issue 依赖调度、免费/付费择优、费用硬限额属于后续明确授权的独立合同；V1 不让其假装上线。

### 6.3 Worker Run 映射与 UI 语义

展示最低字段：repository、Issue URL、worker_id/profile_ref、actions_run_url、run_attempt、origin_candidate_run、candidate_digest/tree、verification outcome、delivery Draft PR、recovery mode、last observed event_at、数据来源/时效。

“空闲”仅表示当前没有运行占用的配置容量，不表示模型在线；“失败”区分 runner/provider/verification/delivery/recovery，不以总体 Actions 红绿替代；“最近事件”是诊断观察，不能替代 GitHub 真实状态。

## 7. Control Room 与血汗工厂 TV

- 复用 Control Room 现有读模型展示 GitHub Actions/Issue/Candidate，V1 不扩展公开 API 返回原始工具输出或账号细节。
- Workers Observability API 查询只由具有专用受限凭据的服务端发出，强制服务名、app_id、repo、run_id、时间范围、limit/分页的白名单过滤与输出脱敏；**当前 API 文档所需 Observability Write 权限是实施门禁，不能当只读保证**。
- 需要私有 Run 细节的 TV 初期仅授权查看；若要公开展示，则另行制定内容审批/数据脱敏与显式公开范围，不能直接打开现有 CORS:* Public API。
- 短期 Logs 超出保留期后，TV 只展示 GitHub 可核验的历史里程碑与 Artifact 链接，明确“详细事件已过期”。绝不能把日志缓存当成永久任务台账。
- 暂不提供自动打断、鞭子按钮、远程执行或修改任务权限；这些属于未来有独立授权的 Control Plane 能力。

## 8. 契约测试与验收证据

### 8.1 Logs POC（第一张最小实施卡的建议验收）

T1/T2：HMAC 正常与错误签名、时间漂移、App 混用、body 变更、无凭据、字段溢出/非法 schema、敏感字段拒绝、batch/event 体积、重复 event_id、无存储重放限制说明、响应语义。  
T3：在实际 Worker Runtime 用 WebCrypto 验签并发出 JSON console event；证明失败路径不记录请求密钥。  
T4（必须真实 Cloudflare Free 账号）：发送一条合法事件与一条非法事件，**真实 Workers Logs 索引/Query API 能以 app_id + run_id 检出合法事件、不能查到敏感内容**，记录查询实际权限、延迟、CPU、请求计数、保留期及 12-01 计费适配。未通过 T4 不能宣称已达到 Logs 的可检索目标。

### 8.2 Reporter

- 一个受控真实 Run 产生可信阶段事件，验证 Run/Artifact/Issue 引用一致；日志不包含原始 prompt/secret。
- Worker Shell 中不能读取 Reporter credential；需要独立 Job/Runner 作为安全证据，而不只是环境变量约定。
- 失败/跳过/重复/乱序/expired artifact 均不被渲染为 PASS；独立 Reporter 失败不得影响真实交付。
- Live Reporter 的“在 Run 未结束前读到事件”属于单独 T4 POC，未实测不能写已接通。

### 8.3 Workforce

- 用真实开放 Issue + 真实 caller 检查 eligible/ineligible、重复调度拒绝、busy/unknown、Candidate 续工与 Delivery-only Retry 状态；
- 第三次返工应升级维护者而不是无界自动重派；
- 无计费/模型 usage 数据时诚实 unknown；
- 未经授权，不会发生 dispatch、Issue outcome、merge、release 或环境晋级。

### 8.4 产品推广与冻结边界

- 先完成 Logs POC → 可信 Reporter 阶段事件 → 一个已核实 caller 真实 Run；再对 Cloud Auth、Mobile、Desktop 分别 repin、授予精确 caller permission 上限并分仓验收。
- 现有 AGT-059 所需权限是 actions:read（恢复拉取）与 issues:write（隔离 Recovery Index 写 pointer）；Reporter 额外的 issues:write 只能存在于自身可信 Job。调用方的顶层权限只定义上限，各 Job 自身必须保持最小权限。
- Cloud Auth 默认分支 dev；Desktop/Mobile 默认 prod。issue_comment 路线不能只在 dev 改 YAML 就宣布已启用。晋级/生产调度烟测需独立授权。
- Free Wrapper 仍由历史 immutable SHA 保护，付费 caller 的更新不等于免费 Worker 已迁移。

## 9. 实施切片（不是现在自动创建的 Issues）

A. Logs receive/query POC：单 Worker + HMAC + structured log + 免费账号真查询 + 失败边界。  
B. Reporter 阶段性接线：独立 Job、真实 stage source、签名批量上报、无模型读取凭据。  
C. Workforce V1 read model：Worker profiles/实际 Run/Recovery 投影与授权前检查，不自动派工。  
D. 首个真实产品 caller 灰度：Cloud Auth；随后 Mobile / Desktop 单独晋级验收。  
E. Live Reporter 独立隔离 POC → Control Room 私有 Run TV；按证据决定是否需要新能力，不能靠自称“实时”通过。

不要求 A～E 合成一张大任务卡。每个切片有独立验证证据、风险与可回退边界。

## 10. 实施前必须明确的门禁与拒绝条件

1. **零费用**：如任何方案要求付费 Cloudflare 功能、付费写入存储或新服务器，立即停止并回到技术裁决，不能自动开通。
2. **Free 查询可达性**：如 Logs 在账号实际环境中无法按 Run ID 可控检索，不能伪称 POC 成功，也不能私自增加 D1/R2；应退回为“仅有控制台诊断 + GitHub 事实”的降级产品合同，再由维护者裁决是否接受。
3. **凭据隔离**：如 Live Reporter 无法在另一安全边界观察实时流，V1 保留阶段报道，不向 model shell 授密。
4. **Reporter 写 Issue**：同一 Issue 允许一条 reporter human-readable sticky comment，但不能替代 recovery_index marker，不能修改任务合同或 outcome。
5. **Workforce 调度权**：自动跨仓库施工、改 Issue/Project、修改发布权限、自动合并等任何控制面操作都必须有另行明确授权。
6. **短留存与日志缺口**：Workers Logs 不是审计归档；Artifact 也有到期窗口。历史恢复失败必须显示，不得静默重派从零。
7. **设计状态**：本文未经产品维护者正式接受前是 Proposed；不代表目标已经部署，亦不授权创建实施 Issue、修改生产密钥或执行工作流。

## 11. 证据与上游设计

- Organization policy: https://github.com/uichat-mira/.github/blob/main/AGENTS.md
- Source of truth: https://github.com/uichat-mira/.github/blob/main/docs/governance/source-of-truth.md
- Worker v2 design (draft, historical proposal): https://github.com/uichat-mira/.github/pull/69
- AGT-056: https://github.com/uichat-mira/.github/issues/70
- AGT-057: https://github.com/uichat-mira/.github/issues/71
- AGT-058: https://github.com/uichat-mira/.github/issues/72
- AGT-059 and actual Recovery contract: https://github.com/uichat-mira/.github/issues/73 ; https://github.com/uichat-mira/.github/blob/main/docs/governance/external-worker-recovery.md
- Shared runtime: https://github.com/uichat-mira/.github/blob/main/.github/workflows/mira-external-worker.yml
- Existing Control Room projection: https://github.com/uichat-mira/control-room/blob/prod/README.md

**一句话结论：** 不可靠的模型可以换班；GitHub 保护工程事实，Reporter 让过程可观察，Logs 保存有限现场，Workforce 管理被授权的执行，Control Room 只展示可追溯的真相。
