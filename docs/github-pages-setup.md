# Hosting the Use Case Dashboard on GitHub Pages

A step-by-step guide to get the Infrastructure Monitoring Use Case Dashboard running on GitHub Pages — free, no server required.

---

## Prerequisites

- A GitHub account ([github.com](https://github.com))
- Git installed on your machine (`git --version` to check)
- The repository files: `index.html`, `data.js`, and `custom-text.js`

---

## Step 1: Create a New GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it something like `infra-monitoring-use-cases`
3. Set visibility to **Public** (required for free GitHub Pages) or **Private** (requires GitHub Pro/Enterprise for Pages)
4. Check **"Add a README file"**
5. Click **Create repository**

---

## Step 2: Push the Dashboard Files

```bash
# Clone your new repo
git clone https://github.com/YOUR_USERNAME/infra-monitoring-use-cases.git
cd infra-monitoring-use-cases

# Copy the required files
cp /path/to/repo/index.html .
cp /path/to/repo/data.js .
cp /path/to/repo/custom-text.js .

# Push to GitHub
git add index.html data.js custom-text.js
git commit -m "Add use case dashboard"
git push origin main
```

Or use the GitHub Web UI: click **"Add file"** → **"Upload files"** and upload the three files.

---

## Step 3: Enable GitHub Pages

1. In your repo, go to **Settings** (gear icon, top menu bar)
2. In the left sidebar, click **Pages** (under "Code and automation")
3. Under **"Build and deployment"**:
   - **Source:** Select **"Deploy from a branch"**
   - **Branch:** Select **`main`** and folder **`/ (root)`**
4. Click **Save**

---

## Step 4: Access Your Dashboard

1. Wait 1–2 minutes for GitHub to build and deploy
2. Your dashboard will be live at:

```
https://YOUR_USERNAME.github.io/infra-monitoring-use-cases/
```

3. The URL also appears at the top of the **Settings → Pages** section once deployed
4. You'll see a green checkmark next to your latest commit when deployment is complete

---

## Updating the Dashboard

When use case content changes:

1. Run `python3 build.py` to regenerate `data.js` from `use-cases/*.md`
2. Commit and push `data.js`
3. GitHub Pages auto-redeploys within ~60 seconds

---

## Optional: Custom Domain

If you want a cleaner URL like `usecases.yourdomain.com`:

1. Go to **Settings → Pages**
2. Under **Custom domain**, enter your domain
3. Add a **CNAME** record in your DNS pointing to `YOUR_USERNAME.github.io`
4. Check **"Enforce HTTPS"**

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 404 error | Make sure the file is named `index.html` |
| Page not loading | Check Settings → Pages shows a green "Your site is live" message |
| Old version showing | Hard refresh with `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) |
| Private repo, no Pages | GitHub Pages on private repos requires GitHub Pro or Enterprise |
