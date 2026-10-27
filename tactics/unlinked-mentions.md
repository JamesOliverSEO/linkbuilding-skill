# Unlinked brand mentions

Find pages that already name the user's brand or product without linking, and ask for the link. The warmest tactic: the writer already chose to mention the brand.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md).

## Step 1. Search for mentions

**Do:** search each variant with the unlinked-mentions footprints in [footprints.md](../footprints.md): brand name, product names, founder name, and common misspellings and spacing variants (for example "Acme Tools" and "AcmeTools"). Exclude the user's own domain and social profiles.

## Step 2. Confirm unlinked

**Do:** `blb.py haslink PAGE [PAGE ...] --domain USER_DOMAIN --brand "BRAND"`.

**Pass:** `mentions_brand = yes` and `links_to_domain = no`.

**Also worth a note:** `links_to_domain = yes` with `rel` containing nofollow is a link already. Leave it alone.

## Step 3. Filter

**Fail:** negative reviews or complaints, scraped or spun copies, forum posts, pages older than about 3 years with no sign of updates (low reply rate), and the user's own guest posts.

**Pass:** neutral or positive mentions on real sites.

## Step 4. Contact

As [broken-link-building.md](broken-link-building.md) step 5. Prefer the author of the page; `blb.py scan PAGE` lists published emails, contact page and socials.

## Step 5. Draft

Under 90 words, thank first, one ask.

```
Subject: Thanks for mentioning [brand]

Hi [first name],

Thanks for including [brand] in [page title]. [One specific line about what they said.]

Would you be open to linking the mention to [best page URL] so readers can find it? It is the page that covers [what the mention is about].

Thanks again either way.

[Sender name]
```

Pick the page that matches the mention (a feature mention links to that feature's page, not the homepage). One follow-up after about 7 days, then stop.

## Change log

- A brand made of common words found nothing in 9 searches: it was swamped by namesakes (organisations with similar names), and the search tool did not reliably honour exact quotes or `-site:`. Report such a result as inconclusive, not "none"; it needs a stronger search tool or a paid mentions source. Also search founder and author names and the brand plus product terms.
