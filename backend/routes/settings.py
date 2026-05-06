from flask import Blueprint, jsonify, request
from models import db, AppSettings

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
def get_settings():
    rows = AppSettings.query.all()
    return jsonify({r.key: r.value for r in rows})


@settings_bp.route("/", methods=["PUT"])
def update_settings():
    data = request.get_json() or {}
    for key, value in data.items():
        row = AppSettings.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
        else:
            db.session.add(AppSettings(key=key, value=str(value)))
    db.session.commit()
    return jsonify(success=True)
