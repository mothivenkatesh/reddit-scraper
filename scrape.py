"""
reddit-scraper: pull user history, subreddit posts, and thread + comments
via Reddit's free public JSON endpoints. No login, no browser.

Usage
-----
# User's posts + comments
python scrape.py --user spez
python scrape.py --users spez,kn0thing

# Subreddit feed
python scrape.py --subreddit indianstartups --sort new --max 500
python scrape.py --subreddit SaaS --sort top

# Full thread with comments
python scrape.py --thread https://www.reddit.com/r/SaaS/comments/abc123/title/

# From a file (one target per line; prefix u/ for user, r/ for subreddit,
# or full https URL for a thread)
python scrape.py --file targets.txt
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


UA = "reddit-scraper/1.0 by /u/anonymous (educational use)"
TIMEOUT = 30
POLITE_DELAY = 1.5  # seconds between requests; Reddit asks for ~1/sec


def get_json(url, params=None, retries=3):
    """GET a JSON endpoint with retry on 429/5xx."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA},
                             timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                wait = 5 * (attempt + 1)
                print(f"    {r.status_code}, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"    request error: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def paginate_listing(url, max_items, extra_params=None):
    """Walk a Reddit listing using the `after` cursor."""
    items = []
    after = None
    while len(items) < max_items:
        params = {"limit": 100, "raw_json": 1}
        if extra_params:
            params.update(extra_params)
        if after:
            params["after"] = after
        data = get_json(url, params=params)
        if not data or "data" not in data:
            break
        children = data["data"].get("children", [])
        if not children:
            break
        items.extend([c["data"] for c in children])
        after = data["data"].get("after")
        if not after:
            break
        time.sleep(POLITE_DELAY)
    return items[:max_items]


def scrape_user(username, max_items):
    username = username.strip().lstrip("u/").lstrip("/")
    print(f"user: {username}")
    base = f"https://www.reddit.com/user/{username}"
    result = {"user": username, "scraped_at": datetime.now(timezone.utc).isoformat()}

    print("  fetching submissions...")
    result["submissions"] = paginate_listing(f"{base}/submitted/.json", max_items)
    print(f"    {len(result['submissions'])} submissions")

    print("  fetching comments...")
    result["comments"] = paginate_listing(f"{base}/comments/.json", max_items)
    print(f"    {len(result['comments'])} comments")
    return result


def scrape_subreddit(name, sort, max_items):
    name = name.strip().lstrip("r/").lstrip("/")
    print(f"subreddit: r/{name} ({sort})")
    url = f"https://www.reddit.com/r/{name}/{sort}/.json"
    params = {"t": "all"} if sort == "top" else None
    posts = paginate_listing(url, max_items, extra_params=params)
    print(f"    {len(posts)} posts")
    return {
        "subreddit": name,
        "sort": sort,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(posts),
        "posts": posts,
    }


def flatten_comments(children, depth=0):
    """Recursively flatten the comment tree."""
    out = []
    for c in children:
        if c.get("kind") == "more":
            continue  # skip "load more" placeholders
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        out.append({
            "id": d.get("id"),
            "parent_id": d.get("parent_id"),
            "author": d.get("author"),
            "body": d.get("body"),
            "score": d.get("score"),
            "created_utc": d.get("created_utc"),
            "permalink": d.get("permalink"),
            "depth": depth,
        })
        replies = d.get("replies")
        if isinstance(replies, dict):
            out.extend(flatten_comments(
                replies.get("data", {}).get("children", []), depth + 1
            ))
    return out


def scrape_thread(url):
    url = url.rstrip("/")
    if not url.endswith(".json"):
        url = url + ".json"
    print(f"thread: {url}")
    data = get_json(url, params={"raw_json": 1, "limit": 500})
    if not data or len(data) < 2:
        print("    failed to load")
        return None
    post = data[0]["data"]["children"][0]["data"]
    comments = flatten_comments(data[1]["data"]["children"])
    print(f"    1 post + {len(comments)} comments")
    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "post": post,
        "comments": comments,
    }


def slug_from_thread_url(url):
    p = urlparse(url.rstrip("/"))
    parts = [x for x in p.path.split("/") if x]
    for i, x in enumerate(parts):
        if x == "comments" and i + 1 < len(parts):
            return parts[i + 1]
    return "thread"


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {path}")


def dispatch_target(target, args, data_dir):
    """Infer what a target is (user/subreddit/thread) and scrape it."""
    t = target.strip()
    if not t or t.startswith("#"):
        return
    if t.startswith("http"):
        result = scrape_thread(t)
        if result:
            write_json(data_dir / f"thread_{slug_from_thread_url(t)}.json", result)
    elif t.startswith("u/") or t.startswith("/u/"):
        user = t.lstrip("/").lstrip("u/")
        write_json(data_dir / f"u_{user}.json", scrape_user(user, args.max))
    elif t.startswith("r/") or t.startswith("/r/"):
        sub = t.lstrip("/").lstrip("r/")
        write_json(data_dir / f"r_{sub}_{args.sort}.json",
                   scrape_subreddit(sub, args.sort, args.max))
    else:
        print(f"  unknown target: {t} (use u/<name>, r/<name>, or a thread URL)")


def main():
    ap = argparse.ArgumentParser(description="Scrape Reddit via public JSON endpoints")
    ap.add_argument("--user", help="scrape one user (submissions + comments)")
    ap.add_argument("--users", help="comma-separated user list")
    ap.add_argument("--subreddit", help="scrape a subreddit feed")
    ap.add_argument("--thread", help="scrape a single thread URL (post + all comments)")
    ap.add_argument("--file", help="file of targets, one per line (u/... r/... or URLs)")
    ap.add_argument("--sort", default="new",
                    choices=["new", "hot", "top", "rising", "controversial"])
    ap.add_argument("--max", type=int, default=500,
                    help="max posts/comments per target [500]")
    ap.add_argument("--out-dir", default="reddit-scrape")
    args = ap.parse_args()

    workspace = Path(args.out_dir).resolve()
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output: {data_dir}")
    print()

    if args.user:
        write_json(data_dir / f"u_{args.user}.json",
                   scrape_user(args.user, args.max))
    if args.users:
        for u in args.users.split(","):
            dispatch_target(f"u/{u.strip()}", args, data_dir)
    if args.subreddit:
        sub = args.subreddit.lstrip("r/").lstrip("/")
        write_json(data_dir / f"r_{sub}_{args.sort}.json",
                   scrape_subreddit(sub, args.sort, args.max))
    if args.thread:
        result = scrape_thread(args.thread)
        if result:
            write_json(data_dir / f"thread_{slug_from_thread_url(args.thread)}.json", result)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            dispatch_target(line, args, data_dir)

    if not any([args.user, args.users, args.subreddit, args.thread, args.file]):
        ap.print_help()
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
