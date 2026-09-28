# Beep — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Beep (Medium Linux Elastix)  
**Date:** 2026-09-28  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document.

## TL;DR

TLS 1.0 + Elastix LFI graph.php → amportal.conf → SSH root reuse; old DH-SHA1 KEX

Full chain and neighbouring machines: [../2017-oldest-easies/WRITEUP.md](../2017-oldest-easies/WRITEUP.md).
