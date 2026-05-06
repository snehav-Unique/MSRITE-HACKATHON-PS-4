import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db


def create_app():
    app = Flask(__name__)

    db_path = os.path.join(os.path.dirname(__file__), "optimetric.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "optimetric-hackathon-2024"

    CORS(app, origins="*")
    db.init_app(app)

    from routes.dashboard import dashboard_bp
    from routes.analytics import analytics_bp
    from routes.schedule import schedule_bp
    from routes.settings import settings_bp
    from routes.strategy import strategy_bp

    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(schedule_bp, url_prefix="/api/schedule")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
    app.register_blueprint(strategy_bp, url_prefix="/api/strategy")

    with app.app_context():
        db.create_all()
        from seed_data import seed_database
        seed_database()

    @app.route("/api/health")
    def health():
        return jsonify(status="ok", version="1.0.0")

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n  OptiMetric backend running at http://localhost:5000\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
