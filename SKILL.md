---
name: linkbuilding
description: Use when building backlinks to a site with an outreach tactic - broken link building, link gap (sites linking to competitors but not you), unlinked brand mentions, resource pages, guest posts, link reclamation, competitor dead pages, Moving Man (moved or closed resources), "best X" listicle inclusion, or skyscraper content - including finding prospects, checking dead links, counting referring domains, finding contacts and drafting outreach emails. Also use for plain requests like "get more backlinks", "build links to my site", "who links to my competitors", "find link opportunities", "why did I lose links" or "what can the linkbuilding skill do".
---

# Link building

## Overview

A playbook per tactic, each with a decidable rule at every step, plus one shared toolkit. Output is always a prospect table and drafted emails. **The skill never sends email.** The user sends.

## Tactics

| Tactic | File | Start here when |
|---|---|---|
| Broken link building | [broken-link-building.md](tactics/broken-link-building.md) | the niche has old resource lists and guides |
| Link gap | [link-gap.md](tactics/link-gap.md) | the user has clear competitors with more links |
| Unlinked brand mentions | [unlinked-mentions.md](tactics/unlinked-mentions.md) | the brand already gets talked about |
| Resource pages | [resource-pages.md](tactics/resource-pages.md) | the user has genuinely useful guides or tools |
| Guest posts | [guest-posts.md](tactics/guest-posts.md) | the user can write expert articles |
| Link reclamation | [link-reclamation.md](tactics/link-reclamation.md) | the site is older, has moved URLs, or lost links (do this first: quickest wins) |
| Competitor dead pages | [competitor-dead-pages.md](tactics/competitor-dead-pages.md) | competitors have pruned or moved old content |
| Moving Man | [moving-man.md](tactics/moving-man.md) | a tool or brand in the niche rebranded or shut down |
| "Best X" listicle inclusion | [listicle-inclusion.md](tactics/listicle-inclusion.md) | the user sells a product (start here for any SaaS) |
| Skyscraper | [skyscraper.md](tactics/skyscraper.md) | a competitor piece earns many links and the user can beat it |

When the user just says "build links", ask for the inputs below, then suggest an order: reclamation, then listicles (for a product) or unlinked mentions, then broken link building and competitor dead pages.

When the user asks what the skill can do, give a two-line summary and show the starter prompts in [prompts.md](prompts.md).

## Talking to the user

The user may not know SEO terms or tactic names. Run the session as a conversation, not a batch job.

**Starting:**
- Ask one question at a time. Start with the site, then what they want from it (more traffic to a page, links for a new product, recovering lost links).
- Recommend one tactic with a one-line reason, for example "Your site moved URLs last year, so reclamation is the quickest win." Offer the others only if they ask.
- Before the first step, say in two or three lines what the tactic does and what they will get at the end.

**Before each step:** say what is about to happen, roughly how long it takes, and whether it costs anything. Paid steps follow the paid-call rule below.

**After each step:**
- Give a short plain summary with numbers, for example "Checked 40 pages, found 12 dead links, 3 worth pitching."
- Show the top 5 to 10 rows as a small table with only the columns that matter for the decision. Save the full CSV and give its path. Never paste a whole CSV into chat.
- Say what looks promising and what was dropped, and why, in a line or two.
- End with a clear next choice: continue to the next step, adjust (a different niche keyword, a lower threshold), or stop here.

**Words:** explain a term the first time it comes up, in one short clause. Examples:
- referring domains: how many different sites link to that page;
- dead / recheck / review: broken for sure / might be a temporary error, check again later / redirects somewhere else, needs a human look;
- dofollow: a link that passes ranking value;
- prospect: a page we might ask for a link.

**Finishing a run (the handoff):**
1. Where the tracker CSV and any other files were saved.
2. How many emails are drafted, and the drafts themselves, ready to copy.
3. What the user does next: send the emails from their own inbox, set `status = sent` and `first_sent` in the tracker, and come back in about 7 days for the follow-ups.
4. One suggested next tactic, with its one-line reason.

Keep messages short. When a step finds nothing, say so plainly and suggest what to change, rather than padding the result.

## Inputs every run needs

Ask for anything missing before starting:

1. Target site URL.
2. Its niche, in a few words.
3. Candidate pages to promote (a list of URLs, or run `blb.py sitemap SITE` and pick from it).
4. Per tactic extras: competitors (link gap, competitor dead pages, listicles, skyscraper), brand names (unlinked mentions, listicles), the product's differentiator (listicles).

## Shared toolkit

Script: `scripts/blb.py` in this skill's folder (Python 3 standard library, no install). Run it with the full path to wherever the skill is installed, for example `python3 ~/.claude/skills/linkbuilding/scripts/blb.py`. Every subcommand takes targets as arguments or `--file` (one per line, or a CSV with a `url`, `dead_url` or `domain` column) and writes CSV to stdout or `--out`.

**Free:**

| Need | Command |
|---|---|
| Dead outbound links on prospect pages | `blb.py outbound PAGE [...]` |
| Check a list of URLs (and where redirects end) | `blb.py check URL [...]` (`--all` keeps live ones) |
| Domain registered / expired / unregistered | `blb.py rdap DOMAIN [...]` |
| First and last good Wayback copy | `blb.py wayback URL [...]` (slow, rate limited) |
| Every URL a site has had | `blb.py history DOMAIN/PATH` (narrow big sites with a path) |
| A site's sitemap URLs | `blb.py sitemap SITE` |
| Does a page link to a domain, mention a brand | `blb.py haslink PAGE [...] --domain D --brand "B"` |
| Qualify a prospect, find contact routes | `blb.py scan PAGE [...]` (published emails, contact/about/write-for-us pages, sponsored markers, CMS, socials, modified date) |
| Finding prospect pages | The agent's own web search |

**Paid (DataForSEO):**

| Need | Command | Rough cost |
|---|---|---|
| Referring domains per URL or domain | `blb.py refdomains URL [...]` | one call per 1,000 URLs |
| Linking pages, one per domain | `blb.py backlinks TARGET [--lost] [--broken] [--title "a\|b"]` | one call per target |
| Competitor's dead pages with links | `blb.py deadpages DOMAIN [--min-rd 3]` | one call per domain |
| Competitor's most-linked live pages | `blb.py toppages DOMAIN [--min-rd 20]` | one call per domain |
| Domains linking to all competitors, not the user | `blb.py gap USER COMP1 COMP2 [...]` | one call |

Measured October 2026: about **2.4 US cents per call plus 0.003 cents per row or URL**, so a 1,000-row call is about 5 cents. (Prices are written in cents because some agents rewrite a dollar sign followed by a digit when loading this file.) Calls are cheap; the thing to watch is running one call per target over long lists.

DataForSEO's crawl can be weeks old: re-check anything it calls dead or lost with `check` or `haslink` before pitching.

### Paid-call rule

Run every paid command without `--yes` first. It prints the call count and an upper-bound cost. Show the user that estimate and wait for a yes. Then re-run with `--yes`; it prints the actual cost. Use `--limit` to cap rows. Credentials come from `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` in the environment (or a `.env` file named by `DATAFORSEO_ENV_FILE`). If they are missing, say so, point the user to the README, and carry on with the free commands.

### Verdicts from `check` and `outbound`

| Verdict | Reasons | Meaning |
|---|---|---|
| dead | `http_404`, `http_410`, `dns_fail`, `connection_refused`, `parked`, `redirect_home`, `soft_404`, `owner_archived` | A real prospect |
| recheck | `blocked` (401/403/429), `server_error` (5xx), `timeout`, `ssl_error`, `dns_flaky` | Not dead yet. Re-run later; never pitch on a recheck, and never spend a paid call on one |
| review | `redirect_offsite`, `closed_notice` | Redirects to another site, or loads but says the business closed. Look by hand: acquired, moved (Moving Man), or dead? |
| live | `ok` | Dropped unless `--all` |

`dns_fail` is only given after DNS keeps failing on repeated lookups; a lookup that fails once and then works gives `dns_flaky`. Big publishers often block the script (`blocked`): check those in a browser before calling a link lost.

`owner_archived` means the site already swapped the link for a Wayback copy. The original is dead and the owner maintains links, which makes it a warm prospect.

## Prospect tracker

Every tactic writes to one CSV the user keeps, from [tracker-template.csv](tracker-template.csv). Keep it in the site's own project folder as `linkbuilding/tracker.csv`, with each run's raw CSVs in `linkbuilding/runs/YYYY-MM-DD-<name>/`. Ask where the project folder is if it is not obvious, never leave the tracker in a temp folder. The `status` column moves through: `found`, `drafted`, `sent`, `followed_up`, `linked`, `declined`, `no_reply`. Add rows; never delete them, so the same site is not pitched twice. Before drafting, check the tracker for the prospect's domain: one live conversation per site at a time, whatever the tactic.

## House rules for all copy

- No em dashes or en dashes anywhere, templates included. Check the rendered email, not just the source.
- Outreach leads with what helps the recipient, then offers the user's page as one option.
- No guessed email addresses and no paid email finders. Contacts come from bylines, author pages and contact/about pages (`scan` lists published ones).
- No paying for links. A site that asks for a fee is flagged for the user, never accepted by the skill.
- One follow-up per prospect, then stop.
- Thresholds in these files are starting values to tune, not proven rules. When a run teaches something, update the tactic file and its change log line.
