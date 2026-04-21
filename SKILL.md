---
name: reddit-scraper
description: Pull Reddit content via public JSON endpoints. Scrapes user history (submissions + comments), subreddit feeds (new/hot/top/rising/controversial), or whole threads with every comment. No login, no browser, no Scrapling. Outputs JSON per target plus a flat CSV. Use for user research, voice-of-customer mining, community analysis, or building datasets for LLM fine-tuning.
trigger: /reddit-scrape
---

# /reddit-scrape

Scrape Reddit using `<url>.json` public endpoints. No auth. No Playwright. Just `requests` and JSON parsing. Very fast (hundreds of posts per minute) and low ban risk.

## Usage

```
/reddit-scrape user <username>                       # submissions + comments for one user
/reddit-scrape users u1,u2,u3                        # many users
/reddit-scrape subreddit <name>                      # subreddit feed (default sort=new)
/reddit-scrape subreddit <name> --sort top --max 1000
/reddit-scrape thread <url>                          # single thread with all comments
/reddit-scrape file targets.txt                      # mixed file (u/x, r/y, https://...)
/reddit-scrape csv                                   # flatten data/*.json to all.csv
```

Sort options for subreddits: `new`, `hot`, `top`, `rising`, `controversial`.
Max default is 500 items per target.

## What Claude must do when invoked

### Step 1 - Resolve

`SKILL_DIR` = directory holding this SKILL.md.
`WORKSPACE` defaults to `./reddit-scrape` in cwd (override with `--out-dir`).

### Step 2 - Ensure dependencies

```bash
python -c "import requests" 2>/dev/null || python -m pip install -q requests
```

That's it. No browser, no Scrapling, no Playwright.

### Step 3 - Route the subcommand

**`user <u>`** or **`users u1,u2,u3`:**
```bash
python "$SKILL_DIR/scrape.py" --user <u> --out-dir "$WORKSPACE" [--max 500]
python "$SKILL_DIR/scrape.py" --users "u1,u2,u3" --out-dir "$WORKSPACE"
```

**`subreddit <name>`:**
```bash
python "$SKILL_DIR/scrape.py" --subreddit <name> \
  --sort <new|hot|top|rising|controversial> --max 500 --out-dir "$WORKSPACE"
```

**`thread <url>`:**
```bash
python "$SKILL_DIR/scrape.py" --thread "<url>" --out-dir "$WORKSPACE"
```

**`file <path>`** - mixed targets, one per line. The script auto-detects:
- `u/<name>` or `/u/<name>` -> user scrape
- `r/<name>` or `/r/<name>` -> subreddit scrape (uses current --sort)
- `https://...` -> thread scrape
- Lines starting with `#` are ignored

```bash
python "$SKILL_DIR/scrape.py" --file "<path>" --sort new --max 500 --out-dir "$WORKSPACE"
```

**`csv`:**
```bash
python "$SKILL_DIR/to_csv.py" --data-dir "$WORKSPACE/data" --out "$WORKSPACE/all.csv"
```

The CSV handles all three shapes (user, subreddit, thread) and tags each row with a `kind` column (`submission` or `comment`).

### Step 4 - Summarize

Per target: count of submissions, comments, or posts. Flag any 404s (deleted user or subreddit).

## Notes

### Reddit's rate limits

Reddit's unauthenticated JSON endpoints allow about 60 requests per minute from a single IP. The scraper waits 1.5 seconds between requests (polite), so one run hits roughly 40/min. No authentication token needed.

If you hit 429, the scraper waits 5, 10, 15 seconds and retries. If you're still throttled after 3 tries it gives up on that page and moves on.

### Subreddit max is ~1000

Reddit's listing endpoints hard-cap at 1000 items via `after=` pagination, no matter what you pass to `--max`. For deeper history, use [pushshift](https://github.com/pushshift/api) or the official Reddit API via PRAW.

### Comment trees

For threads, the scraper flattens the nested comment tree into a flat list with `depth` and `parent_id` columns so you can reconstruct the thread. It skips "load more" placeholders (you'd need PRAW or a second fetch per placeholder to expand those).

### Legal

Reddit's content is CC-licensed user content. Reading it via the public JSON endpoint is explicitly supported ("add `.json` to any URL" is in their old docs). Reasonable personal research, LLM training, and analytics are fine. Don't redistribute user content as your own or build a Reddit clone.

For commercial bulk use, use the [official Reddit API via PRAW](https://praw.readthedocs.io/) with a registered app (free, 1000 requests/hour).

## Files

- `scrape.py` - hits Reddit's JSON endpoints with retry and pagination
- `to_csv.py` - flatten any mix of user/subreddit/thread exports to one CSV
