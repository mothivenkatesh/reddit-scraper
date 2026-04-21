"""
Flatten reddit-scraper JSON output into one CSV.

Handles all three shapes: user (submissions + comments), subreddit (posts),
thread (post + comments). Each row gets a `kind` column so you can filter.

Usage
-----
python to_csv.py
python to_csv.py --data-dir reddit-scrape/data --out reddit-scrape/all.csv
"""
import argparse
import csv
import json
from pathlib import Path

FIELDS = [
    "source_file", "kind", "subreddit",
    "id", "author", "title", "body",
    "score", "num_comments", "created_utc", "permalink",
    "url", "is_self", "flair", "depth", "parent_id",
]


def from_submission(sub):
    return {
        "kind": "submission",
        "subreddit": sub.get("subreddit"),
        "id": sub.get("id"),
        "author": sub.get("author"),
        "title": sub.get("title"),
        "body": sub.get("selftext"),
        "score": sub.get("score"),
        "num_comments": sub.get("num_comments"),
        "created_utc": sub.get("created_utc"),
        "permalink": sub.get("permalink"),
        "url": sub.get("url"),
        "is_self": sub.get("is_self"),
        "flair": sub.get("link_flair_text"),
    }


def from_comment(c, subreddit=None):
    return {
        "kind": "comment",
        "subreddit": subreddit or c.get("subreddit"),
        "id": c.get("id"),
        "author": c.get("author"),
        "title": "",
        "body": c.get("body"),
        "score": c.get("score"),
        "created_utc": c.get("created_utc"),
        "permalink": c.get("permalink"),
        "depth": c.get("depth"),
        "parent_id": c.get("parent_id"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="reddit-scrape/data")
    ap.add_argument("--out", default="reddit-scrape/all.csv")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = 0
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for jf in sorted(data_dir.glob("*.json")):
            data = json.loads(jf.read_text(encoding="utf-8"))
            src = jf.name

            # user export
            if "submissions" in data or "comments" in data:
                for sub in data.get("submissions", []):
                    w.writerow({"source_file": src, **from_submission(sub)})
                    rows += 1
                for c in data.get("comments", []):
                    w.writerow({"source_file": src, **from_comment(c)})
                    rows += 1
                continue

            # subreddit export
            if "posts" in data:
                for sub in data["posts"]:
                    w.writerow({"source_file": src, **from_submission(sub)})
                    rows += 1
                continue

            # thread export
            if "post" in data and "comments" in data:
                w.writerow({"source_file": src, **from_submission(data["post"])})
                rows += 1
                sub = data["post"].get("subreddit")
                for c in data["comments"]:
                    w.writerow({"source_file": src, **from_comment(c, sub)})
                    rows += 1
                continue

    print(f"{rows} rows -> {out}")


if __name__ == "__main__":
    main()
