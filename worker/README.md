# Review sign-in

The preview's Review tab writes to GitHub issues (one per icon, labelled `icon` and `status: …`). Signing in needs a GitHub App and this small Cloudflare Worker, which swaps GitHub's login code for a token. Until both exist, the preview falls back to links that open GitHub.

## 1. Create the GitHub App

[New GitHub App](https://github.com/settings/apps/new):

- **Homepage URL:** `https://marcinbauer-ohf.github.io/ha-icons/`
- **Callback URL:** `https://ha-icons-auth.<your-subdomain>.workers.dev/callback` (you get the subdomain in step 2, so you can come back and fill it in)
- **Expire user authorization tokens:** untick it. Otherwise everyone gets signed out every 8 hours.
- **Webhook:** untick Active.
- **Repository permissions:** Issues: Read and write. Leave everything else at No access.
- **Where can this app be installed:** Only on this account.

Then create it, note the **Client ID**, and generate a **client secret**. Install the app on the `ha-icons` repository only (Install App in the sidebar).

## 2. Deploy the worker

```bash
cd worker
```

Put the Client ID into `CLIENT_ID` in `wrangler.toml`, then:

```bash
npx wrangler login
```

```bash
npx wrangler secret put CLIENT_SECRET
```

```bash
npx wrangler deploy
```

The deploy prints the worker's URL. Put it into the app's Callback URL (step 1) with `/callback` on the end.

## 3. Point the preview at it

In `sheet.template.html`, fill in `AUTH`:

```js
const AUTH = {client: '<Client ID>', worker: 'https://ha-icons-auth.<your-subdomain>.workers.dev'}
```

Rebuild and push.

## Who can do what

Anyone signed in can comment. Changing the status means changing labels, which needs **triage** access or higher on the repo. Without it, GitHub also opens new issues without their labels, so the issue won't show up in the preview. Give reviewers triage access under Settings → Collaborators.

The worker only redirects to the pages listed in `PAGES` in `index.js`: the Pages site and `http://localhost:8765/sheet.html` for local testing (`cd dist && python3 -m http.server 8765`).
