# Guest posts

Write an article for another site in the niche, with a link back in the author bio or where it genuinely helps the reader.

Tools, verdicts and house rules are in [SKILL.md](../SKILL.md). Thresholds are starting values to tune.

## Step 1. Find sites

**Do:** guest-post footprints in [footprints.md](../footprints.md) plus niche keywords. Link gap rows routed here are already qualified sites.

## Step 2. Qualify

**Do:** `blb.py scan SITE_PAGE` (finds the write-for-us page, sponsored markers, CMS). Then `blb.py refdomains SITE_DOMAIN` for site strength (paid, cheap in bulk: batch every candidate domain in one call).

**Pass when the site:**
- publishes guidelines or a contribution page;
- published posts by outside authors in the last 6 months;
- is on topic for the user's audience;
- has 50 or more referring domains;
- does **not** tag guest posts as sponsored or charge for them. Paid links break Google's guidelines; flag any fee and leave the decision to the user.

**Fail:** "write for us" pages on sites that publish anything (casino, CBD and loans next to the user's topic), sites where every post is a guest post.

## Step 3. Pitch ideas

**Do:** read the guidelines and 5 recent posts. Propose 3 topics that the site has not covered, that their audience wants, and where the user has real expertise. Check each idea with a site search (`site:theirdomain.com topic`) to make sure it is not a duplicate.

## Step 4. Draft

Follow their stated process exactly (form fields, word counts, subject line rules). When they ask for email:

```
Subject: Guest post idea: [best title]

Hi [first name],

I read your guidelines and your recent post on [recent post topic]. Here are three ideas I think your readers would get a lot from:

1. [Title]: [one line on the angle]
2. [Title]: [one line on the angle]
3. [Title]: [one line on the angle]

A bit about me: [one line of real credentials]. Examples of my writing: [1 or 2 URLs].

Happy to adjust any of these to fit your plans.

[Sender name]
```

**Record:** status moves to `pitched_topic`, then `accepted`, `written`, `published` in notes. Writing the post itself is a separate job (use your usual writing process).
