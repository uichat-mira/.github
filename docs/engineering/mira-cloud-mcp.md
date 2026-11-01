# Mira Cloud · 内建服务 MCP 互操作约定（讨论稿）

> 状态：**Architecture Proposal / 跨仓库评审中**。不是已冻结的组织 Policy、正式 Token 合同或上线声明。
> 
> 维护归属：uichat-mira/.github · 首版：2026-11-01 · 适用于 Mira Cloud 内建服务、Cloud Agent 和未来自有客户端。

## 1. 目的与既定产品边界

Mira Cloud 是统一 Cloud Account 身份下的一组**独立内建服务**。观澜、拾言、Relay、Cloud Agent 等拥有各自的业务、数据与发布边界，**可以在明确授权下相互调用**。当前最明确的主动调用方是正在开发的 Cloud Agent；不因为这一实现顺序让观澜依赖 Agent。

- **MCP 是 Agent 消费业务能力的标准互操作协议，不是另一套账号、服务总线，也不是强制所有内部 RPC 都使用 MCP。** 非 Agent 的内部协作可保留清楚且有授权的领域 API。
- 自有服务与客户端应复用 Mira Cloud 登录体验：不为每个内建服务额外弹 OAuth 页面、要求粘贴 Token 或手动安装 MCP 服务；**免二次交互授权不等于后端免验证权限**。
- 服务互通不是内部超级权限。身份、消费者归属、业务读写和撤销仍由对应权威独立判定。
- 不预建统一 MCP Gateway、中心注册数据库、工具市场、代理编排平台、第二套 OAuth 登录或附加常驻服务；要增加时须先提供真实需求与测量证据。
- 本文补充 [Mira Cloud Core Specification](./mira-cloud.md) 和 [Mira Cloud Authentication Design](./mira-cloud-auth.md)，不取代其身份和部署决定。

## 2. 最小协议与拓扑

~~~text
Mira Cloud Agent / 未来获准的服务调用方
      │ 官方 MCP Client 或所在 Agent SDK 的薄适配
      │ HTTPS · Stateless Streamable HTTP（优先）
      ▼
Guanlan /mcp            其他内建服务 /mcp（按需）
      │                            │
      ▼                            ▼
各服务自己的权限校验、领域操作、数据存储

Cloud Auth：共享身份与受限凭证信任根；
不代理每次业务 MCP 调用，也不接管服务业务权限。
~~~

- 默认优先 **MCP 2026-07-28 + 官方 SDK + Stateless Streamable HTTP**。真实服务端/客户端的支持版本必须按运行时测试验证，明确仍需支持的 legacy 范围；不可仅凭规范名称推断兼容。
- 各服务维护自己的稳定 MCP 入口和工具 Schema。生产调用地址由服务配置管理，不把 Worker 名、Cloudflare Service Binding 或开发 URL 固化为通用服务合同。
- 第一阶段只需标准工具发现、列表和调用；Resources、Prompts、Tasks、MRTR、Apps、长连接通知等扩展按实际业务需求增量启用，不是 V1 前置条件。
- 不自行重写 JSON-RPC、MCP 版本握手或 OAuth 协议；优先复用成熟 SDK，服务端业务合同为单一真相源。

## 3. 薄服务目录与工具治理

第一版可以只用**部署配置里的可信静态服务目录**：服务 ID、目标 MCP 地址、允许的受众/audience、能力类别、超时/并发与取消策略、部署环境限制。目录中**不存用户令牌、消费者隐私和动态授权结果**。

- Agent 按任务发现和暴露**少量**工具，不把所有服务的工具 Schema 常驻模型上下文。动态工具列表缓存要遵守私有作用域。
- 服务端拥有工具名称、输入输出 Schema、实际操作与错误语义；客户端可收窄权限/上下文，但不得复制并独立维护第二套业务规则。
- 工具返回的网页、新闻、Markdown 视作不可信数据，不因出现在 MCP 结果中就成为系统指令。
- 同平台的 Service Binding 或内部 RPC 可以作为传输优化，但不得把云部署拓扑变成客户端协议和授权语义的依赖。
- 跨服务调用应设置超时、调用深度和循环防护，避免 Agent 工具自动触发无限链式调用。

## 4. 身份与业务委托：两个不同问题

需要同时知道：

1. **调用者身份**：哪一个 Mira 服务实例 / 运行时在调用？
2. **业务委托身份**：此操作代表哪个 Cloud Account、哪个稳定消费者、获得哪些 read/write 权限？

这两层都不能从模型填写的工具参数自行推断。

- Cloud Auth 是账户、会话和受限凭证的权威。目标资源服务应核验可信 issuer、签名/JWKS、audience、scope、到期和必要的调用主体/委托绑定，再判断所属账户与对象级业务权限。
- **不能跨服务转发万能 Bearer**。每个目标服务使用自己的 audience 和最小 scope；服务 A 转调 B 时必须获得有效且已收窄的 B 授权上下文，不能把 Shiyan 或 Relay 票据借给 Guanlan 使用。
- Cloud Agent 定时/无人值守工作的“服务主体 + 用户委托”签发、续期、撤销和消费者绑定，仍需跨仓库合同确认；**不能套用设备绑定 Cloud Session 冒充云 Agent 身份**。
- 短期签名凭证的撤销通常受有效期窗口约束。如产品要求即时停权，须明确在线验证或等价实证措施；不得把“停止续签”等同于“已签发 Token 即时失效”。
- **读写分离**：MCP 读取不得自动写消费状态。写操作必须单独受 scope、主体与资源权限保护；readOnly/idempotent 注解只是客户端提示，不能代替权限检查。
- 用户订阅/关注点更改仍需明确批准，不能被包装成 Agent 的普通写工具自行执行。
- 凭证只留在受信任运行时，不进入模型上下文、MCP 工具参数、持久会话文本、普通日志或测试快照。

## 5. 交互、错误与一致性

- 区分传输错误、认证失败（401/403）、MCP 工具 isError 与业务冲突。保留 structuredContent、原始文本和业务错误码，不将数据库故障伪装成空查询。
- **空新闻 items 但 nextCursor 非空 ≠ 查询结束**：扫描窗口无命中时应继续分页，下一页仍要重新授权。
- 对写工具，网络超时后结果可能已提交。使用同一个 operationId 做安全重试，服务端执行幂等和版本 CAS；收到 version_conflict 后必须重新做业务决策，不能静默覆盖较新的状态。
- 每次工具调用定义超时、取消、并发/限流、可安全重试条件、最小必要审计与 Trace ID。指标包括延迟、失败类别、请求 CPU / 数据库行操作 / 配额，不在日志暴露 Token、私人源链接或其他敏感数据。
- Token 过期、服务不可达、用户/消费者撤销、跨账户/错误 audience/scope 都要 fail-closed，并保留可解释的异常结果。

## 6. 与 SDK/平台解耦

- **MCP 服务端**使用服务所在语言的标准实现；既有 Guanlan 已使用官方 TypeScript SDK v2，不要求其他服务改用 Pi。
- **Cloud Agent**先核对自己的 Pi SDK 锁定版本、Agent Session/ResourceLoader/Extension 装配与权限管道。优先复用 Pi 内建 MCP Extension；若确有动态凭证或运行时约束，再使用官方 MCP Client 做一层薄适配。两条路径择一，不要叠两套工具系统。
- Pi CLI 的 MCP 配置不代表嵌入式 Pi SDK Session 已自动装载扩展。这个装配差异由 Agent 仓库负责验证，不成为整个 Mira Cloud 的协议依赖。
- MCP 不强制绑定 Cloudflare；服务可部署在 Worker、VPS 或其他环境，只要维护相同可验证的能力和权限合同。

## 7. 验证与推广次序

1. **T1/T2 契约**：工具 Schema、版本/legacy 兼容、错误语义、游标、幂等与权限反例。
2. **T3 服务端真实运行时**：实际 workerd/D1 或等效服务后端，验证跨账户、跨消费者、过期、错 audience/scope、无订阅、写 CAS、故障与重试；fixture 不算真实 Cloud Auth 端到端。
3. **T3/T4 跨服务链路**：Cloud Agent 以明确服务身份和用户委托调用 Guanlan，完成“新闻读取 → Agent 决策 → 受控写回 → 重启/恢复”，验证撤销与权限隔离。
4. **发布与容量闸门**：独立测量 CPU、D1 用量、网络、备份/回滚与 dev → test → prod 实际环境。协议通过不代表 Free 持续 CPU、生产安全或业务上线已获批。

首个实践可以是 **Cloud Agent → Cloud Guanlan**，但服务间互通约定是通用的，不能为了第一位调用方制造 Guanlan 特例或云 Agent 专属网关。

## 8. 已有实现与尚未落地（核对日期：2026-11-01）

| 范围 | 已核对的现实 / 仍缺的部分 |
| --- | --- |
| Guanlan | dev 已有官方 MCP TypeScript Server v2、只读新闻查询/WHOAMI、JWT/JWKS 与权限测试；消费状态 CAS 账本在领域层，**尚未公开正式 MCP 写工具、未完成真实 Cloud Auth 和生产部署** |
| Guanlan audience | 验证层配置已采用 mira:cloud-guanlan 和 guanlan.read；**不能推定 Cloud Auth 已有对应签发功能** |
| Cloud Auth | dev 的设备绑定 Cloud Session → audience-bound 短期凭证与 JWKS 已实现，当前签发支持 Shiyan/Relay；**云 Agent 委托、Guanlan audience/scopes 尚待合同和运行验收** |
| Cloud Agent | 已知采用 Pi SDK；未取得锁定版本与实际运行代码，不能宣称 MCP 自动装配、后台身份或写工具已经实现 |
| 跨服务生产 | 没有本次真实跨仓库 E2E、授权撤销和容量证据，不宣称上线 |

## 9. 需要与 Cloud Agent 线程共同收敛的事项

- Pi SDK 当前依赖、扩展装载位置、工具可见性、后台任务/取消/恢复和真实执行权威；
- Cloud Agent 的服务身份、账户委托、消费者绑定与撤销来源；
- Guanlan 受控写工具 Schema、scope、权限和账本 CAS 适配；
- 哪个独立 PoC 最省组件，又能给出真实授权/越权、读写与恢复证据；
- 是否有必须引入统一网关、事件消息或额外持久进程的**实际而非假设**需求。

本文件是可复用的组织级讨论基线。正式权限/Token claim、生产部署及跨仓库施工必须由各归属仓库的 Issue、代码和验收证据决定。

## 参考

- [MCP 2026-07-28 规范](https://modelcontextprotocol.io/specification/2026-07-28)
- [官方 TypeScript MCP SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Pi MCP / SDK](https://pi.dev/docs/latest/mcp)
- [Guanlan MCP 服务端](https://github.com/uichat-mira/cloud-mcp-guanlan/blob/dev/src/mcp/server.ts)
- [Cloud Auth 服务凭证合同](https://github.com/uichat-mira/cloud-auth/blob/dev/docs/service-credentials-v0.md)
