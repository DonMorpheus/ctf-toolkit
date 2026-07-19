# HackTheBox (`htb/`)

This directory is the **main HTB workspace** in [ctf-toolkit](https://github.com/DonMorpheus/ctf-toolkit): scripts, small PoCs, and pointers written while solving **HackTheBox** machines on a personal Kali lab.

Nothing here is a turnkey “attack platform” — each subdirectory belongs to **one retired or in-progress box** and assumes you already have legal access (HTB VPN, your own lab, or similar).

## What this folder is for

- **Reusable tooling** from real solves (clients, enum one-liners, pivot helpers).
- **Clear layout** so recruiters and future-you can see *which* box a script came from.
- **No secrets in git** — no `.ovpn`, flags, or live passwords (see repo root `.gitignore`).

## What you can find here

| Kind of content | Typical examples |
|-----------------|------------------|
| **Python** | Custom protocol clients, socket helpers, small automation |
| **Bash** | On-target enum, fuzz stubs, callback / exfil wrappers |
| **Per-box README** | Context for that machine, script index, how pieces fit together |
| **Linux / Windows patterns** | Whatever that box actually taught (e.g. local services, IPC, misconfig) |

Scripts are **machine-specific**. Always open the box’s README before running anything against an IP.

## Quick start

1. **Clone the repo**
   ```bash
   git clone https://github.com/DonMorpheus/ctf-toolkit.git
   cd ctf-toolkit/htb
   ```

2. **Connect to HTB** (on your machine, not in this repo)  
   Use your HackTheBox VPN config and confirm you can reach the target IP (`tun0`, ping, `nmap`).

3. **Pick a machine** from the table below and read its README  
   Example: [`Paperwork/README.md`](Paperwork/README.md) → then the scripts path listed there.

4. **Run tooling from your attacker host or from a shell on the box**  
   As documented per script (many helpers expect `python3`, env vars like `LHOST`, or SSH onto the target).

5. **Add a new box** when you finish another machine: create `htb/<BoxName>/`, drop scripts + README, add a row to the table — same pattern as existing entries.

## Machines

| Box | Difficulty | Path |
|-----|------------|------|
| **Paperwork** | Easy (Linux) | [`Paperwork/`](Paperwork/) — [`WRITEUP.md`](Paperwork/WRITEUP.md), [`edu/`](Paperwork/edu/), [`paperwork/`](Paperwork/paperwork/) scripts |
| **Connected** | Hard (Linux / FreePBX) | [`Connected/`](Connected/) — CVE-2025-57819, `ha_trigger` privesc |
| **Enigma** | Easy / Medium (Linux) | [`Enigma/`](Enigma/) — [`WRITEUP.md`](Enigma/WRITEUP.md), [`scripts/`](Enigma/scripts/) |
| **FireFlow** | Hard (K8s / Langflow) | [`FireFlow/`](FireFlow/) — Langflow → MCP → kubelet |
| **Nexus** | Medium (Linux) | [`Nexus/`](Nexus/) — Gitea leak → Krayin → SSH |
| **Makesense** | Medium (Linux / WP) | [`Makesense/`](Makesense/) — voice/OCR chain (Release Arena) |
| **ReactorWatch** | Medium (Linux / Next.js) | [`ReactorWatch/`](ReactorWatch/) — [`WRITEUP`](ReactorWatch/WRITEUP.md), [`scripts/`](ReactorWatch/scripts/) |
| **Bedside** | Medium/Hard (Linux / Season 11) | [`Bedside/`](Bedside/) — pdfminer → esm LFI → sudo torch checkpoint |

## Layout convention

```text
htb/
├── README.md              ← you are here (HTB overview)
└── <BoxName>/             ← official HTB machine name (e.g. Paperwork)
    ├── README.md          ← what this box is about, where scripts live
    └── <tooling>/         ← e.g. paperwork/ — actual .py / .sh files
```

## Standard lab notes

- **Resets** change IPs and sometimes paths — scripts use placeholders (`<TARGET_IP>`, `CHANGE_ME`, `LHOST`).
- **Scope:** HTB rules + your contract / local law; do not point this at systems you do not own or are not allowed to test.
- **Write-ups / flags** stay outside public repos or in private notes — this tree is for **code and structure**, not spoilers for active boxes.

## Disclaimer

Educational and portfolio use only. You are responsible for how and where you run these tools.