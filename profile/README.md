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
