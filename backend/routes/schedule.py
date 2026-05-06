from flask import Blueprint, jsonify, request
from models import db, ScheduleItem, ContentItem
from datetime import datetime, timedelta

schedule_bp = Blueprint("schedule", __name__)


def _item_dict(item):
    return {
        "id": item.id,
        "content_id": item.content_id,
        "platform": item.platform,
        "content_type": item.content_type,
        "time": item.scheduled_datetime.strftime("%H:%M"),
        "score": item.score,
        "status": item.status,
    }


@schedule_bp.route("/weekly")
def weekly():
    today = datetime.utcnow()
    week_offset = request.args.get("week_offset", 0, type=int)
    platform_filter = request.args.get("platform", "")

    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=7)

    q = ScheduleItem.query.filter(
        ScheduleItem.scheduled_datetime >= monday,
        ScheduleItem.scheduled_datetime < sunday,
    )
    if platform_filter and platform_filter != "All":
        q = q.filter(ScheduleItem.platform == platform_filter)

    items = q.order_by(ScheduleItem.scheduled_datetime).all()

    by_day = {i: [] for i in range(7)}
    for item in items:
        by_day[item.scheduled_datetime.weekday()].append(_item_dict(item))

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_numbers = [(monday + timedelta(days=i)).day for i in range(7)]
    # Only highlight today if we're on the current week
    today_idx = today.weekday() if week_offset == 0 else -1

    return jsonify(
        week_label=f"{monday.strftime('%b %d')} - {(monday + timedelta(days=6)).strftime('%b %d')}",
        day_names=day_names,
        day_numbers=day_numbers,
        today_idx=today_idx,
        schedule=by_day,
        week_offset=week_offset,
    )


@schedule_bp.route("/today")
def today_focus():
    today = datetime.utcnow()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today.replace(hour=23, minute=59, second=59)

    items = ScheduleItem.query.filter(
        ScheduleItem.scheduled_datetime >= start,
        ScheduleItem.scheduled_datetime <= end,
        ScheduleItem.status != "cancelled",
    ).order_by(ScheduleItem.score.desc()).limit(3).all()

    return jsonify([_item_dict(i) for i in items])


@schedule_bp.route("/queue")
def queue():
    # High-scoring unscheduled items
    already_scheduled = {s.content_id for s in ScheduleItem.query.all()}
    items = ContentItem.query.filter(
        ContentItem.score >= 70,
    ).order_by(ContentItem.score.desc()).limit(12).all()

    unscheduled = [i for i in items if i.content_id not in already_scheduled][:8]
    return jsonify([{
        "content_id": i.content_id,
        "platform": i.platform,
        "content_type": i.content_type,
        "score": round(i.score / 100, 2),
        "decision": "Post Now" if i.decision == "post_now" else "Schedule",
    } for i in unscheduled])


@schedule_bp.route("/add", methods=["POST"])
def add():
    data = request.get_json() or {}
    item = ScheduleItem(
        content_id=data.get("content_id"),
        platform=data.get("platform"),
        content_type=data.get("content_type", "Post"),
        score=float(data.get("score", 0)) * 100,
        scheduled_datetime=datetime.fromisoformat(data["scheduled_datetime"]),
        status="queued",
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(success=True, id=item.id), 201
