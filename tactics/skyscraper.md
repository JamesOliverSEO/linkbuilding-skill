# Skyscraper

Find a competitor's most-linked piece on a topic, make something clearly better, and pitch the sites that link to the original.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md). Thresholds are starting values to tune.

## Step 1. Find linkable pieces

**Do:**
- `blb.py toppages COMPETITOR --min-rd 20 --limit 50` (paid) for each competitor: their most-linked live pages;
- or search the topic, take the top 10 results and run `blb.py refdomains URL [...]` on them in one batch (paid, cheap).

**Pass:** 20 or more referring domains, on a topic the user's site can credibly own, and not a homepage, tool login or brand page (people link to those for the brand, not the content).

## Step 2. Work out why it gets links

**Do:** read the piece. Name what the linking sites cite it for: original data or statistics, a definition, a tool or calculator, a template, a list of examples, a guide. Sample 10 linking pages from step 4 to confirm what they quote.

## Step 3. Decide whether the user can beat it

**Pass only when the user can make it clearly better on what gets cited:**
- **More current:** the original's data or examples are 2 or more years old;
- **More complete:** it misses sections the linkers need;
- **Original data:** the user can add data nobody else has;
- **Easier to use:** a tool, template or visual where the original is text.

**Fail:** "a bit longer" or "better designed" alone. If the user cannot beat it on the cited thing, stop and say why.

**Output:** a brief for the new piece (angle, sections, the specific improvements, the stats to replace). Writing it is a separate job (use your usual writing process).

## Step 4. Get the linkers

**Do (once the user's piece is live):** `blb.py backlinks ORIGINAL_URL --limit 300` (paid).

**Pass:** `dofollow = True`, on-topic site, the link sits in the body of an article (not a sitewide list), and `haslink` confirms it is still there. Linkers quoting an outdated stat that the new piece updates go to the top.

## Step 5. Draft

Under 120 words. Lead with what is new for **their** page, never ask them to remove the original.

```
Subject: Updated [topic] [data/guide] for your [page title]

Hi [first name],

Your [page title] cites [original page name] for [what they cite]. That [data/guide] is from [year], so I thought you'd want to know we just published [new piece name] with [the specific improvement, e.g. 2026 figures from X sources]: [URL]

If it is useful, it could make a good addition next time you update the page.

[Sender name]
```

One follow-up after about 7 days, then stop.
