// Sign-in for the preview. GitHub's token endpoint needs the app's client secret and has no CORS,
// so this worker swaps the login code for a user token and hands it back to the page in the URL fragment.
// Only these pages can receive a token; never redirect anywhere taken from the request.
const PAGES = ['https://marcinbauer-ohf.github.io/ha-icons/', 'http://localhost:8765/sheet.html']

export default {
  async fetch(req, env) {
    const url = new URL(req.url)
    if (url.pathname !== '/callback') return new Response('Not found', {status: 404})
    // state is "<nonce>.<page index>.<icon>"; the page checks the nonce, we only pick the page from the allowlist
    const state = url.searchParams.get('state') || ''
    const page = PAGES[+state.split('.')[1]] || PAGES[0]
    const r = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', Accept: 'application/json', 'User-Agent': 'ha-icons-auth'},
      body: JSON.stringify({client_id: env.CLIENT_ID, client_secret: env.CLIENT_SECRET, code: url.searchParams.get('code')}),
    })
    const got = await r.json()
    const hash = got.access_token ? `gh_token=${encodeURIComponent(got.access_token)}` : `gh_error=${encodeURIComponent(got.error_description || got.error || 'sign-in failed')}`
    return Response.redirect(`${page}#${hash}&state=${encodeURIComponent(state)}`, 302)
  },
}
