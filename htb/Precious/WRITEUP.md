# Precious — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Precious (Easy Linux)  
**Date:** 2026-09-28  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document.

## TL;DR

pdfkit 0.8.6 command injection (not SSTI) → .bundle/config reuse → sudo YAML.load gadget → SUID bash -p

Full chain and neighbouring machines: [../2017-oldest-easies/WRITEUP.md](../2017-oldest-easies/WRITEUP.md).
