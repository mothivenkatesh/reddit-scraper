# reddit-scraper

Pulls content off Reddit fast. Users (their posts and comments), subreddit feeds, or whole threads with every comment. No login, no browser, no Reddit account needed. Uses Reddit's own public JSON endpoints, so it's fast and low risk.

Built for non-developers. Two setup commands and you're running.

## What you can scrape

- **A user.** Everything they've posted and commented, up to 1000 of each.
- **A subreddit.** The feed (new, hot, top, rising, or controversial), up to 1000 posts.
- **A thread.** The original post plus every comment, with parent/child relationships preserved.
- **Any mix.** Give it a file with `u/someone`, `r/somecommunity`, and thread URLs all mixed together.

## What you can do with it

- **Research what your users complain about.** Scrape `r/ProductManagement` or your specific niche community, run the output through Claude, ask "what are the top 10 pain points people mention?"
- **Build an LLM fine-tuning dataset.** Comments and posts are good training data.
- **Audit a creator or expert.** Pull a user's entire history and see what they actually care about.
- **Track sentiment on a thread.** Full comment trees make this easy.
- **Monitor competitor mentions.** Scrape a subreddit feed once a week, diff the results.

## What you need first

1. **Python 3.10 or newer.** Check in Terminal (Mac) or PowerShell (Windows):
   ```
   python --version
   ```
   Install from [python.org](https://www.python.org/downloads/) if it's missing. On Windows, tick "Add Python to PATH".

2. That's it. No browser install. No Reddit account. No API keys.

## Step 1. Download this repo

Green **Code** button at the top, **Download ZIP**, unzip it. Or:

```
git clone https://github.com/mothivenkatesh/reddit-scraper.git
cd reddit-scraper
```

## Step 2. Install the one dependency

```
pip install -r requirements.txt
```

That's it. It only uses `requests` (a standard Python library).

## Step 3. Run it

### Scrape one user's full history

```
python scrape.py --user spez
```

Pulls their last 500 submissions and 500 comments. To get fewer or more, add `--max 100` or `--max 1000`.

### Scrape multiple users

```
python scrape.py --users spez,kn0thing,paulg
```

### Scrape a subreddit feed

```
python scrape.py --subreddit indianstartups --sort new --max 500
```

Sort options: `new`, `hot`, `top`, `rising`, `controversial`.

### Scrape a specific thread with all its comments

Copy the thread URL from Reddit:

```
python scrape.py --thread https://www.reddit.com/r/SaaS/comments/abc123/some-title/
```

You get the original post and every comment, flattened into a list. Each comment has a `depth` and `parent_id` so you can still see the conversation structure.

### Scrape a mixed batch from a file

Make `targets.txt` with one target per line. The scraper figures out what each one is from the prefix:

```
u/spez
u/naval
r/SaaS
r/ProductManagement
https://www.reddit.com/r/startups/comments/abc/title/
# Lines starting with # are ignored
```

Then:

```
python scrape.py --file targets.txt --sort new --max 500
```

## Step 4. Get a spreadsheet

After scraping:

```
python to_csv.py
```

Writes `reddit-scrape/all.csv`. One row per post or comment, with a `kind` column so you can filter. Columns for author, subreddit, title, body, score, timestamp, permalink, and thread depth for comments.

## Where everything goes

```
reddit-scrape/
  data/
    u_spez.json
    u_naval.json
    r_SaaS_new.json
    thread_abc123.json
  all.csv
```

Delete the folder to start clean.

## Limits worth knowing

- **Reddit caps listings at 1000 items.** Even if you say `--max 5000`, Reddit's pagination stops at 1000. To go deeper into a user's or subreddit's history, you'd need [Pushshift](https://github.com/pushshift/api) or the official Reddit API via [PRAW](https://praw.readthedocs.io/).

- **Rate limits.** Reddit allows about 60 requests per minute from a single IP, unauthenticated. The tool waits 1.5 seconds between requests (~40/min) to stay polite. If you hit a 429, it waits 5-15 seconds and retries. After three fails, it moves on.

- **"Load more" in long threads.** If a thread has hundreds of comments, Reddit collapses some into "load more" placeholders. The scraper currently skips these. To expand them, you'd need to follow them recursively (PRAW does this automatically).

## When it breaks

| You see | What happened | What to do |
|---------|---------------|------------|
| `404` for a user | Account deleted or banned | Normal. Move on. |
| `404` for a subreddit | Private, banned, or doesn't exist | Normal. Move on. |
| `429` repeating | Reddit is throttling you | Wait 10 minutes, run again |
| `ModuleNotFoundError: requests` | You skipped Step 2 | Re-run `pip install -r requirements.txt` |
| Fewer than 1000 items when you expected 1000 | You hit Reddit's real end, or a deleted account | Check the user's profile manually |

## For Claude Code users

Drop this folder into `~/.claude/skills/reddit-scraper/` and you get a slash command: `/reddit-scrape user spez`, `/reddit-scrape subreddit SaaS`, etc. See `SKILL.md` for details.

## Legal

Reddit content is user-generated and CC-licensed by default. Reading the public JSON feed is explicitly supported by Reddit (adding `.json` to any URL is documented behavior). Reasonable research, LLM training, and analytics are fine.

Don't redistribute user content as your own. Don't dump scraped data publicly with user handles attached. For commercial production use, use the [official Reddit API via PRAW](https://praw.readthedocs.io/) which gives you 1000 requests per hour with a free registered app.

## Why no Scrapling or Playwright?

Reddit's public JSON endpoints return structured data without login or anti-bot. Using a browser here would be 10x slower for zero benefit. This tool is deliberately lightweight.
