from datetime import date
from flask import Flask, redirect, url_for
from flask_login import LoginManager

from config import Config
from models import db, Employee, LeaveType


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Employee.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.employee import employee_bp
    from routes.manager import manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(403)
    def forbidden(e):
        return "403 - You don't have permission to view this page.", 403

    with app.app_context():
        db.create_all()
        seed_defaults()

    return app


def seed_defaults():
    """Create default leave types and a first admin account if none exist yet."""
    if LeaveType.query.count() == 0:
        db.session.add_all([
            LeaveType(name="Casual Leave", default_days_per_year=12, description="For personal/short-notice needs"),
            LeaveType(name="Sick Leave", default_days_per_year=10, description="For medical/health reasons"),
            LeaveType(name="Earned Leave", default_days_per_year=15, description="Accrued leave, plannable in advance"),
        ])
        db.session.commit()

    if Employee.query.filter_by(role="admin").count() == 0:
        admin = Employee(
            name="Admin",
            email="admin@company.com",
            role="admin",
            department="Administration",
            joining_date=date.today(),
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
        print(">> Default admin created: admin@company.com / Admin@123  (change this password!)")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
