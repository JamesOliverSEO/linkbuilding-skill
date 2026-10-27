#!/usr/bin/env python3
"""Link building helpers. Standard library only.

Subcommands (free):
  outbound URL [URL ...]        external links on prospect pages, checked for dead ones
  check URL [URL ...]           check a list of URLs directly (dead / live / recheck / review)
  rdap DOMAIN [DOMAIN ...]      registration status and expiry from RDAP
  wayback URL [URL ...]         first and last good Wayback capture (rate limited)
  history DOMAIN                every URL Wayback has seen on a domain (find old pages)
  sitemap URL_OR_DOMAIN         URLs listed in a site's XML sitemaps
  haslink PAGE [...] --domain D does each page link to D (anchor, rel), and mention --brand
  scan PAGE [...]               qualify a prospect: contact routes, published emails,
                                write-for-us page, sponsored markers, CMS, socials

Subcommands (PAID, DataForSEO, print an estimate and need --yes):
  refdomains URL [URL ...]      referring domains per URL or domain
  backlinks TARGET [...]        linking pages, one per domain (--lost, --broken, --title)
  deadpages DOMAIN [...]        a domain's 4xx/5xx pages that still have referring domains
  toppages DOMAIN [...]         a domain's most-linked live pages
  gap YOU COMP [COMP ...]       domains linking to every competitor but not to YOU

Every subcommand also reads targets from --file (one per line, or a CSV with a
url / dead_url column) and writes CSV to stdout or --out.
"""

import argparse
import csv
import io
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
TIMEOUT = 15
READ_BYTES = 200_000

# Hosts that are never broken-link targets (share buttons, profiles).
SKIP_HOSTS = {"facebook.com", "twitter.com", "x.com", "linkedin.com", "pinterest.com",
              "instagram.com", "youtube.com", "youtu.be", "t.co", "wa.me", "tiktok.com",
              "reddit.com", "whatsapp.com", "google.com", "apple.com"}
SECOND_LEVEL = {"co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk", "com.au", "net.au", "org.au",
                "co.nz", "co.za", "com.br", "co.jp", "co.in", "com.mx", "com.sg", "com.tr"}

PARKED_MARKERS = ["domain is for sale", "buy this domain", "this domain may be for sale",
                  "domain for sale", "parked free", "parkingcrew", "sedoparking", "sedo.com",
                  "dan.com", "afternic", "hugedomains", "bodis.com", "above.com",
                  "this domain has expired", "domain has expired", "renew this domain",
                  "abovedomains", "forsale.min.js"]
# A brand that shut down but still serves a 200 page. Verdict review: read it by hand.
CLOSED_MARKERS = ["ceased trading", "no longer trading", "wrap up operations",
                  "bid farewell", "has closed its doors", "we have closed", "closing down sale",
                  "permanently closed", "we are closing"]
SOFT404_TITLE = re.compile(r"\b(404|not found|page not found|page cannot be found|"
                           r"no longer available|doesn.t exist)\b", re.I)

# Optional .env file holding DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD, used only when they
# are not already set in the environment.
DFS_ENV_DEFAULT = os.environ.get("DATAFORSEO_ENV_FILE", ".env")
# Observed in October 2026: refdomains 2 URLs $0.024072; backlinks, domain_pages and
# domain_intersection $0.0242 at 5 rows and $0.0244 at 10 rows. So about
# $0.024 per call + $0.00003 per URL or row. Estimates round up slightly.
DFS_CALL_COST = 0.025
DFS_URL_COST = 0.00005
DFS_BATCH = 1000
DFS_ROW_COST = 0.00005

SPONSORED_MARKERS = ["sponsored post", "sponsored content", "paid post", "advertorial",
                     "partner content", "in partnership with", "this post is sponsored"]
SOCIAL_HOSTS = ["twitter.com", "x.com", "linkedin.com", "facebook.com", "instagram.com",
                "youtube.com", "tiktok.com", "threads.net", "bsky.app", "mastodon.social"]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_SKIP = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".webp", "domain.com")


def reg_domain(host):
    host = (host or "").lower().split(":")[0].strip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def http_get(url, read=READ_BYTES):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        body = r.read(read)
        charset = r.headers.get_content_charset() or "utf-8"
        return r.status, r.geturl(), body.decode(charset, "replace")


WAYBACK_LINK = re.compile(r"^https?://web\.archive\.org/web/\d+[a-z_]*/(.+)$", re.I)


def resolves(host, tries=3):
    """True when DNS answers for host. Retries because lookups fail spuriously under load."""
    for i in range(tries):
        try:
            socket.getaddrinfo(host, 443)
            return True
        except socket.gaierror:
            time.sleep(2 * (i + 1))
    return False


def classify(url, _retried=False):
    """Return dict(url, verdict, reason, http_status, final_url).

    verdict: dead | live | recheck | review
    """
    out = {"url": url, "verdict": "", "reason": "", "http_status": "", "final_url": ""}
    m = WAYBACK_LINK.match(url)
    if m:
        # The site owner already swapped a dead link for an archive copy: the original is
        # dead and they maintain their links. Not fetched (archive.org rate limits hard).
        out.update(verdict="dead", reason="owner_archived", final_url=m.group(1))
        return out
    try:
        status, final, body = http_get(url)
    except urllib.error.HTTPError as e:
        out["http_status"] = e.code
        if e.code in (404, 410):
            out.update(verdict="dead", reason=f"http_{e.code}")
        elif e.code in (401, 403, 429, 503) or e.code >= 500:
            out.update(verdict="recheck", reason="blocked" if e.code < 500 else "server_error")
        else:
            out.update(verdict="recheck", reason=f"http_{e.code}")
        return out
    except urllib.error.URLError as e:
        r = e.reason
        if isinstance(r, socket.gaierror):
            # One failed lookup is not proof: parallel checks produced false dns_fail on
            # live sites. Only dead when DNS keeps failing on its own.
            host = urllib.parse.urlparse(url).hostname or ""
            if not _retried and resolves(host):
                return classify(url, _retried=True)
            if _retried:
                out.update(verdict="recheck", reason="dns_flaky")
            else:
                out.update(verdict="dead", reason="dns_fail")
        elif isinstance(r, (socket.timeout, TimeoutError)):
            out.update(verdict="recheck", reason="timeout")
        elif isinstance(r, ssl.SSLError):
            out.update(verdict="recheck", reason="ssl_error")
        elif isinstance(r, ConnectionRefusedError):
            out.update(verdict="dead", reason="connection_refused")
        else:
            out.update(verdict="recheck", reason=f"error:{type(r).__name__}")
        return out
    except (socket.timeout, TimeoutError):
        out.update(verdict="recheck", reason="timeout")
        return out
    except Exception as e:  # noqa: BLE001 - any other failure is a recheck, never a dead link
        out.update(verdict="recheck", reason=f"error:{type(e).__name__}")
        return out

    out["http_status"] = status
    out["final_url"] = final
    src, dst = urllib.parse.urlparse(url), urllib.parse.urlparse(final)
    low = body.lower()
    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    title = title.group(1).strip() if title else ""

    if any(m in low for m in PARKED_MARKERS):
        out.update(verdict="dead", reason="parked")
    elif src.path.strip("/") and not dst.path.strip("/") and not dst.query:
        out.update(verdict="dead", reason="redirect_home")
    elif SOFT404_TITLE.search(title):
        out.update(verdict="dead", reason="soft_404")
    elif reg_domain(src.hostname) != reg_domain(dst.hostname):
        out.update(verdict="review", reason="redirect_offsite")
    elif any(m in low for m in CLOSED_MARKERS):
        out.update(verdict="review", reason="closed_notice")
    else:
        out.update(verdict="live", reason="ok")
    return out


def check_many(urls, workers):
    """Classify URLs in parallel across hosts, one at a time per host with a 1s gap."""
    by_host = {}
    for u in urls:
        by_host.setdefault(urllib.parse.urlparse(u).hostname or "", []).append(u)
    results = {}

    def run_host(host_urls):
        for i, u in enumerate(host_urls):
            if i:
                time.sleep(1)
            results[u] = classify(u)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run_host, by_host.values()))
    return [results[u] for u in urls]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._cur = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            a = dict(attrs)
            if a.get("href"):
                self._cur = {"href": a["href"], "rel": a.get("rel") or "", "text": ""}

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._cur is not None:
            self._cur["text"] = " ".join(self._cur["text"].split())[:120]
            self.links.append(self._cur)
            self._cur = None


def outbound_links(page_url):
    _, final, body = http_get(page_url, read=3_000_000)
    p = LinkParser()
    p.feed(body)
    home = reg_domain(urllib.parse.urlparse(final).hostname)
    seen, out = set(), []
    for l in p.links:
        u = urllib.parse.urljoin(final, l["href"]).split("#")[0]
        pu = urllib.parse.urlparse(u)
        if (pu.hostname or "").endswith("safelinks.protection.outlook.com"):
            # Outlook-wrapped link: check the real target, not the wrapper.
            u = urllib.parse.parse_qs(pu.query).get("url", [u])[0].split("#")[0]
            pu = urllib.parse.urlparse(u)
        if pu.scheme not in ("http", "https"):
            continue
        d = reg_domain(pu.hostname)
        if d == home or d in SKIP_HOSTS or u in seen:
            continue
        seen.add(u)
        out.append({"url": u, "anchor": l["text"], "rel": l["rel"]})
    return out


def rdap(domain):
    domain = reg_domain(domain if "/" not in domain else urllib.parse.urlparse(domain).hostname)
    row = {"domain": domain, "domain_status": "", "registered": "", "expires": ""}
    try:
        req = urllib.request.Request(f"https://rdap.org/domain/{domain}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        row["domain_status"] = "unregistered" if e.code == 404 else f"rdap_http_{e.code}"
        return row
    except Exception as e:  # noqa: BLE001
        row["domain_status"] = f"rdap_error:{type(e).__name__}"
        return row
    ev = {e.get("eventAction"): e.get("eventDate", "")[:10] for e in d.get("events", [])}
    row["registered"], row["expires"] = ev.get("registration", ""), ev.get("expiration", "")
    st = " ".join(d.get("status", [])).lower()
    if "redemption" in st or "pending delete" in st:
        row["domain_status"] = "expiring"
    elif row["expires"] and row["expires"] < time.strftime("%Y-%m-%d"):
        row["domain_status"] = "expired"
    else:
        row["domain_status"] = "registered"
    return row


def _wb_get(url, tries=4, timeout=30):
    wait = 5
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tries - 1:
                time.sleep(wait)
                wait *= 3
                continue
            raise
        except (TimeoutError, socket.timeout):
            if i < tries - 1:
                time.sleep(wait)
                wait *= 3
                continue
            raise
    return ""


def wayback(url):
    row = {"url": url, "captures_ok": "", "first_ok": "", "last_ok": "", "last_ok_snapshot": ""}
    base = ("https://web.archive.org/cdx/search/cdx?output=json&filter=statuscode:200"
            "&fl=timestamp,original&url=" + urllib.parse.quote(url, safe=""))
    try:
        first = json.loads(_wb_get(base + "&limit=1") or "[]")
        time.sleep(1.5)
        last = json.loads(_wb_get(base + "&limit=-1") or "[]")
    except Exception as e:  # noqa: BLE001
        row["captures_ok"] = f"error:{type(e).__name__}"
        return row
    if len(first) < 2:
        row["captures_ok"] = "0"
        return row
    row["captures_ok"] = "yes"
    row["first_ok"] = first[1][0][:8]
    if len(last) >= 2:
        ts, orig = last[1]
        row["last_ok"] = ts[:8]
        row["last_ok_snapshot"] = f"https://web.archive.org/web/{ts}/{orig}"
    return row


def dfs_creds(env_path):
    login, pw = os.environ.get("DATAFORSEO_LOGIN"), os.environ.get("DATAFORSEO_PASSWORD")
    if not (login and pw) and os.path.exists(env_path):
        for line in open(env_path):
            k, _, v = line.strip().partition("=")
            if k == "DATAFORSEO_LOGIN":
                login = v.strip().strip('"')
            elif k == "DATAFORSEO_PASSWORD":
                pw = v.strip().strip('"')
    if not (login and pw):
        sys.exit("DataForSEO credentials not found. Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD "
                 f"in your environment or in {env_path} (see the README).")
    return login, pw


def refdomains(urls, env_path):
    login, pw = dfs_creds(env_path)
    auth = "Basic " + b64encode(f"{login}:{pw}".encode()).decode()
    rows, total = [], 0.0
    for i in range(0, len(urls), DFS_BATCH):
        batch = urls[i:i + DFS_BATCH]
        req = urllib.request.Request(
            "https://api.dataforseo.com/v3/backlinks/bulk_referring_domains/live",
            data=json.dumps([{"targets": batch}]).encode(),
            headers={"Authorization": auth, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as r:
            task = json.load(r)["tasks"][0]
        if task["status_code"] != 20000:
            sys.exit(f"DataForSEO error {task['status_code']}: {task['status_message']}")
        total += task.get("cost") or 0
        for res in task.get("result") or []:
            for it in res.get("items") or []:
                rows.append({"url": it["target"],
                             "ref_domains": it.get("referring_main_domains", 0),
                             "ref_domains_dofollow": (it.get("referring_main_domains", 0)
                                                      - it.get("referring_main_domains_nofollow", 0))})
    print(f"DataForSEO actual cost: ${total:.4f}", file=sys.stderr)
    return rows


def dfs_post(endpoint, payload, env_path):
    login, pw = dfs_creds(env_path)
    auth = "Basic " + b64encode(f"{login}:{pw}".encode()).decode()
    req = urllib.request.Request(
        f"https://api.dataforseo.com/v3/backlinks/{endpoint}/live",
        data=json.dumps([payload]).encode(),
        headers={"Authorization": auth, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        task = json.load(r)["tasks"][0]
    if task["status_code"] != 20000:
        sys.exit(f"DataForSEO error {task['status_code']}: {task['status_message']}")
    res = (task.get("result") or [{}])[0] or {}
    return res.get("items") or [], task.get("cost") or 0


def backlinks(target, limit, env_path, lost=False, broken=False, title=None):
    payload = {"target": target, "mode": "one_per_domain", "limit": limit,
               "order_by": ["domain_from_rank,desc"]}
    if lost:
        payload["backlinks_status_type"] = "lost"
    filters = []
    if title:
        # Filter on DataForSEO's side so --limit counts matching rows. "a|b" becomes OR'd likes.
        terms = [t.strip() for t in title.split("|") if t.strip()][:6]
        likes = []
        for t in terms:
            likes += [["page_from_title", "like", f"%{t}%"], "or"]
        filters.append(likes[:-1] if len(terms) > 1 else likes[0])
    if broken:
        filters.append(["is_broken", "=", True])
    if filters:
        payload["filters"] = filters[0] if len(filters) == 1 else [filters[0], "and", filters[1]]
    items, cost = dfs_post("backlinks", payload, env_path)
    rows = []
    for it in items:
        rows.append({"target": target, "url_from": it.get("url_from"),
                     "domain_from": it.get("domain_from"), "page_from_title": it.get("page_from_title"),
                     "anchor": it.get("anchor"), "dofollow": it.get("dofollow"),
                     "domain_from_rank": it.get("domain_from_rank"), "url_to": it.get("url_to"),
                     "url_to_status_code": it.get("url_to_status_code"), "is_lost": it.get("is_lost"),
                     "is_broken": it.get("is_broken"), "first_seen": (it.get("first_seen") or "")[:10],
                     "last_seen": (it.get("last_seen") or "")[:10]})
    return rows, cost


def domain_pages(domain, limit, env_path, dead, min_rd):
    if dead:
        filters = [["status_code", ">=", 400], "and",
                   ["page_summary.referring_main_domains", ">=", min_rd]]
    else:
        filters = [["status_code", "=", 200], "and",
                   ["page_summary.referring_main_domains", ">=", min_rd]]
    items, cost = dfs_post("domain_pages", {
        "target": domain, "limit": limit, "filters": filters,
        "order_by": ["page_summary.referring_main_domains,desc"]}, env_path)
    rows = [{"domain": domain, "page": it.get("page"), "status_code": it.get("status_code"),
             "title": (it.get("meta") or {}).get("title"),
             "ref_domains": (it.get("page_summary") or {}).get("referring_main_domains"),
             "dfs_crawled": (it.get("fetch_time") or "")[:10]} for it in items]
    return rows, cost


def gap(you, comps, limit, env_path):
    items, cost = dfs_post("domain_intersection", {
        "targets": {str(i + 1): c for i, c in enumerate(comps)},
        "exclude_targets": [you], "limit": limit,
        "order_by": ["1.rank,desc"]}, env_path)
    rows = []
    for it in items:
        di = it.get("domain_intersection") or {}
        first = di.get("1") or {}
        row = {"referring_domain": first.get("target"), "rank": first.get("rank")}
        for k, v in sorted(di.items()):
            row[f"backlinks_to_{comps[int(k) - 1]}"] = (v or {}).get("backlinks")
        rows.append(row)
    return rows, cost


def history(prefix, limit=2000):
    """Distinct URLs Wayback captured with a 200 under a domain or path prefix
    (example.com or example.com/blog). Big sites are slow: narrow with a path."""
    prefix = re.sub(r"^https?://", "", prefix).rstrip("/*")
    q = ("https://web.archive.org/cdx/search/cdx?output=json&collapse=urlkey"
         "&filter=statuscode:200&filter=mimetype:text/html&fl=original,timestamp"
         f"&limit={limit}&url={urllib.parse.quote(prefix)}/*")
    try:
        data = json.loads(_wb_get(q, tries=3, timeout=120) or "[]")
    except Exception as e:  # noqa: BLE001
        print(f"Wayback index failed for {prefix} ({type(e).__name__}); narrow it with a path, "
              f"e.g. {prefix}/blog", file=sys.stderr)
        return []
    return [{"url": u, "last_seen_ok": ts[:8]} for u, ts in data[1:]]


def sitemap(target, cap=50000):
    if not target.startswith("http"):
        target = "https://" + target
    p = urllib.parse.urlparse(target)
    root = f"{p.scheme}://{p.netloc}"
    queue = [target] if p.path.endswith(".xml") else []
    if not queue:
        try:
            _, _, robots = http_get(root + "/robots.txt")
            queue = re.findall(r"(?im)^sitemap:\s*(\S+)", robots)
        except Exception:  # noqa: BLE001
            pass
        queue = queue or [root + "/sitemap.xml"]
    rows, seen = [], set()
    while queue and len(rows) < cap:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            _, _, xml = http_get(sm, read=20_000_000)
        except Exception as e:  # noqa: BLE001
            print(f"could not fetch {sm}: {e}", file=sys.stderr)
            continue
        if "<sitemapindex" in xml:
            queue += re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)
            continue
        for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
            loc = re.search(r"<loc>\s*(.*?)\s*</loc>", block)
            mod = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", block)
            if loc:
                rows.append({"url": loc.group(1), "lastmod": mod.group(1)[:10] if mod else ""})
    return rows


def haslink(page, domain, brand=None):
    row = {"page": page, "links_to_domain": "", "anchor": "", "rel": "", "mentions_brand": ""}
    try:
        _, final, body = http_get(page, read=3_000_000)
    except Exception as e:  # noqa: BLE001
        row["links_to_domain"] = f"fetch_error:{type(e).__name__}"
        return row
    p = LinkParser()
    p.feed(body)
    want = reg_domain(domain)
    hits = [l for l in p.links
            if reg_domain(urllib.parse.urlparse(urllib.parse.urljoin(final, l["href"])).hostname) == want]
    row["links_to_domain"] = "yes" if hits else "no"
    if hits:
        row["anchor"] = " | ".join(dict.fromkeys(h["text"] for h in hits))[:200]
        row["rel"] = " | ".join(dict.fromkeys(h["rel"] or "follow" for h in hits))
    if brand:
        text = re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", body))
        row["mentions_brand"] = "yes" if re.search(re.escape(brand), text, re.I) else "no"
    return row


def scan(page):
    row = {"page": page, "emails": "", "contact_page": "", "about_page": "", "write_for_us": "",
           "sponsored_markers": "", "cms": "", "socials": "", "modified": ""}
    try:
        _, final, body = http_get(page, read=3_000_000)
    except Exception as e:  # noqa: BLE001
        row["emails"] = f"fetch_error:{type(e).__name__}"
        return row
    low = body.lower()
    p = LinkParser()
    p.feed(body)
    links = [(urllib.parse.urljoin(final, l["href"]), l["text"].lower()) for l in p.links]
    home = reg_domain(urllib.parse.urlparse(final).hostname)

    def first(pred):
        return next((u for u, t in links if pred(u.lower(), t)), "")

    row["contact_page"] = first(lambda u, t: "contact" in u or "contact" in t)
    row["about_page"] = first(lambda u, t: re.search(r"/about(-us)?/?$", u) or t in ("about", "about us"))
    row["write_for_us"] = first(lambda u, t: any(k in u or k in t for k in (
        "write-for-us", "write for us", "contribute", "guest-post", "guest post", "submit")))
    emails = {m.lower() for m in EMAIL_RE.findall(body) if not any(s in m.lower() for s in EMAIL_SKIP)}
    emails |= {u[7:].split("?")[0].lower() for u, _ in links if u.lower().startswith("mailto:")}
    row["emails"] = " | ".join(sorted(e for e in emails if "@" in e))
    row["sponsored_markers"] = " | ".join(m for m in SPONSORED_MARKERS if m in low)
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', body, re.I)
    row["cms"] = gen.group(1) if gen else ("WordPress" if "/wp-content/" in low else "")
    row["socials"] = " | ".join(sorted({u for u, _ in links if reg_domain(urllib.parse.urlparse(u).hostname)
                                        in SOCIAL_HOSTS and reg_domain(urllib.parse.urlparse(u).hostname) != home}))[:500]
    mod = re.search(r'(?:article:modified_time|dateModified)["\']?\s*(?:content=|:)\s*["\']([0-9-]{10})', body)
    row["modified"] = mod.group(1) if mod else ""
    return row


def read_targets(args):
    items = list(args.targets)
    if args.file:
        text = open(args.file).read()
        first = text.splitlines()[0] if text.strip() else ""
        if "," in first:
            for r in csv.DictReader(io.StringIO(text)):
                v = r.get("dead_url") or r.get("url") or r.get("domain")
                if v:
                    items.append(v.strip())
        else:
            items += [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return list(dict.fromkeys(items))


def write_csv(rows, path):
    if not rows:
        print("no rows", file=sys.stderr)
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    f = open(path, "w", newline="") if path else sys.stdout
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
    if path:
        f.close()
        print(f"wrote {len(rows)} rows to {path}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["outbound", "check", "rdap", "wayback", "history", "sitemap",
                                    "haslink", "scan", "refdomains", "backlinks", "deadpages",
                                    "toppages", "gap"])
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--out")
    ap.add_argument("--all", action="store_true", help="outbound/check: include live links too")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--yes", action="store_true", help="paid commands: confirm the call")
    ap.add_argument("--env", default=DFS_ENV_DEFAULT, help="paid commands: .env file with DataForSEO credentials")
    ap.add_argument("--limit", type=int, default=100, help="paid commands: max rows per target")
    ap.add_argument("--min-rd", type=int, default=3, help="deadpages/toppages: min referring domains")
    ap.add_argument("--lost", action="store_true", help="backlinks: lost links only")
    ap.add_argument("--broken", action="store_true", help="backlinks: links to broken pages only")
    ap.add_argument("--title", help="backlinks: keep linking pages whose title matches this regex")
    ap.add_argument("--domain", help="haslink: the domain to look for")
    ap.add_argument("--brand", help="haslink: brand name to look for in the page text")
    args = ap.parse_intermixed_args()
    targets = read_targets(args)
    if not targets:
        sys.exit("no targets")

    if args.cmd in ("backlinks", "deadpages", "toppages", "gap"):
        calls = 1 if args.cmd == "gap" else len(targets)
        if args.cmd == "gap" and len(targets) < 2:
            sys.exit("gap needs YOUR domain then at least one competitor")
        est = calls * (DFS_CALL_COST + args.limit * DFS_ROW_COST)
        print(f"{calls} call(s) at up to {args.limit} rows each, estimated cost up to ${est:.3f}",
              file=sys.stderr)
        if not args.yes:
            sys.exit("not run: re-run with --yes once the cost is approved")
        rows, total = [], 0.0
        if args.cmd == "gap":
            rows, total = gap(targets[0], targets[1:], args.limit, args.env)
        for t in ([] if args.cmd == "gap" else targets):
            if args.cmd == "backlinks":
                r, c = backlinks(t, args.limit, args.env, args.lost, args.broken, args.title)
            else:
                r, c = domain_pages(t, args.limit, args.env, args.cmd == "deadpages", args.min_rd)
            rows += r
            total += c
        print(f"DataForSEO actual cost: ${total:.4f}", file=sys.stderr)
    elif args.cmd == "history":
        rows = [r for t in targets for r in history(t, args.limit if args.limit != 100 else 2000)]
    elif args.cmd == "sitemap":
        rows = [r for t in targets for r in sitemap(t)]
    elif args.cmd == "haslink":
        if not args.domain:
            sys.exit("haslink needs --domain")
        rows = [haslink(t, args.domain, args.brand) for t in targets]
    elif args.cmd == "scan":
        rows = [scan(t) for t in targets]
    elif args.cmd == "refdomains":
        calls = -(-len(targets) // DFS_BATCH)
        est = calls * DFS_CALL_COST + len(targets) * DFS_URL_COST
        print(f"{len(targets)} URLs in {calls} call(s), estimated cost ${est:.3f}", file=sys.stderr)
        if not args.yes:
            sys.exit("not run: re-run with --yes once the cost is approved")
        rows = refdomains(targets, args.env)
        rows.sort(key=lambda r: -r["ref_domains"])
    elif args.cmd == "rdap":
        rows = [rdap(t) for t in targets]
    elif args.cmd == "wayback":
        rows = []
        for t in targets:
            rows.append(wayback(t))
            time.sleep(1.5)
    elif args.cmd == "check":
        rows = check_many(targets, args.workers)
        if not args.all:
            rows = [r for r in rows if r["verdict"] != "live"]
    else:
        rows = []
        for page in targets:
            try:
                links = outbound_links(page)
            except Exception as e:  # noqa: BLE001
                print(f"could not fetch {page}: {e}", file=sys.stderr)
                continue
            checked = check_many([l["url"] for l in links], args.workers)
            seen_dead = set()
            for l, c in zip(links, checked):
                if c["verdict"] == "live" and not args.all:
                    continue
                dead = c["final_url"] if c["reason"] == "owner_archived" else l["url"]
                if dead in seen_dead:
                    continue
                seen_dead.add(dead)
                rows.append({"prospect_page": page, "dead_url": dead, "anchor": l["anchor"],
                             "rel": l["rel"], "verdict": c["verdict"], "reason": c["reason"],
                             "http_status": c["http_status"], "final_url": c["final_url"]})
            print(f"{page}: {len(links)} external links checked", file=sys.stderr)
        # Domain-level dead links get an RDAP lookup: an expired domain is the top prospect.
        for r in rows:
            if r["reason"] in ("dns_fail", "parked", "connection_refused"):
                r["domain_status"] = rdap(r["dead_url"])["domain_status"]
    write_csv(rows, args.out)


if __name__ == "__main__":
    main()
