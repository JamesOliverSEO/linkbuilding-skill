# Competitor dead pages

Find pages on competitor sites that are dead but still have backlinks, then pitch the user's page to every site linking to them. A broken link building variant that starts from the competitor, not the linking page.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md). Thresholds are starting values to tune.

## Step 1. Find the competitor's dead pages

Two routes. Prefer the free one for a first look.

**Free route (Wayback):**
1. `blb.py history COMPETITOR.com/section --limit 2000 --out hist.csv`. Narrow big sites with a path (`/blog`, `/learn`, `/guides`); a whole big domain times out.
2. `blb.py check --file hist.csv --out dead.csv` keeps the URLs that are not live today.
3. `blb.py refdomains --file dead.csv` (paid but cheap: one call covers up to 1,000 URLs, about $0.03 to $0.05) to see which still have links.

**Paid route (DataForSEO crawl):** `blb.py deadpages COMPETITOR.com --min-rd 3 --limit 100` (about $0.03 per competitor). Faster and ranked, but the crawl can be weeks old, so **always re-check the results** with `blb.py check` before going further.

**Pass:** confirmed dead today and 3 or more referring domains.

## Step 2. Match a replacement

As [broken-link-building.md](broken-link-building.md) step 4 (Wayback snapshot, same topic and purpose). A dead page with many referring domains and no match on the user's site is a content opportunity: mark `needs_content` and report it.

## Step 3. Get the linking pages

**Do:** `blb.py backlinks DEAD_URL --limit 200` (paid, one call per dead page; only run it on matched pages). Keep `dofollow = True` rows from on-topic sites.

**Then:** `blb.py haslink URL_FROM [...] --domain COMPETITOR.com` to confirm each page still links to the competitor today.

## Step 4. Contact and draft

As [broken-link-building.md](broken-link-building.md) steps 5 and 6. Variant A or B fits as written: the linking page has a broken link to the competitor's dead page. Do not name or criticise the competitor beyond saying the page is gone.

**Record:** `tactic = competitor-dead-pages`, `dead_url` = the competitor page.

## Change log

- First real run: the free route checked about 130 old URLs (about 9 minutes; `check` paces one request per host every few seconds) and found a quarter dead, but exact-URL `refdomains` showed no links on almost all of them. The paid `deadpages` route (about 2.5 cents) found the linked dead pages the free route missed, because it catches http/www/slash variants and pages Wayback never saved. Start with the paid route for one competitor; use the free route only for path-level digging. Most linkers to dead pages were spam scrapers and forums: expect to keep about 1 in 8.
