# 02 — React2Shell

- CVE-2025-55182 (react-server-dom) + CVE-2025-66478 (Next).
- Next 15.0.0–15.0.4 podatne; patch 15.0.5.
- Endpoint Next.js: **POST /** + nagłówek **Next-Action** + multipart RSC Flight.
- PoC: https://github.com/freeqaz/react2shell (`detect.sh`, `exploit-redirect.sh`, `shell.sh`).
- MSF check ≠ run; redirect nie wymaga nc.
