# Link reclamation

Recover links the user already earned: links pointing at pages that now 404, and links that were removed.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md).

## Step 1. Links to the user's broken pages (no outreach needed)

**Do:** `blb.py backlinks USER_DOMAIN --broken --limit 1000` (paid). Then `blb.py check` on every distinct `url_to` to confirm it is still broken today (DataForSEO's crawl can be weeks old).

**Fix on the user's site:** 301-redirect each confirmed dead target to the closest live page (same topic, not the homepage). List them for the user as `old URL -> new URL` pairs, sorted by how many domains link to the old URL. This needs no outreach and is the quickest win in the whole skill.

## Step 2. Lost links

**Do:** `blb.py backlinks USER_DOMAIN --lost --limit 500` (paid), then `blb.py haslink URL_FROM [...] --domain USER_DOMAIN` to confirm the link is really gone today.

**Pass for outreach when:**
- the linking page is still live (`haslink` did not return a fetch error);
- the page still covers the same topic (the link was edited out, not the page rewritten into something else);
- the user's target page still exists and is still the best fit.

**Skip:** pages that were deleted (nothing to restore), and links lost because the user's own page was removed (step 1 covers those).

## Step 3. Draft

Under 80 words, no blame.

```
Subject: Link on your [topic] page

Hi [first name],

Your [page title] page used to link to our [page name] ([URL]), and I noticed the link is no longer there. If it was removed by accident, would you consider adding it back? [If our page moved: it now lives at [new URL].]

No worries if it was a deliberate change.

[Sender name]
```

One follow-up after about 7 days, then stop.

## Step 4. Wrong URL variants

When `url_to` is an old slug or http version that redirects in a chain of 3 or more hops, or ends at the homepage, fix the redirect on the user's site first. Ask the linker to update the URL only when the redirect cannot be fixed.

## Change log

- About a third of the "lost" editorial links in one run were still live, or pointed at an old domain that still 301s. Run `haslink` against the current domain and every old domain before calling a link lost. A linker's typo in the URL is a 301 on the user's side, not an email.
