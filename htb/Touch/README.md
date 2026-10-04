# Touch (HTB, Windows / Release Arena)

Airport kiosk: Nexion DeviceHub on HTTPS, full-screen RDP session, boarding-pass print service that `Assembly.LoadFrom`s every `plugins\*.dll`.

Unauth serial leak becomes the portal password → kiosk RDP (NLA off) → Edge `file://` breakout → drop a **managed** plugin next to the TP-820 service → DeviceHub restart writes a ProgramData trigger → service re-runs `Initialize()` as SYSTEM.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — `PrinterPlugin` matching the host contract (`public void Initialize()`)

## Scripts

| File | What |
|------|------|
| `scripts/PrinterPlugin.cs` | CLR plugin: log `Environment.UserName`, copy `root.txt` onto the kiosk desktop |
| `scripts/PrinterPlugin.csproj` | `netstandard2.0` class library (host is net8.0 Windows Desktop) |

```bash
dotnet build scripts/PrinterPlugin.csproj -c Release
# drop bin/Release/netstandard2.0/PrinterPlugin.dll into the printer plugins\ folder
# then POST /api/printer/restart on DeviceHub (authenticated cookie)
```

A native implant (`DllMain` / `LoadLibrary`) is the wrong drop. The host never calls it.

No flags, VPN configs, or live passwords in this tree.
