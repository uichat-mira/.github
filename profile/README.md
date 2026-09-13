<p align="center">
  <img src="https://github.com/uichat-mira.png?size=160" width="96" alt="Mira" />
</p>

<h1 align="center">Mira</h1>

<p align="center"><strong>Local-first personal AI, built around a desktop host.</strong></p>

<p align="center">
  Chat is the beginning. Mira is growing into a workspace that can hold conversations, knowledge, tools, devices, and the work around them together.
</p>

<p align="center">
  <a href="https://mira.tomz.io">Website</a>
  ·
  <a href="https://github.com/uichat-mira/uichat-mira-docs">Docs</a>
  ·
  <a href="https://control.mira.tomz.io">Control Room</a>
</p>

<p align="center">
  <a href="https://control.mira.tomz.io">
    <img src="https://control.mira.tomz.io/embed/github-overview.svg" width="900" alt="Mira Control Room live organization snapshot" />
  </a>
</p>

---

## No 996. No exploitation.
## 反对 996。反对以奋斗之名压榨劳动者。

**Mira is built for people. It will not celebrate a culture that consumes them.**

We oppose illegal forced overtime, unpaid overtime, coercive “voluntary” overtime, and any practice that pressures workers to surrender rights they are entitled to by law.

If a business can survive only by taking people's nights, weekends, health, and dignity without lawful compensation, **the problem is not that its employees are not working hard enough. The problem is the business.**

Mira's source code is released under the MIT License. We keep that freedom deliberately. But freedom to use our code is **not** our endorsement of how you treat the people who build your products.

**Do not use “open source” as a prettier word for free labor.  
Do not call exploitation dedication.  
Do not call fear voluntary.  
And do not call 996 progress.**

**Mira 是为人而做的。我们不会歌颂一种消耗人的工作文化。**

我们反对违法强制加班、无偿加班、以明示或暗示方式强迫员工“自愿加班”，也反对任何诱导、逼迫劳动者放弃其依法享有权利的行为。

如果一家企业必须依靠夺走员工的夜晚、周末、健康和尊严，并且拒绝给予合法补偿才能维持运转，**问题不是员工还不够努力，问题就是这家企业本身。**

Mira 的源代码继续采用 MIT License。我们有意保留这种自由。但你有自由使用我们的代码，**不等于我们认可你如何对待替你写代码、做产品、维持系统运转的人。**

**不要把“开源”包装成免费劳动。  
不要把压榨叫作奋斗。  
不要把恐惧之下的服从叫作自愿。  
更不要把 996 叫作进步。**

**People are not infrastructure. 人不是基础设施。**

[Read the full Mira Fair Work Statement / 阅读完整 Mira 公平劳动声明 →](https://github.com/uichat-mira/.github/blob/main/FAIR-WORK.md)

---

Mira is a small family of projects built around one idea: keep the useful parts close to the user, make powerful capabilities understandable, and let each layer own only what it should.

## The core

| Project | Role |
| --- | --- |
| [**Mira Desktop**](https://github.com/uichat-mira/mira-desktop) | The local-first host and main workspace for chat, knowledge, tools, files, and personal workflows. |
| [**Mira Mobile**](https://github.com/uichat-mira/mira-mobile) | The companion on your phone: mobile interaction, device capabilities, and reliable connection back to Mira. |
| [**Mira Relay**](https://github.com/uichat-mira/uichat-mira-relay) | A deliberately small transport bridge between Mobile and Desktop. It forwards traffic; it does not become the Mira cloud backend. |

## Around the core

| Project | Role |
| --- | --- |
| [**Mira Docs**](https://github.com/uichat-mira/uichat-mira-docs) | Product, architecture, engineering notes, and the public map of how Mira fits together. |
| [**Control Room**](https://github.com/uichat-mira/control-room) | A read-only operational view of the organization, builds, runtime, governance, and public infrastructure. |
| [**Cloud Shiyan**](https://github.com/uichat-mira/cloud-shiyan) | Organization-owned cloud runtime work for Mira Cloud. Currently in bootstrap. |

## How we build here

- **Local first.** The desktop host remains the center of gravity; network services should add reach without quietly taking ownership away from it.
- **Small, verifiable steps.** Prefer changes that can be implemented, reviewed, tested, and reversed in a short loop.
- **One truth for each job.** Code and runtime describe what exists; Issues own engineering work; Organization docs own shared policy; Control Room and the website are projections, not competing ledgers.
- **Boundaries matter.** A relay transports. A cockpit observes. A mobile client connects. Clear ownership keeps the system understandable as it grows.

## Start here

Want to **use or understand Mira**? Start with [Mira Desktop](https://github.com/uichat-mira/mira-desktop) and the [documentation](https://github.com/uichat-mira/uichat-mira-docs).

Want to **see what the organization is doing right now**? Open the [Mira Control Room](https://control.mira.tomz.io).

Want to **work with the code or with an AI engineering agent**? Read the current [Organization collaboration entry](https://github.com/uichat-mira/.github/blob/main/AGENTS.md) first; repository-specific contracts take it from there.

---

<p align="center"><sub>Active development · one small, usable improvement at a time.</sub></p>
