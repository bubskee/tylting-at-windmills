# Tylting at Windmills

Personal website and writing archive, built with [Astro](https://astro.build/) and hosted as static assets on [Cloudflare Workers](https://developers.cloudflare.com/workers/).

This site is the home for essays, experiments, and **Hill Climb Till It's Go Time** (HCTiGT). The authoritative repository is [bubskee/tylting-at-windmills](https://github.com/bubskee/tylting-at-windmills). Changes can be developed in [bfaber-centaur/tylting-at-windmills](https://github.com/bfaber-centaur/tylting-at-windmills) and proposed upstream via pull requests.

## Development

Requires Node.js 22.23.4 or later (see .node-version).

```sh
npm install
npm run dev
npm run build
```

*The First Step* comes from the canonical `bubskee/hctigt/posts/01-the-first-step.md` manuscript at build time, not a checked-in copy. The sync script generates `src/content/writing/the-first-step.md` and retrieves its local NASA image under `public/hctigt-assets/`. Both paths are gitignored. Site publication metadata, including the series preface above article titles, plus heading handling and Bilbo blockquote presentation live in `scripts/hctigt-publication.mjs`. The preface is independent site chrome; any similar paragraph in HCTiGT remains in the article, with its original footnote, until edited at the canonical source.

A normal `npm run build` (and `npm run dev`) imports the **current HCTiGT main** first. Run `npm run sync:hctigt` to refresh by hand. For a reproducible snapshot, set `HCTIGT_REF` to a 40-character Git commit SHA. Network failures stop the build rather than silently shipping a stale copy. HCTiGT commits **do not themselves trigger** a Cloudflare deployment; a site build must run to pick up revisions.

To publish additional non-HCTiGT posts later, use Markdown/MDX files in `src/content/writing` and fill in the collection frontmatter. There is deliberately no generic remote publishing framework yet.

## Cloudflare Workers deployment

The site lives under **[https://tylting.at/windmills/](https://tylting.at/windmills/)** (the registered domain is `tylting.at`, with a **y**). Until DNS is configured, the underlying Worker is accessible at [https://tylting-at-windmills.bfaber.workers.dev](https://tylting-at-windmills.bfaber.workers.dev).

Cloudflare dashboard → Workers & Pages → `tylting-at-windmills` is deployed from the authoritative **bubskee/tylting-at-windmills** repository.

- Production branch: `main`
- Build command: `npm run build`
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler preview` (optional preview builds)

The `wrangler.jsonc` config publishes Astro's static `dist/` directory. Astro builds into `dist/windmills/`, and `scripts/prepare-deploy.mjs` moves `_redirects` to `dist/` (where Cloudflare Workers processes it) and copies `robots.txt` to the domain root. No Worker script or Cloudflare Astro adapter is necessary.

### Custom domain (Dynadot registrar)

1. In Cloudflare **Domains → Onboard a domain**, add `tylting.at` to the same account, on the Free plan. Review and preserve any existing DNS records you need.
2. Cloudflare will assign **two account/zone-specific nameservers** on the `tylting.at` Overview page. If DNSSEC is already enabled for this domain at Dynadot, disable it before switching nameservers, then enable it again through Cloudflare after activation. At Dynadot choose **My Domains → Manage Domains → tylting.at → Action → DNS Settings → Name Servers**, enter those exact two nameservers and save. Do **not** copy nameservers from another Cloudflare domain.
3. Wait until the Cloudflare `tylting.at` DNS zone is **Active**. Then open **Workers & Pages → tylting-at-windmills → Settings → Domains & Routes → Add → Custom Domain** and enter `tylting.at`. Cloudflare creates the necessary DNS record and TLS certificate automatically.
4. Optionally add `www.tylting.at` as an additional custom domain and configure a redirect to the apex to avoid duplicate indexable hostnames.

The Astro `site` fallback in `astro.config.mjs` is `https://tylting.at`, with `base: '/windmills'` for the site's public URL prefix. The Cloudflare Worker redirects old root-level links through `public/_redirects`. If `SITE_URL` is defined among Cloudflare's **build-time** environment variables, ensure it is also set to `https://tylting.at`; otherwise the build-time override wins. For a future custom domain change, update `SITE_URL` or the fallback and redeploy.


## Site structure

- /windmills/ — homepage
- /windmills/writing/ — chronological writing
- /windmills/writing/the-first-step/ — first article / Colab
- /windmills/series/hctigt/ — HCTiGT series
- /windmills/projects/ — projects
- /windmills/about/ — about
- /windmills/rss.xml — RSS

Posts accept title, description, pubDate, optional updatedDate, optional series: hctigt, tags, draft, and optional crosspostUrl (e.g. LessWrong). The site's own URL remains the canonical URL.

The site uses no external services, analytics, database, or CMS. The First Step's manuscript and image are imported from `bubskee/hctigt` during each build; updates to prose, including removing any repetitive series introduction, must originate in HCTiGT.

### Article margin notes

At browser widths of 1280px or more, a lightweight client-side script shows
the existing rendered footnotes beside their in-text references, shifting notes
down to prevent overlap. Ordinary endnotes remain in place as the accessible
fallback on narrow screens or with JavaScript disabled. The visual copies are
hidden from assistive technology. No manuscript-specific formatting required.
Layout tests: `node --test scripts/sidenotes.test.mjs`.
