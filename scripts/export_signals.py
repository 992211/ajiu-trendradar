"""Export the newest TrendRadar SQLite snapshot as a small public JSON feed."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_LABELS = {"douyin": "抖音", "weibo": "微博"}


def main() -> None:
    source_root = Path(sys.argv[1])
    target = Path(sys.argv[2])
    databases = sorted((source_root / "news").glob("*.db"))
    if not databases:
        raise SystemExit("TrendRadar did not produce a news database")

    database = databases[-1]
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT title, platform_id, rank, url, mobile_url, last_crawl_time
        FROM news_items
        WHERE platform_id IN ('douyin', 'weibo')
        ORDER BY platform_id, rank ASC
        """
    ).fetchall()
    connection.close()

    grouped = {key: [] for key in SOURCE_LABELS}
    for row in rows:
        grouped[row["platform_id"]].append(
            {
                "title": row["title"],
                "rank": row["rank"],
                "url": row["mobile_url"] or row["url"],
                "captured_at": row["last_crawl_time"],
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "TrendRadar",
        "sources": [
            {"id": source_id, "label": label, "items": grouped[source_id]}
            for source_id, label in SOURCE_LABELS.items()
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
