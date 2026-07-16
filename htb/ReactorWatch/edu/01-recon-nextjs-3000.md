# 01 — Recon :3000

- nmap myli się (`ppp?`) — to HTTP Next.js.
- Dowód wersji: chunk `517-*.js` → `version:"15.0.3"`.
- GET `/` = prerender (`x-nextjs-prerender: 1`).
- `/api/*` = 404 HTML, bez JSON/auth.
- Nie szukaj tokenów w curl — ich nie ma na tym porcie.
