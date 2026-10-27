# Link gap

Find sites that link to several competitors but not to the user, work out why they link, and route each one to the tactic whose pitch fits.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md). Thresholds are starting values to tune.

## Step 1. Pick competitors

**Do:** ask the user for 2 or 3 real competitors (same product category or same content topic). Never guess them.

**Pass:** each competitor competes for the same audience. A giant generalist site (Wikipedia, Forbes) is not a competitor.

## Step 2. Pull the gap

**Do:** `blb.py gap USER_DOMAIN COMP1 COMP2 [COMP3] --limit 200` (paid: show the estimate, wait for a yes, re-run with `--yes --out gap.csv`). It returns domains linking to **every** competitor listed and not to the user, highest rank first.

**Tip:** with 3 competitors the list is short and strong. If it comes back under 20 rows, drop to the 2 strongest competitors.

## Step 3. Filter

**Fail:** directories, spam (scraper or "stats" sites), forums, social sites, the competitors' own properties, and domains in a different language from the user's audience.

**Pass:** real editorial sites on topic.

## Step 4. Find the linking page and route it

**Do:** `blb.py backlinks COMP1 --limit 1000 --yes --out comp1-links.csv` (paid, one call per competitor) and join on `domain_from` to see which page on each gap domain links to the competitor. Read the page title and URL, open it when unsure.

**Route by page type:**

| The linking page is | Hand off to |
|---|---|
| a resource or links page | [resource-pages.md](resource-pages.md) step 3 |
| a "best X" or "alternatives" list | [listicle-inclusion.md](listicle-inclusion.md) step 3 |
| a guest post by the competitor | [guest-posts.md](guest-posts.md) step 2 |
| an article citing a competitor's guide or data | [skyscraper.md](skyscraper.md) step 5 (only when the user has a better piece) |
| a page where the competitor link is dead | [broken-link-building.md](broken-link-building.md) step 4 |
| news, partner or paid placement | skip, note why |

**Record:** one tracker row per gap page, `tactic = link-gap > [routed tactic]`.

## Change log

- A gap against one niche competitor plus two big generalist publishers returned about 90 domains, almost all directories, scrapers and spam, and none usable. Generalists are ruled out in step 1 for this reason. Use niche-only competitors, and when the niche has fewer than two, use page-level backlinks to the competitor's matching page instead of a domain gap.
