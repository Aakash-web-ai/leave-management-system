from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from models import db, Employee, LeaveType, LeaveBalance, LeaveRequest
from routes.employee import get_or_create_balance

manager_bp = Blueprint("manager", __name__)


def manager_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_manager_or_admin():
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@manager_bp.route("/team")
@login_required
@manager_required
def team_requests():
    status_filter = request.args.get("status", "pending")

    query = LeaveRequest.query
    if current_user.role == "manager":
        # Managers only see requests from their direct reports
        report_ids = [e.id for e in Employee.query.filter_by(manager_id=current_user.id).all()]
        query = query.filter(LeaveRequest.employee_id.in_(report_ids))

    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    requests_list = query.order_by(LeaveRequest.applied_on.desc()).all()

    return render_template("team_requests.html", requests=requests_list, status_filter=status_filter)


@manager_bp.route("/team/review/<int:request_id>", methods=["POST"])
@login_required
@manager_required
def review_request(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    action = request.form.get("action")
    comment = request.form.get("comment", "").strip()

    if leave_request.status != "pending":
        flash("This request has already been reviewed.", "warning")
        return redirect(url_for("manager.team_requests"))

    if action == "approve":
        balance = get_or_create_balance(
            leave_request.employee_id, leave_request.leave_type_id, leave_request.start_date.year
        )
        if float(leave_request.days) > balance.remaining_days:
            flash("Cannot approve: employee no longer has sufficient balance.", "danger")
            return redirect(url_for("manager.team_requests"))

        balance.used_days = float(balance.used_days) + float(leave_request.days)
        leave_request.status = "approved"
        flash(f"Leave request approved for {leave_request.employee.name}.", "success")

    elif action == "reject":
        leave_request.status = "rejected"
        flash(f"Leave request rejected for {leave_request.employee.name}.", "info")
    else:
        flash("Unknown action.", "danger")
        return redirect(url_for("manager.team_requests"))

    leave_request.reviewed_by = current_user.id
    leave_request.reviewed_on = datetime.utcnow()
    leave_request.review_comment = comment
    db.session.commit()

    return redirect(url_for("manager.team_requests"))


# ============================================
# ADMIN: employee management
# ============================================
@manager_bp.route("/admin/employees")
@login_required
@admin_required
def manage_employees():
    employees = Employee.query.order_by(Employee.name).all()
    managers = Employee.query.filter(Employee.role.in_(["manager", "admin"])).all()
    return render_template("manage_employees.html", employees=employees, managers=managers)


@manager_bp.route("/admin/employees/<int:emp_id>/update", methods=["POST"])
@login_required
@admin_required
def update_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    emp.role = request.form.get("role", emp.role)
    manager_id = request.form.get("manager_id", type=int)
    emp.manager_id = manager_id if manager_id else None
    emp.is_active_flag = request.form.get("is_active") == "on"
    db.session.commit()
    flash(f"Updated {emp.name}.", "success")
    return redirect(url_for("manager.manage_employees"))


@manager_bp.route("/admin/leave-types", methods=["GET", "POST"])
@login_required
@admin_required
def manage_leave_types():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        default_days = request.form.get("default_days", type=int)
        description = request.form.get("description", "").strip()

        if name and default_days:
            db.session.add(
                LeaveType(name=name, default_days_per_year=default_days, description=description)
            )
            db.session.commit()
            flash(f"Added leave type '{name}'.", "success")
        return redirect(url_for("manager.manage_leave_types"))

    leave_types = LeaveType.query.all()
    return render_template("manage_leave_types.html", leave_types=leave_types)


@manager_bp.route("/admin/reports")
@login_required
@admin_required
def reports():
    year = datetime.utcnow().year
    all_requests = (
        LeaveRequest.query.filter(db.extract("year", LeaveRequest.start_date) == year)
        .order_by(LeaveRequest.start_date.desc())
        .all()
    )

    total_approved = sum(float(r.days) for r in all_requests if r.status == "approved")
    total_pending = len([r for r in all_requests if r.status == "pending"])
    total_rejected = len([r for r in all_requests if r.status == "rejected"])

    return render_template(
        "reports.html",
        requests=all_requests,
        year=year,
        total_approved=total_approved,
        total_pending=total_pending,
        total_rejected=total_rejected,
    )
