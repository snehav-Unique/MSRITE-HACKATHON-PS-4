from flask import Blueprint, jsonify, request
from models import db, ContentItem
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/metrics")
def metrics():
    total = ContentItem.query.count()
    post_now = ContentItem.query.filter_by(decision="post_now").count()
    scheduled = ContentItem.query.filter_by(decision="schedule").count()
    # accuracy = % where decision matches score threshold (87)
    items = ContentItem.query.with_entities(ContentItem.decision, ContentItem.score).all()
    correct = sum(
        1 for d, s in items
        if (d == "post_now" and s >= 87) or (d == "schedule" and s < 87)
    )
    accuracy = round(correct / total * 100, 1) if total else 0
    return jsonify(total=total, post_now=post_now, scheduled=scheduled, accuracy=accuracy)


@dashboard_bp.route("/content")
def content():
    decision = request.args.get("decision", "")
    platform = request.args.get("platform", "")
    time_filter = request.args.get("time", "")
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)

    q = ContentItem.query
    if decision and decision != "All Decisions":
        q = q.filter_by(decision="post_now" if decision == "Post Now" else "schedule")
    if platform and platform != "All Platforms":
        q = q.filter_by(platform=platform)
    if search:
        q = q.filter(ContentItem.content_id.ilike(f"%{search}%"))
    if time_filter and time_filter != "All Time Slots":
        label_map = {"Morning": (6, 9), "Peak": (17, 22), "Late Night": (22, 24)}
        bounds = label_map.get(time_filter)
        if bounds:
            q = q.filter(ContentItem.time_slot >= bounds[0], ContentItem.time_slot < bounds[1])

    q = q.order_by(
        (ContentItem.decision == "post_now").desc(),
        ContentItem.score.desc()
    )
    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()

    def slot_label(h):
        if h < 6: return "Quiet"
        if h < 9: return "Morning"
        if h < 13: return "Mid"
        if h < 17: return "Afternoon"
        if h < 20: return "Peak"
        if h < 22: return "Evening"
        return "Late"

    return jsonify(
        items=[{
            "content_id": r.content_id,
            "platform": r.platform,
            "time_slot": f"{r.time_slot:02d}:00 ({slot_label(r.time_slot)})",
            "decision": "Post Now" if r.decision == "post_now" else "Schedule",
            "score": round(r.score, 1),
        } for r in rows],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@dashboard_bp.route("/distribution")
def distribution():
    post_now = ContentItem.query.filter_by(decision="post_now").count()
    scheduled = ContentItem.query.filter_by(decision="schedule").count()
    total = post_now + scheduled
    return jsonify(
        post_now=post_now,
        scheduled=scheduled,
        total=total,
        post_now_pct=round(post_now / total * 100, 1) if total else 0,
    )


@dashboard_bp.route("/hourly-density")
def hourly_density():
    rows = db.session.query(
        ContentItem.time_slot,
        ContentItem.platform,
        func.count(ContentItem.id).label("cnt"),
    ).group_by(ContentItem.time_slot, ContentItem.platform).all()

    hourly = {}
    for slot, plat, cnt in rows:
        hourly.setdefault(slot, {"Instagram": 0, "YouTube": 0})[plat] = cnt

    data = [
        {"hour": f"{h:02d}:00", "instagram": hourly[h].get("Instagram", 0), "youtube": hourly[h].get("YouTube", 0)}
        for h in sorted(hourly)
    ]
    return jsonify(data)
