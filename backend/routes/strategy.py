from flask import Blueprint, jsonify, request
from models import db, StrategyConfig, ContentItem
from datetime import datetime

strategy_bp = Blueprint("strategy", __name__)


def _config_dict(cfg):
    return {
        "post_now_threshold": cfg.post_now_threshold,
        "sensitivity_boost_high": cfg.sensitivity_boost_high,
        "sensitivity_boost_medium": cfg.sensitivity_boost_medium,
        "max_daily_posts": cfg.max_daily_posts,
        "engine_cooling_mins": cfg.engine_cooling_mins,
        "prioritize_reels": cfg.prioritize_reels,
        "avoid_shorts_overlap": cfg.avoid_shorts_overlap,
        "cross_platform_sync": cfg.cross_platform_sync,
    }


@strategy_bp.route("/", methods=["GET"])
def get_strategy():
    cfg = StrategyConfig.query.first() or StrategyConfig()
    return jsonify(_config_dict(cfg))


@strategy_bp.route("/", methods=["PUT"])
def update_strategy():
    data = request.get_json() or {}
    cfg = StrategyConfig.query.first()
    if not cfg:
        cfg = StrategyConfig()
        db.session.add(cfg)

    float_fields = ["post_now_threshold", "sensitivity_boost_high", "sensitivity_boost_medium"]
    int_fields = ["max_daily_posts", "engine_cooling_mins"]
    bool_fields = ["prioritize_reels", "avoid_shorts_overlap", "cross_platform_sync"]

    for f in float_fields:
        if f in data:
            setattr(cfg, f, float(data[f]))
    for f in int_fields:
        if f in data:
            setattr(cfg, f, int(data[f]))
    for f in bool_fields:
        if f in data:
            setattr(cfg, f, bool(data[f]))

    cfg.updated_at = datetime.utcnow()
    db.session.commit()

    # Re-score all items with new threshold
    threshold_pct = cfg.post_now_threshold * 100
    for item in ContentItem.query.all():
        item.decision = "post_now" if item.score >= threshold_pct else "schedule"
    db.session.commit()

    return jsonify(success=True, config=_config_dict(cfg))


@strategy_bp.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json() or {}
    threshold = float(data.get("post_now_threshold", 0.87)) * 100
    items = ContentItem.query.all()
    results = []
    pn_count = 0
    for item in items:
        new_dec = "post_now" if item.score >= threshold else "schedule"
        if new_dec == "post_now":
            pn_count += 1
        results.append({
            "content_id": item.content_id,
            "score": item.score,
            "old_decision": item.decision,
            "new_decision": new_dec,
            "changed": item.decision != new_dec,
        })
    changed = sum(1 for r in results if r["changed"])
    return jsonify(
        summary={
            "total": len(items),
            "post_now": pn_count,
            "scheduled": len(items) - pn_count,
            "decisions_changed": changed,
        },
        preview=results[:20],
    )
