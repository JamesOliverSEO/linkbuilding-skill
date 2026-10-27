# "Best X" listicle inclusion

Get the user's product added to "best [category] tools" and "[competitor] alternatives" articles. For a product, these pages send buyers as well as links, so they come first for any SaaS.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md). Thresholds are starting values to tune.

## Step 1. Inputs

Ask for: the product, 2 or 3 category phrases buyers use ("rank tracker", "brand mention tool"), 3 to 5 competitors, and the one concrete thing the product does better or differently. No differentiator, no pitch.

## Step 2. Find the lists

**Do both:**
- **Search:** listicle footprints in [footprints.md](../footprints.md) for each category phrase and each competitor ("best [category]", "[competitor] alternatives", "[competitor] vs").
- **Competitor backlinks:** `blb.py backlinks COMPETITOR --limit 500 --title "best|top|alternative|vs|review" --out lists.csv` (paid). Lists that mention competitors almost always link to them.

## Step 3. Qualify

**Do:** `blb.py haslink LIST_PAGE [...] --domain USER_DOMAIN --brand "PRODUCT"`, then read each page.

**Pass when the list:**
- names 2 or more of the user's competitors and does not include the user (`links_to_domain = no`, `mentions_brand = no`);
- was published or updated in the last 2 years (lists get refreshed; a stale list still gets updated if the author is active);
- is editorial: written by a person who reviews tools.

**Flag, do not pitch:** lists run by a competitor (they will not add a rival), and lists that charge for inclusion or label entries as sponsored. Paid placement must be `rel="sponsored"` under Google's guidelines; that is the user's call.

**Already listed** (`mentions_brand = yes` and `links_to_domain = no`): hand off to [unlinked-mentions.md](unlinked-mentions.md) step 5.

## Step 4. Find the author

As [broken-link-building.md](broken-link-building.md) step 5. The byline author is the right contact here, not a general inbox.

## Step 5. Draft

Under 120 words. Make it easy to say yes: offer access and a ready blurb.

```
Subject: [Product] for your [list title]

Hi [first name],

I read your [list title] and liked how you [one specific thing about their review method]. I'd like to suggest [product] for the next update.

What it does differently: [the one concrete differentiator].

Happy to set you up with a free account so you can test it yourself: [link or "just reply"]. Here is a short description in case it helps:

"[2 sentence blurb, plain and factual]"

Thanks for considering it.

[Sender name]
```

**Rules:** never criticise the competitors on their list, never offer payment, no inflated claims. The blurb uses the brand's exact spelling. One follow-up after about 10 days (list updates are slower), then stop.
