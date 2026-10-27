# Moving Man

Find brands, tools and resources in the niche that rebranded, moved, or shut down, then reach the sites still linking to the old version.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md).

## Step 1. Find moved or closed resources

**Do:**
- news searches with the Moving Man footprints in [footprints.md](../footprints.md) ("rebrands as", "shutting down", "sunsetting", "has been acquired", "discontinued") plus niche keywords;
- earlier `blb.py outbound` runs: `review` rows (`redirect_offsite`) and `redirect_home` rows are often moved or acquired resources.

**Then:** `blb.py check --all OLD_URL [...]` shows where each old URL ends up today (`final_url`).

**Classify:**

| Outcome | Meaning | Pitch |
|---|---|---|
| dead (any dead reason) | closed | user's page as the replacement |
| redirects to the new brand, same content | moved | "it moved to X"; offer the user's page only as an alternative |
| redirects to an unrelated page or homepage | effectively gone | user's page as the replacement |

## Step 2. Get the sites still linking to the old version

**Do:** `blb.py backlinks OLD_DOMAIN_OR_URL --limit 200` (paid). Then `blb.py haslink URL_FROM [...] --domain OLD_DOMAIN` to confirm the old link is still on the page.

**Pass:** on-topic site, link still present, user has a page that fits.

## Step 3. Contact

As [broken-link-building.md](broken-link-building.md) step 5.

## Step 4. Draft

```
Subject: [Old name] link on your [topic] page

Hi [first name],

Your [page title] page links to [old name] ([old URL]). [It shut down in [month year]. / It now redirects to [where it goes].]

If you are updating the page, we have a [format] that covers the same ground: [URL].

Thanks for keeping the page useful.

[Sender name]
```

When the brand simply moved with the same content, say so honestly and offer the user's page as one option, not as the fix. One follow-up after about 7 days, then stop.

## Change log

- Best source of dead brands was the user's own discontinued-product pages. About 95% of backlinks to dead brand domains were link-selling spam and domain-report scrapers, so pass `--title` or filter titles before reading. `check` now flags parked for-sale pages as `parked` and 200 OK shutdown pages as `closed_notice`. Confirm the replacement page is still live (a review can itself have been redirected).
