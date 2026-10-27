# Broken link building

Find dead links on relevant pages, then offer the site owner a working replacement from the user's site.

Tools and verdicts are in [SKILL.md](../SKILL.md). Every threshold here is a starting value to tune.

## Step 1. Find prospect pages

**Do:** search with the resource-page footprints in [footprints.md](../footprints.md), combined with the niche keywords. Start with about 10 queries; widen only if the first batch is thin. Collect the page URLs.

**Pass when the page:**
- links out to 10 or more external sites (resource lists, "best of" lists, guides);
- is on topic for the user's niche;
- is not the user's own site, a competitor, a forum thread, a directory that charges for listings, or a social profile.

**Fail:** link farms (hundreds of unrelated links), pages with no visible owner or contact route, and pages where every outbound link is nofollow sponsored.

**Record:** `prospect_page`, `prospect_domain`, `tactic = broken-link-building`, `status = found`.

## Step 2. Check outbound links

**Do:** `blb.py outbound PAGE [PAGE ...] --out dead.csv`. It pulls every external link with its anchor text, checks it, and keeps everything that is not live. Domain-level failures (`dns_fail`, `parked`, `connection_refused`) get an RDAP lookup automatically.

**Pass:** verdict `dead`.

**Hold:** `recheck` rows. Re-run `blb.py check --file` on them a day later. A row still failing on a second run with `timeout` or `server_error` can be treated as dead; `blocked` stays recheck (it is usually bot protection, not a dead page).

**Look by hand:** `review` rows (offsite redirects). Dead when the new site is unrelated; skip when the brand moved to a new domain.

**Expired-domain branch:** when `domain_status` is `unregistered` or `expired`, mark the row priority. The whole site is gone, so every page linking to it is a prospect. Tell the user: a domain with strong referring domains may also be worth registering (that is their call, not part of this tactic).

**Record:** `dead_url`, `dead_reason`, `anchor`, `domain_status`.

## Step 3. Judge the dead link's value

**Do:** `blb.py refdomains --file dead.csv` first (prints the estimate). Show the estimate, wait for a yes, then re-run with `--yes --out refs.csv`.

**Pass:** 3 or more referring domains (`ref_domains`) on the dead URL. A dead page that other sites linked to proves the content was wanted, and every one of those linking pages is an extra prospect for the same pitch.

**Still allowed below the threshold:** a dead link on a strong, on-topic prospect page, when the user has an obvious replacement. Mark it `low_value` in notes.

**Sort:** by `ref_domains`, highest first. Expired-domain rows go to the top.

**Record:** `ref_domains`.

## Step 4. Match a replacement

**Do:** `blb.py wayback DEAD_URL` for the last good snapshot, then open and read that snapshot. Note what the dead page covered: its topic, format and the key points the linking page relied on. Compare against the user's candidate pages.

**Pass when a user page:**
- covers the same topic and serves the same purpose for the reader (a guide replaces a guide, a tool replaces a tool);
- is at least as complete as the dead page.

**No match:** mark `needs_content` in notes and list the topic. When several high-value dead URLs share a topic, suggest the user writes one page that replaces them all. Never pitch a page that does not substitute for the dead one.

**No Wayback copy:** judge from the anchor text and the linking page's context, and say so in notes.

**Record:** `wayback_last_ok`, `wayback_snapshot`, `replacement_page`.

## Step 5. Find a contact

**Do:** look on the prospect page for an author byline, then the site's contact, about and team pages.

**Pass:** a named person's published email, or the site's contact form.

**Fail:** no contact route found. Mark `no_contact` and stop for that row. Never guess an address pattern, never use a paid email finder.

**Record:** `contact_name`, `contact_email_or_form`, `contact_source` (the page where it was found).

## Step 6. Draft the outreach

**Do:** draft one email per prospect page (not per dead link; group a page's dead links in one email). Use the variant that fits. Fill every bracket from the row; never send a bracket.

**Rules:**
- under 120 words;
- the broken link comes first, the user's page second;
- name the exact page and the exact dead link so they can find it fast;
- when the page has other dead links with no replacement from the user, list them too (it is a free favour and builds trust);
- no em dashes or en dashes;
- subject lines are plain, not clever.

### Variant A: the user has an existing page

```
Subject: Broken link on your [topic] page

Hi [first name],

I was reading your [page title] page and noticed the link to [dead page name] ([dead URL]) no longer works. [It returns a 404. / The site has gone offline.]

If you want a replacement, we have a [format] on [topic] that covers [the thing the dead page covered]: [replacement URL]

[Also broken on the same page: [other dead URL].]

Either way, thanks for keeping the list going.

[Sender name]
```

### Variant B: the user wrote a new page to replace it

```
Subject: [Dead page name] link on your [topic] page

Hi [first name],

Your [page title] page links to [dead page name] ([dead URL]), which has gone offline.

It was a useful [format], so we put together an updated version covering [the main points]: [replacement URL]

Happy for you to use it if it helps.

[Sender name]
```

### Follow-up (once, about 7 days later, then stop)

```
Subject: Re: [original subject]

Hi [first name], just bumping this in case it got buried. The [dead page name] link on [page title] is still broken. No worries if you have already sorted it.

[Sender name]
```

**Record:** `status = drafted`. The user sends and then updates `status`, `first_sent` and `followed_up`. After the follow-up with no reply, set `no_reply`.

## Improving this tactic

After each run, note what wasted time or produced replies (a footprint that only found link farms, a reason code that misfired, a subject line that got answers) and update this file or [footprints.md](../footprints.md). Keep the change small and say why in a one-line note at the bottom.

## Change log

- First version.
- DataForSEO cost corrected from real calls: about 2.4 cents per call plus 0.003 cents per URL.
- For a product-review site, health and academic "useful links" pages mostly had dead links to official bodies a review site cannot replace. Consumer pages worked better (moving checklists, home and renovation resources, travel, student accommodation, nursery setup).
- `outbound` gave false `dns_fail` under parallel load; fixed with a DNS retry (`dns_flaky`). Outlook safelinks are now unwrapped.
