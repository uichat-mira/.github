
# Mira GitHub Worker v2 — 赛博施工队设计

Status: Draft design proposal  
Date: 2026-11-12  
Owner: uichat-mira/.github

## 1. 目标

Mira External Worker v1 已经证明了一条可用的 GitHub 原生施工链：

~~~text
GitHub Issue
  -> trusted enrollment
  -> OpenCode Worker
  -> repository-owned verification
  -> commit / push
  -> Draft PR
  -> structured evidence
~~~

v2 不重写这条链，也不引入新的任务数据库或自定义 Agent runtime。

v2 的目标是把现有单体 Worker 流程升级为一条可以长期运行、失败可恢复、权限可解释、验证可独立、状态可观察的 GitHub 原生施工流水线。

核心要求：

1. 施工模型不拥有 GitHub 写入权。
2. 施工成果必须先冻结成不可变 Candidate，再进入验收和交付。
3. 验收必须在新的 Runner / 干净 checkout 上重放同一 Candidate。
4. Worker 失败、供应商异常、验证失败或普通取消，不应自动等于成果消失。
5. 时间预算用于成本、调度和止损判断，不作为正常施工的“处决时钟”。
6. GitHub Issue、Actions、Artifact、Git branch / commit / PR 继续作为唯一工程事实链。
7. 施工队角色必须对应真实的软件边界，而不是给同一 Job 的几个 Step 换名字。

## 2. 当前 v1 基线

当前 Organization reusable workflow：

- .github/workflows/mira-external-worker.yml

现有能力已经包括：

- 绑定一个明确的开放 Issue；
- 绑定显式 delivery base 与 base SHA；
- 读取当前 Organization policy、repository AGENTS.md 与 pinned execute-work-item Skill；
- run-scoped provider / model；
- 付费与 native free Worker 路线；
- OpenCode repository read/edit、shell、build/test、web/network 能力；
- trusted repository-owned verification；
- isolated feat/worker-... branch；
- Draft PR；
- worker-run.json、trajectory.jsonl、verification log、changed-file summaries 等 evidence package。

现有主要缺口：

- Candidate 代码只有在 Worker 正常返回、verification 通过以后才 commit / push；
- Worker 中途失败时，Artifact 保存了诊断信息，但不一定保存完整可恢复 patch；
- trusted verification 仍在模型刚修改过的同一 workspace 中执行；
- Worker reusable workflow 当前顶层权限包含 GitHub 写权限，虽然模型没有专用 GitHub mutation tool，但权限边界仍可进一步收紧；
- 30 / 45 / 60 分钟 caller timeout 仍被当作正常执行上限；
- evidence 是“黑匣子”，还没有稳定的人类可读现场报道和续工入口；
- 还没有真正的 Foreman / 调度层。

## 3. 不可动摇的设计原则

### 3.1 Agent 不拥有工程事实

模型输出只能作为施工报告。

以下对象才拥有事实：

- Issue：任务合同；
- exact base SHA：施工起点；
- Candidate：候选代码；
- Actions job result：执行状态；
- verification evidence：验证结果；
- branch / commit / PR：交付状态；
- environment / release：部署现实。

模型说“完成”“测试通过”“已修复”不能替代上述证据。

### 3.2 施工与 GitHub 写入分离

Worker Job：

- contents: read
- issues: read
- 无 pull-requests: write
- 无 merge / Issue outcome / release / deployment authority

Delivery Job 才获得：

- contents: write
- pull-requests: write

Reusable workflow 的 caller 仍需提供足够的权限上限，但各内部 Job 必须继续按最小权限降级。

### 3.3 Candidate 先于 Verification

Worker 结束后，任何 commit / push / PR 之前，trusted Capture 阶段先冻结 Candidate。

后续 Verify、Recovery、Delivery 都只能消费这一份 Candidate，不允许重新从 Worker workspace 猜测“最终版本”。

### 3.4 Verification 必须换工地

Verify Job 使用新的 GitHub Runner：

~~~text
checkout exact base SHA
  -> download Candidate Artifact
  -> verify digest
  -> apply patch
  -> verify reconstructed tree identity
  -> run repository-owned verification
~~~

这样 verification 证明的就是后续交付的同一份候选代码，而不是一个仍可被 Worker 修改的 workspace。

### 3.5 时间预算不是生命上限

30 / 45 / 60 分钟属于历史执行预算，不应继续承担“正常自动杀死 Worker”的语义。

正常结束条件应是：

- completed；
- blocked；
- provider / harness error；
- maintainer cancel / handoff；
- explicit policy stop。

仍保留一个远高于正常任务预算的 runaway fuse，只用于：

- 无限循环；
- 永久挂起；
- 无法退出的子进程；
- 明显失控的异常执行。

GitHub Actions 当前 job timeout 默认 360 分钟。v2 不应把一个远低于平台上限的数字继续解释为统一工时制度。

## 4. 角色模型

### 4.1 Enrollment — 门房

非 AI。

职责：

- 验证调用者；
- 读取 Issue；
- 冻结 base branch / base SHA；
- 过滤 trusted maintainer amendments；
- 计算 contract_fingerprint；
- 检查是否存在上一轮 Recovery Candidate；
- 生成 immutable run identity。

不得：

- 修改代码；
- 接受 Issue；
- 决定功能完成。

### 4.2 Worker — 施工牛马

AI + OpenCode。

职责：

- 读 Issue / policy / repository instructions；
- 读代码；
- 修改 workspace；
- 运行自身能力范围内、与任务风险匹配的开发测试；
- 报告 blocker 和已知 validation gap。

不得：

- push；
- 开 PR；
- merge；
- 修改 Issue outcome；
- release / deploy；
- 把自己的测试报告当作 trusted verification。

### 4.3 Capture — 成果保全员

非 AI，trusted workflow code。

职责：

- 在 Worker 结束、失败或可处理取消后冻结 workspace；
- 生成完整 binary patch；
- 生成 Candidate manifest；
- 计算 digest 与 tree identity；
- 上传 Candidate Artifact；
- 生成最小恢复信息。

Capture 不判断功能正确与否。

### 4.4 Reporter — 随队记者

Reporter 是投影层，不是权威层。

它负责把机器事实转换成人类可读状态，例如：

~~~text
Mira Worker · Run 4312...
状态：施工中 / 候选已保存 / 验证失败 / 已交付
耗时：47m
Candidate：#3
变更：8 files
最近可信事件：T2 contract test failed
是否可续工：yes
~~~

Reporter 不能：

- 把 Worker 自述改写成 PASS；
- 接受 Issue；
- 决定合并；
- 覆盖 trusted verification。

#### v2.0 Reporter

v2.0 只保证阶段边界报道：

- enrolled；
- Candidate captured；
- verification result；
- delivery result；
- final / recoverable state。

它应更新同一条 Issue comment，而不是制造大量评论。

#### Live Reporter

真正的施工中近实时外部报道是目标能力，但不能为了直播把 issues: write credential 暴露给拥有 shell 的 Worker Runner。

因此 Live Reporter 不作为 v2.0 的安全前提。

未来可采用独立 Reporter Bridge：

~~~text
Worker telemetry (untrusted)
        ->
Reporter Bridge / GitHub App
        ->
single Issue status comment
~~~

Bridge 可以发布：

- tool / test lifecycle；
- checkpoint；
- provider retry；
- long-running / no-new-observable-event；
- candidate captured；
- cancellation / runner loss。

Worker telemetry 仍然只是 telemetry；可信 pipeline state 必须从 GitHub Actions / Candidate / Verify 读取。

### 4.5 Verify — 验收员

非 AI 为默认。

职责：

- 新 Runner；
- exact base SHA；
- 重放 Candidate；
- 运行 caller / repository 拥有的 verification profile；
- 输出结构化 T1–T3 / build / static evidence；
- 明确 skipped / not-applicable coverage。

若任务需要 T4 / T5、浏览器或真实设备证据，应由相应能力的独立执行者承担，不能为了统一流程强迫普通 Worker 做它不具备能力的验收。

### 4.6 Delivery — 交付员

非 AI，唯一常规 GitHub 写入角色。

前置条件：

- Candidate identity 已冻结；
- required verification PASS；
- delivery base / contract 未发生禁止交付的漂移；
- 没有明确 blocker。

职责：

- 创建 isolated worker branch；
- commit exact verified Candidate；
- push；
- 创建 Draft PR；
- 写入 Candidate / verification / run pointers；
- 校验 PR base / head / Draft boundary。

不得：

- merge；
- close / accept Issue；
- promote environment；
- release。

### 4.7 Foreman — 工头

不属于 mira-external-worker.yml 的底层施工 primitive。

Foreman 位于流水线上层，根据 GitHub 状态决定：

- 哪张卡可派；
- 免费还是付费 Worker；
- 是否存在 Recovery Candidate；
- 续工、换人还是升级维护者；
- 是否因依赖未满足而不派；
- 是否已连续返工达到人工接管条件。

Foreman 不直接写业务代码。

## 5. Workflow 拓扑

目标结构：

~~~text
Issue
  |
  v
Enrollment
  |
  v
Worker
  |
  v
Capture --------------------+
  |                         |
  | Candidate Artifact      | Reporter projection
  v                         |
Verify <--------------------+
  |
  +-- FAIL / BLOCKED --> RECOVERABLE
  |
  v PASS
Delivery
  |
  v
Draft PR
~~~

建议 v2 将当前一个大 Job 拆成至少：

- enrollment
- worker_capture
- verify
- delivery
- report

worker_capture 暂时保持同一 Runner，是因为 Capture 必须读取 Worker 的当前 workspace。

Verify 和 Delivery 必须使用新的 Runner。

## 6. Candidate Contract

v2.0 优先采用 binary patch，而不是要求 Worker 创建 commit。

原因：

- 当前 Worker 的职责是修改 workspace，不拥有 Git mutation；
- patch 最贴近现有行为；
- OpenAI 的非交互 CI 示例同样使用 git diff --binary 将 Agent 变更跨 Job 传递；
- git bundle 更适合已经拥有 commit graph 的 Agent 输出，可作为后续替代实现。

建议 Artifact：

~~~text
candidate.patch
candidate.json
worker-run.json
trajectory.jsonl
worker-output.txt
~~~

建议 candidate.json 至少包含：

~~~json
{
  "schema_version": 1,
  "repository": "owner/repo",
  "issue_number": 123,
  "run_id": "4312...",
  "run_attempt": "1",
  "base_branch": "dev",
  "base_sha": "...",
  "contract_fingerprint": "sha256:...",
  "candidate_patch_sha256": "sha256:...",
  "candidate_tree_oid": "...",
  "provider": "...",
  "model": "...",
  "worker_outcome": "success|failure|blocked|cancelled",
  "created_at": "..."
}
~~~

Capture 的 trusted implementation 可采用类似：

~~~bash
git add -A
git diff --binary --cached "$BASE_SHA" > candidate.patch
git write-tree
sha256sum candidate.patch
~~~

具体命令必须在实现卡中验证 symlink、binary、delete、rename、untracked file 和 empty candidate 行为。

## 7. 状态模型

v2 不把 Actions 的 success / failure / cancelled 直接当作工程状态。

建议工程状态：

~~~text
ENROLLED
  -> WORKING
  -> CANDIDATE_CAPTURED
       -> VERIFY_FAILED -> RECOVERABLE
       -> BLOCKED       -> RECOVERABLE
       -> VERIFIED
            -> DELIVERED
                 -> DRAFT_PR
~~~

重要语义：

~~~text
WORKER_FAILED + recoverable Candidate
  = RECOVERABLE

WORKER_FAILED + no Candidate
  = FAILED
~~~

普通 Worker 失败不应擦除已经完成的有效施工。

## 8. Recovery / 续工

每次 Enrollment 必须先检查同 Issue 最近的可信 Worker 状态。

Reporter comment 可以保存机器 marker，作为 GitHub 内部投影：

~~~html
<!-- mira-worker-v2
run_id=...
candidate_artifact=...
base_sha=...
contract_fingerprint=...
state=RECOVERABLE
-->
~~~

实际事实仍由：

- referenced Actions run；
- Candidate Artifact；
- exact base SHA；
- manifest digest

共同决定。

续工规则：

1. 没有 Candidate：正常从当前合同开工。
2. 有 Candidate，contract fingerprint 未变化：优先恢复并检查已有成果。
3. 有 Candidate，但 Issue / trusted amendment 已变化：先比较合同漂移，再决定继续、部分复用或废弃。
4. Candidate 无法在 exact base 上重放：标记 recovery failure，不允许静默从头施工。
5. Candidate 已 verified 但 Delivery 失败：不得重新跑模型；只重试 trusted Delivery。
6. Candidate verification failed：下一班应继承 Candidate 和失败 evidence，避免重复 discovery。

Candidate retention 应长于普通诊断 evidence；具体天数由实现卡根据仓库 Artifact policy 验证后确定。

## 9. Cancellation 与成果保全

普通 GitHub workflow cancellation 会先尝试中断当前进程，并允许符合条件的 cleanup step 继续；GitHub 最终仍存在强制终止窗口。

因此 v2 必须把 Capture 设计成：

- 无模型调用；
- 无 dependency install；
- 无长网络操作；
- bounded；
- seconds-level；
- 可在失败路径运行。

但 v2 不得声称“任何取消都绝不丢代码”。

以下情况仍可能没有 Recovery Candidate：

- Runner / VM 突然丢失；
- GitHub infrastructure failure；
- force cancel；
- Capture 自身 I/O / Artifact failure；
- Worker 尚未产生任何修改。

v2.0 目标是解决“可控失败和普通结束时不丢活”。

v2.1 再评估 periodic checkpoint，用于缩小 Runner 猝死时的损失窗口。

## 10. Reporter 发布合同

Reporter 的 GitHub Issue comment 应保持单条更新，并区分：

### Trusted facts

例如：

- Candidate digest；
- Verify result；
- Delivery result；
- exact PR URL；
- run / artifact identity。

### Worker telemetry

例如：

- 当前 tool；
- Worker 自己运行的 tests；
- provider retry；
- 最近 observable event。

### Human-readable narrative

可以是确定性模板，也可以未来由低成本模型润色。

AI narrative 永远不能覆盖 trusted fact。

## 11. 权限边界

目标权限：

| Job | contents | issues | pull-requests | Provider secret |
| --- | --- | --- | --- | --- |
| Enrollment | read | read | none | no |
| Worker/Capture | read | read | none | yes |
| Verify | read | read | none | no |
| Reporter | read | write | none | no |
| Delivery | write | read | write | no |

Reporter 与 Worker 如果运行在同一 VM，就不能被宣称为强 credential isolation。

因此真正 Live Reporter 若需要持续 issues: write，应使用外部 Bridge / GitHub App 或其他独立执行边界；不要把高权限 token 仅靠“不同进程”包装成安全隔离。

## 12. 测试与验收原则

v2 不改变 Organization Testing Standard。

Worker 自测用于施工反馈。

Verify Job 负责 feature-PR 所需的 trusted static / T1 / T2 / cheap T3 evidence。

T4 / T5 继续属于：

- environment promotion；
- deployed candidate；
- real device / browser / external integration；

而不是每张 GitHub Worker 卡的统一仪式。

没有浏览器能力的 Worker 不应因未执行浏览器验收而自动失败。

## 13. 分阶段落地

### v2.0 — Durable Candidate Pipeline

必须先完成：

- split Worker / Verify / Delivery；
- Candidate Contract；
- fresh-runner verification；
- recovery Candidate；
- phase Reporter；
- timeout -> runaway fuse 语义；
- failed verification 不丢 Candidate；
- delivery failure 不重新调用模型。

### v2.1 — Checkpoint + Live Reporter

根据 v2.0 真实运行数据再决定：

- periodic / event-driven checkpoint；
- Reporter Bridge；
- near-real-time Issue status；
- runner-loss detection；
- recovery artifact retention policy。

不要为了“直播感”提前引入一个新的高权限常驻服务。

### v2.2 — Foreman

在底层施工 primitive 足够可靠以后，再实现：

- issue dependency scheduling；
- free / paid Worker routing；
- retry / continuation policy；
- provider health / quota awareness；
- repeated-failure escalation；
- concurrency / queue。

Foreman 必须消费 GitHub 事实，不维护第二套任务真相源。

## 14. 非目标

v2.0 不做：

- 新任务数据库；
- 自定义 Agent runtime；
- 多 Agent debate；
- 自动 merge；
- 自动 Issue acceptance / closure；
- 自动 environment promotion；
- 复杂成本优化器；
- 浏览器验收统一化；
- 因为引入“记者”而复制一套 observability database；
- 因为需要 Recovery 就把未经验证代码冒充正式 branch 交付。

## 15. 需要实现阶段验证的开放问题

以下问题在设计阶段不假装已经解决：

1. 普通 workflow cancellation 下，怎样最稳定地保证 Worker 中断后 Capture 获得 cleanup 窗口；
2. Candidate patch 对 binary / symlink / rename / submodule 的准确边界；
3. Candidate Artifact 的 retention 与组织 storage 成本；
4. contract fingerprint 的规范化输入；
5. Reporter comment 的可信 marker 与并发更新冲突；
6. 当前各 product caller 的 immutable Worker SHA 如何渐进升级；
7. free Worker 与 paid Worker 是否共享完全相同的 v2 Candidate pipeline；
8. provider credential 与 shell Worker 的更强隔离是否需要本地 inference proxy。

这些问题应通过小型 fixture / real run 验证，而不是继续在设计文档中推断。

## 16. 参考

### Mira 当前事实

- .github/workflows/mira-external-worker.yml
- docs/governance/external-worker-evidence.md
- docs/governance/external-worker-provider-model.md
- docs/engineering/testing-standard.md
- skills/create-work-item/SKILL.md

### 外部实现参考

- GitHub Actions workflow cancellation:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-cancellation
- GitHub reusable workflow permission propagation:
  https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- GitHub Actions workflow timeout semantics:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- OpenAI non-interactive GitHub CI patch handoff:
  https://learn.chatgpt.com/docs/non-interactive-mode
- GitHub Agentic Workflows Safe Outputs:
  https://github.github.com/gh-aw/reference/safe-outputs/
- GitHub Agentic Workflows PR bundle handoff:
  https://github.github.com/gh-aw/reference/safe-outputs-pull-requests/

## 17. 设计结论

Mira GitHub Worker v2 的核心不是“更聪明的牛马”，而是：

> **让不可靠的执行者运行在可靠的工程流水线上。**

Worker 可以失败、换模型、换班、被维护者中止。

只要 Candidate、验证、权限与交付边界仍然完整，工程就不应该跟着一次模型会话一起消失。
