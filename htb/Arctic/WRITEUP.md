# Arctic — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Arctic (Easy Windows CF8)  
**Date:** 2026-09-28  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document.

## TL;DR

nmap -p- for :8500 JRun → CVE-2009-2265 upload → Meterpreter LPE (WOW64 migrate)

Full chain and neighbouring machines: [../2017-oldest-easies/WRITEUP.md](../2017-oldest-easies/WRITEUP.md).
