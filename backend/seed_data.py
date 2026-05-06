"""
Reads the real CSV data from data/raw/, runs the optimizer logic,
and populates the SQLite database.
"""
import os
import csv
from datetime import datetime, timedelta

from models import db, ContentItem, ScheduleItem, StrategyConfig, AppSettings

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

POST_NOW_THRESHOLD = 0.87
DEFAULT_ACTIVITY = 0.5
DEFAULT_HISTORY = 0.5


def _load_csv(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _build_lookups():
    content = {r["content_id"]: r for r in _load_csv("content.csv")}
    creators = {r["creator_id"]: r for r in _load_csv("creators.csv")}

    history = {}
    for r in _load_csv("historical_engagement.csv"):
        key = (r["creator_id"], r["platform"], r["content_type"], r["time_slot"])
        history[key] = float(r["avg_engagement"])

    platform_activity = {}
    for r in _load_csv("platform_activity.csv"):
        platform_activity[(r["platform"], r["time_slot"])] = float(r["activity_score"])

    creator_platforms = {}
    for (cid, plat, *_) in history:
        creator_platforms.setdefault(cid, set()).add(plat)

    return content, creators, history, platform_activity, creator_platforms


def _base_score(creator):
    if creator is None:
        return 0.5
    return min(float(creator["base_engagement"]) / 2.0, 1.0)


def _activity(platform, slot, pa):
    v = pa.get((platform, str(slot)))
    return float(v) if v is not None else DEFAULT_ACTIVITY


def _history(cid, platform, ctype, slot, hist):
    v = hist.get((str(cid), platform, ctype, str(slot)))
    return float(v) if v is not None else DEFAULT_HISTORY


def _find_best_slot(cid, ctype, cp, hist, pa):
    best_p, best_s, best_v = "Instagram", 12, -1.0
    for platform in cp.get(str(cid), {"Instagram", "YouTube"}):
        for hour in range(24):
            v = _activity(platform, hour, pa) * _history(cid, platform, ctype, hour, hist)
            if v > best_v:
                best_v, best_p, best_s = v, platform, hour
    return best_p, best_s


def _compute(cid, row, creators, hist, pa, cp, config_threshold=POST_NOW_THRESHOLD,
             boost_high=1.3, boost_medium=1.15):
    creator = creators.get(str(row["creator_id"]))
    ctype = row["content_type"]
    sensitivity = row["time_sensitivity"].strip().lower()
    best_p, best_s = _find_best_slot(row["creator_id"], ctype, cp, hist, pa)
    b = _base_score(creator)
    a = _activity(best_p, best_s, pa)
    h = _history(row["creator_id"], best_p, ctype, best_s, hist)
    score = round(b * a * h, 4)
    if sensitivity == "high":
        score = min(score * boost_high, 1.0)
    elif sensitivity == "medium":
        score = min(score * boost_medium, 1.0)
    decision = "post_now" if score >= config_threshold else "schedule"
    return best_p, best_s, score, decision, b, a, h


def _slot_label(hour):
    if hour < 6:
        return "Quiet"
    if hour < 9:
        return "Morning"
    if hour < 13:
        return "Mid"
    if hour < 17:
        return "Afternoon"
    if hour < 20:
        return "Peak"
    if hour < 22:
        return "Evening"
    return "Late"


def seed_database():
    if ContentItem.query.count() > 0:
        return

    content, creators, hist, pa, cp = _build_lookups()

    # Strategy config
    cfg = StrategyConfig()
    db.session.add(cfg)

    # Settings defaults
    defaults = [
        ("auto_apply_strategy", "true"),
        ("smart_notifications", "false"),
        ("weekly_reports", "true"),
        ("ui_density", "Balanced"),
        ("high_contrast", "false"),
        ("webhook_url", "https://hooks.optimetic.io/v1/alpha-creator-77"),
        ("openai_api_key", "sk-placeholder"),
    ]
    for k, v in defaults:
        db.session.add(AppSettings(key=k, value=v))

    # Content items from real CSV
    items_for_schedule = []
    for cid, row in content.items():
        platform, slot, score, decision, b, a, h = _compute(
            cid, row, creators, hist, pa, cp
        )
        item = ContentItem(
            content_id=f"#{int(cid):04d}",
            creator_id=row["creator_id"],
            content_type=row["content_type"],
            time_sensitivity=row["time_sensitivity"].strip().lower(),
            platform=platform,
            time_slot=slot,
            decision=decision,
            score=round(score * 100, 2),
            base_eng=round(b, 4),
            activity_sc=round(a, 4),
            history_sc=round(h, 4),
        )
        db.session.add(item)
        items_for_schedule.append(item)

    # Seed schedule items spread across the current week
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())

    scheduled_so_far = 0
    for item in sorted(items_for_schedule, key=lambda x: x.score, reverse=True):
        if scheduled_so_far >= 12:
            break
        day_offset = scheduled_so_far % 7
        sched_dt = monday + timedelta(days=day_offset, hours=item.time_slot, minutes=0)
        status = "posted" if day_offset < today.weekday() else "queued"
        db.session.add(ScheduleItem(
            content_id=item.content_id,
            platform=item.platform,
            content_type=item.content_type,
            score=item.score,
            scheduled_datetime=sched_dt,
            status=status,
        ))
        scheduled_so_far += 1

    db.session.commit()
    print(f"[seed] Seeded {len(content)} content items.")
