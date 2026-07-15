from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Employee(db.Model, UserMixin):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("employee", "manager", "admin", name="role_enum"), default="employee")
    department = db.Column(db.String(100))
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)
    joining_date = db.Column(db.Date, nullable=False)
    is_active_flag = db.Column("is_active", db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship("Employee", remote_side=[id], backref="reports")
    leave_requests = db.relationship("LeaveRequest", foreign_keys="LeaveRequest.employee_id", backref="employee", lazy="dynamic")
    balances = db.relationship("LeaveBalance", backref="employee", lazy="dynamic")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_manager_or_admin(self):
        return self.role in ("manager", "admin")

    # Flask-Login uses get_id(); UserMixin already provides is_active,
    # but we override it to reflect our own is_active column.
    @property
    def is_active(self):
        return self.is_active_flag


class LeaveType(db.Model):
    __tablename__ = "leave_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    default_days_per_year = db.Column(db.Integer, nullable=False, default=12)
    description = db.Column(db.String(255))


class LeaveBalance(db.Model):
    __tablename__ = "leave_balances"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey("leave_types.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_days = db.Column(db.Numeric(5, 1), nullable=False, default=0)
    used_days = db.Column(db.Numeric(5, 1), nullable=False, default=0)

    leave_type = db.relationship("LeaveType")

    @property
    def remaining_days(self):
        return float(self.total_days) - float(self.used_days)

    __table_args__ = (
        db.UniqueConstraint("employee_id", "leave_type_id", "year", name="unique_balance"),
    )


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey("leave_types.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Numeric(5, 1), nullable=False)
    reason = db.Column(db.String(500))
    status = db.Column(
        db.Enum("pending", "approved", "rejected", "cancelled", name="status_enum"),
        default="pending",
    )
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)
    reviewed_on = db.Column(db.DateTime, nullable=True)
    review_comment = db.Column(db.String(500))

    leave_type = db.relationship("LeaveType")
    reviewer = db.relationship("Employee", foreign_keys=[reviewed_by])
