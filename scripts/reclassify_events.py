"""Re-parse play_events classified as 'other' using expanded parser."""
from fsbb.db import init_db
from fsbb.parser import parse_play_text

conn = init_db()
others = conn.execute(
    "SELECT id, raw_text FROM play_events WHERE event_type = 'other'"
).fetchall()

reclassified = 0
counts = {}
batch = []
for event_id, raw_text in others:
    parsed = parse_play_text(raw_text)
    new_type = parsed["event_type"]
    if new_type != "other":
        batch.append((new_type, parsed["batter_name"], event_id))
        reclassified += 1
        counts[new_type] = counts.get(new_type, 0) + 1
        if len(batch) >= 5000:
            conn.executemany(
                "UPDATE play_events SET event_type=?, batter_name=? WHERE id=?",
                batch,
            )
            conn.commit()
            batch = []

if batch:
    conn.executemany(
        "UPDATE play_events SET event_type=?, batter_name=? WHERE id=?",
        batch,
    )
    conn.commit()

remaining = conn.execute(
    "SELECT COUNT(*) FROM play_events WHERE event_type = 'other'"
).fetchone()[0]
total = conn.execute("SELECT COUNT(*) FROM play_events").fetchone()[0]
print(f"Reclassified: {reclassified}")
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"Remaining 'other': {remaining} ({remaining/total*100:.1f}%)")
conn.close()
