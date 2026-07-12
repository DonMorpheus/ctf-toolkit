# Push `ctf-toolkit` to GitHub (Don_Morpheus)

## 1. Add SSH key to GitHub

1. Open https://github.com/settings/keys (logged in as **Don_Morpheus**).
2. **New SSH key** — paste contents of:

   `~/.ssh/id_ed25519.pub` on this Kali VM

3. Test:

   ```bash
   ssh -T git@github.com
   ```

   Expect: `Hi Don_Morpheus! You've successfully authenticated...`

## 2. Create empty repo on GitHub

- Name: **`ctf-toolkit`**
- Public
- **Do not** add README/license (already in local clone)

URL: `https://github.com/Don_Morpheus/ctf-toolkit`

## 3. Push from Kali

```bash
cd ~/github/ctf-toolkit
git config user.name "Don_Morpheus"
git config user.email "YOUR_GITHUB_EMAIL"
git remote add origin git@github.com:Don_Morpheus/ctf-toolkit.git
git branch -M main
git push -u origin main
```

## 4. Pin repo for HR

Profile → **Customize your pins** → select **ctf-toolkit**.

Optional: create profile repo per `profile/README.md`.