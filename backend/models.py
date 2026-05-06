from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ContentItem(db.Model):
    __tablename__ = "content_items"
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.String(20), unique=True, nullable=False)
    creator_id = db.Column(db.String(10))
    content_type = db.Column(db.String(20))        # SHORT / LONG
    time_sensitivity = db.Column(db.String(20))    # low / medium / high
    platform = db.Column(db.String(20))            # Instagram / YouTube
    time_slot = db.Column(db.Integer)              # 0-23
    decision = db.Column(db.String(20))            # post_now / schedule
    score = db.Column(db.Float)
    base_eng = db.Column(db.Float)
    activity_sc = db.Column(db.Float)
    history_sc = db.Column(db.Float)
    status = db.Column(db.String(20), default="pending")  # pending / posted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScheduleItem(db.Model):
    __tablename__ = "schedule_items"
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.String(20))
    platform = db.Column(db.String(20))
    content_type = db.Column(db.String(20))
    score = db.Column(db.Float)
    scheduled_datetime = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="queued")  # queued / posted / cancelled


class StrategyConfig(db.Model):
    __tablename__ = "strategy_config"
    id = db.Column(db.Integer, primary_key=True)
    post_now_threshold = db.Column(db.Float, default=0.87)
    sensitivity_boost_high = db.Column(db.Float, default=1.3)
    sensitivity_boost_medium = db.Column(db.Float, default=1.15)
    max_daily_posts = db.Column(db.Integer, default=6)
    engine_cooling_mins = db.Column(db.Integer, default=15)
    prioritize_reels = db.Column(db.Boolean, default=True)
    avoid_shorts_overlap = db.Column(db.Boolean, default=False)
    cross_platform_sync = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppSettings(db.Model):
    __tablename__ = "app_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
