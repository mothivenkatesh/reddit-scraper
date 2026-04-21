<div align="center">

# reddit-scraper

**Pull users, subreddits, and full threads from Reddit. No login, no browser, no API key. Just `pip install requests`.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/mothivenkatesh/reddit-scraper?style=social)](https://github.com/mothivenkatesh/reddit-scraper/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/mothivenkatesh/reddit-scraper)](https://github.com/mothivenkatesh/reddit-scraper/commits)
[![Issues](https://img.shields.io/github/issues/mothivenkatesh/reddit-scraper)](https://github.com/mothivenkatesh/reddit-scraper/issues)

**[Quickstart](#quickstart) · [Use cases](#what-you-can-do-with-it) · [Output](#sample-output) · [Compare](#how-it-compares) · [FAQ](#faq)**

**The lightest scraper in this set. 40 lines of setup, 10x the speed of browser-based tools.**

**If this saves you time, give it a star.**

</div>

---

## Why this exists

Most Reddit scrapers on GitHub are bloated. They spin up Playwright, require a Reddit dev account, wrap PRAW with 1000 lines of code. Reddit itself lets you add `.json` to any URL and returns structured data. So that's what this uses.

No browser. No login. No API key. Just `requests`.

## Quickstart

```bash
git clone https://github.com/mothivenkatesh/reddit-scraper.git
cd reddit-scraper
pip install -r requirements.txt

python scrape.py --user spez
python to_csv.py
```

30 seconds to first result. No account ceremony.

## What you can do with it

| Use case | What to run | What you get |
|---|---|---|
| **Audit what an expert actually thinks** | `python scrape.py --user paulg` | Every post and comment they've made, up to 1000 each |
| **Voice-of-audience for a niche** | `python scrape.py --subreddit ProductManagement --sort top --max 1000` | Top posts in a community, sortable by score |
| **Map a full thread discussion** | `python scrape.py --thread <URL>` | Post + every comment, with parent/child threading preserved |
| **Build an LLM fine-tuning dataset** | `python scrape.py --file targets.txt --max 1000` | Thousands of real posts and comments |
| **Monitor competitor mentions** | Re-run weekly, diff the CSVs | New posts that reference a competitor |
| **Theme extraction at scale** | Scrape + feed to Claude | "Top 10 complaints in r/SaaS last month" |
| **Track sentiment on a launch** | Scrape the launch thread | Full comment tree to run sentiment on |

## Sample output

```json
{
  "user": "spez",
  "scraped_at": "2026-04-22T08:15:00Z",
  "submissions": [
    {
      "id": "abc123",
      "title": "An update on our API changes",
      "selftext": "Last month we announced...",
      "subreddit": "reddit",
      "score": 1247,
      "num_comments": 892,
      "created_utc": 1713782400,
      "permalink": "/r/reddit/comments/abc123/...",
      "url": "https://reddit.com/r/reddit/comments/abc123/..."
    }
  ],
  "comments": [
    {
      "id": "def456",
      "parent_id": "t1_xyz789",
      "author": "spez",
      "body": "Thanks for the feedback...",
      "score": 42,
      "created_utc": 1713785000,
      "permalink": "...",
      "depth": 2
    }
  ]
}
```

## How it compares

|  | reddit-scraper | PRAW | PushShift | Browser scraper |
|---|---|---|---|---|
| Needs Reddit dev account | No | Yes | No | No |
| Needs API keys | No | Yes | No | No |
| Install in 1 command | Yes | Yes | Yes | No |
| Installs a browser | No | No | No | Yes |
| Speed | Fast | Fast | Fast | Slow |
| Max items per listing | 1000 (Reddit cap) | 1000 (same cap) | Unlimited (archive) | 1000 |
| Deep history (pre-2020) | No | No | Yes | No |
| Gets "load more" collapsed comments | No | Yes | No | Sometimes |
| Best for | Fast research | Production apps | Historical research | Nothing, use this instead |

## Who this is for

- **Product managers** mining user research from community forums
- **Content strategists** finding what a niche actually talks about
- **Founders** validating ICP language before writing copy
- **Researchers** building corpora for sentiment, classification, topic modeling
- **Growth operators** tracking competitor or category conversation

## Setup walkthrough (for non-developers)

### 1. Python

```
python --version
```

Install 3.10+ from [python.org](https://www.python.org/downloads/) if missing. On Windows, tick "Add Python to PATH".

### 2. Install

```
git clone https://github.com/mothivenkatesh/reddit-scraper.git
cd reddit-scraper
pip install -r requirements.txt
```

Only dependency is `requests`. No browser engine, no Playwright.

### 3. Run it

**One user's full history:**
```
python scrape.py --user spez
```

**Multiple users:**
```
python scrape.py --users spez,kn0thing,paulg
```

**Subreddit feed** (sort options: `new`, `hot`, `top`, `rising`, `controversial`):
```
python scrape.py --subreddit ProductManagement --sort top --max 1000
```

**Single thread with full comment tree:**
```
python scrape.py --thread https://www.reddit.com/r/SaaS/comments/abc123/title/
```

**Mixed batch from a file** - the tool auto-detects each target type by prefix:
```
u/spez
u/naval
r/SaaS
r/ProductManagement
https://www.reddit.com/r/startups/comments/abc/title/
```

```
python scrape.py --file targets.txt --sort new --max 500
```

### 4. Flatten to a spreadsheet

```
python to_csv.py
```

Writes `reddit-scrape/all.csv`. Each row has a `kind` column (`submission` or `comment`) so you can filter. Comments carry `depth` and `parent_id` so you can reconstruct thread structure.

## Where everything lands

```
reddit-scrape/
  data/
    u_spez.json
    u_naval.json
    r_SaaS_new.json
    thread_abc123.json
  all.csv
```

## Limits worth knowing

- **Reddit caps listings at 1000 items.** Hard limit for `after=` pagination. For deeper history use Pushshift.
- **~60 requests/minute** from a single unauthenticated IP. The tool waits 1.5 seconds between requests (~40/min) to stay polite.
- **"Load more" placeholders** in long threads are skipped. To expand them you'd need PRAW.
- **Deleted users and subreddits** return 404. The tool logs and moves on.

## FAQ

**Do I need a Reddit account?**  
No. The public JSON endpoints work unauthenticated.

**Is this legal?**  
Reading Reddit's public JSON is explicitly supported behavior (their own docs mention adding `.json` to any URL). Content is user-generated and CC-licensed by default. Don't redistribute user handles in a creepy way. For commercial scale use PRAW with a registered app.

**Why no PRAW?**  
PRAW is great for production apps but requires a Reddit developer account with OAuth credentials. That's overkill for a quick research scrape. This tool is for the 90% of cases where you just want the data fast.

**Can I get more than 1000 items per user?**  
No. Reddit's own pagination stops there. For deeper history use [Pushshift](https://github.com/pushshift/api).

**Does it get comments from inside `more` placeholders?**  
No. Reddit collapses some comments into "load more" links that require individual requests to expand. If you need complete comment trees, PRAW does this automatically.

**Can I run this on a schedule?**  
Yes. Cron (Mac/Linux) or Task Scheduler (Windows). Pair with a diff tool to spot new posts.

**Does it work for NSFW subreddits?**  
Yes, same endpoint. Reddit's unauthenticated API doesn't filter NSFW by default.

## For Claude Code users

Drop this folder into `~/.claude/skills/reddit-scraper/`. You get `/reddit-scrape user <u>`, `/reddit-scrape subreddit <name>`, `/reddit-scrape thread <url>`. See `SKILL.md`.

## Related projects

- [twitter-scraper](https://github.com/mothivenkatesh/twitter-scraper) - same spirit, for X/Twitter
- [review-scraper](https://github.com/mothivenkatesh/review-scraper) - G2 product reviews and Clutch agency reviews

## License

[MIT](LICENSE). Use it, fork it, ship it.

---

<div align="center">

**If this saved you time, star the repo. It genuinely helps.**

[Report a bug](https://github.com/mothivenkatesh/reddit-scraper/issues) · [Request a feature](https://github.com/mothivenkatesh/reddit-scraper/issues) · [Follow me on X](https://x.com/mothivenkatesh)

</div>
