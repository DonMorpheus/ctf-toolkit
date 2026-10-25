#!/usr/bin/env bash
set -euo pipefail
TARGET="${TARGET:?export TARGET=<ip>}"
echo "${TARGET} airsnacks.htb dutybound.htb"
echo "# append that line to /etc/hosts"
