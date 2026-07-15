from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db, LeaveType, LeaveBalance, LeaveRequest

employee_bp = Blueprint("employee", __name__)


def get_or_create_balance(employee_id, leave_type_id, year):
    """Ensure a balance row exists for this employee/type/year, creating one from the
    leave type's default allocation if it doesn't."""
    balance = LeaveBalance.query.filter_by(
        employee_id=employee_id, leave_type_id=leave_type_id, year=year
    ).first()
    if not balance:
        lt = LeaveType.query.get(leave_type_id)
        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
            total_days=lt.default_days_per_year,
            used_days=0,
        )
        db.session.add(balance)
        db.session.commit()
    return balance


def business_days(start_date, end_date):
    """Count days inclusive, excluding weekends (Sat/Sun)."""
    total = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Mon-Fri
            total += 1
        current = date.fromordinal(current.toordinal() + 1)
    return total


@employee_bp.route("/")
@login_required
def dashboard():
    year = datetime.utcnow().year
    balances = get_all_balances(current_user.id, year)

    recent_requests = (
        LeaveRequest.query.filter_by(employee_id=current_user.id)
        .order_by(LeaveRequest.applied_on.desc())
        .limit(5)
        .all()
    )

    pending_count = LeaveRequest.query.filter_by(
        employee_id=current_user.id, status="pending"
    ).count()

    return render_template(
        "dashboard.html",
        balances=balances,
        recent_requests=recent_requests,
        pending_count=pending_count,
    )


def get_all_balances(employee_id, year):
    leave_types = LeaveType.query.all()
    balances = []
    for lt in leave_types:
        balances.append(get_or_create_balance(employee_id, lt.id, year))
    return balances


@employee_bp.route("/apply", methods=["GET", "POST"])
@login_required
def apply_leave():
    leave_types = LeaveType.query.all()

    if request.method == "POST":
        leave_type_id = request.form.get("leave_type_id", type=int)
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        reason = request.form.get("reason", "").strip()

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Please provide valid start and end dates.", "danger")
            return redirect(url_for("employee.apply_leave"))

        if end_date < start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("employee.apply_leave"))

        if start_date < date.today():
            flash("Start date cannot be in the past.", "danger")
            return redirect(url_for("employee.apply_leave"))

        num_days = business_days(start_date, end_date)
        year = start_date.year

        balance = get_or_create_balance(current_user.id, leave_type_id, year)
        if num_days > balance.remaining_days:
            flash(
                f"Insufficient balance. You requested {num_days} day(s) but only "
                f"have {balance.remaining_days} day(s) remaining for this leave type.",
                "danger",
            )
            return redirect(url_for("employee.apply_leave"))

        new_request = LeaveRequest(
            employee_id=current_user.id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            days=num_days,
            reason=reason,
            status="pending",
        )
        db.session.add(new_request)
        db.session.commit()

        flash(f"Leave request submitted for {num_days} day(s). Awaiting approval.", "success")
        return redirect(url_for("employee.dashboard"))

    return render_template("apply_leave.html", leave_types=leave_types, today=date.today().isoformat())


@employee_bp.route("/history")
@login_required
def history():
    requests_list = (
        LeaveRequest.query.filter_by(employee_id=current_user.id)
        .order_by(LeaveRequest.applied_on.desc())
        .all()
    )
    return render_template("history.html", requests=requests_list)


@employee_bp.route("/cancel/<int:request_id>", methods=["POST"])
@login_required
def cancel_request(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)

    if leave_request.employee_id != current_user.id:
        flash("You can't cancel someone else's request.", "danger")
        return redirect(url_for("employee.history"))

    if leave_request.status != "pending":
        flash("Only pending requests can be cancelled.", "warning")
        return redirect(url_for("employee.history"))

    leave_request.status = "cancelled"
    db.session.commit()
    flash("Leave request cancelled.", "info")
    return redirect(url_for("employee.history"))
