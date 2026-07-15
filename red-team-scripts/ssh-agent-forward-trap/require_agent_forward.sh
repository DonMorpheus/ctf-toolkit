#!/bin/bash
# ForceCommand helper: session allowed only when client used ssh -A (forwarded agent).
if [[ -z "${SSH_AUTH_SOCK:-}" ]] || [[ ! -S "${SSH_AUTH_SOCK}" ]]; then
  echo "ACCESS DENIED: ForwardAgent required (ssh -A). All other methods are disabled."
  echo "Example: ssh -A -i <key> legacy@$(hostname -f 2>/dev/null || echo host)"
  exit 1
fi
if [[ -n "${SSH_ORIGINAL_COMMAND:-}" ]]; then
  exec /bin/bash -c "$SSH_ORIGINAL_COMMAND"
fi
exec /bin/bash -l