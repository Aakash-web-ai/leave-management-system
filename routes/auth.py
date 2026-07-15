from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from models import db, Employee, LeaveType, LeaveBalance

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("employee.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = Employee.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Contact an admin.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("employee.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        if Employee.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register"))

        new_emp = Employee(
            name=name,
            email=email,
            department=department,
            role="employee",
            joining_date=date.today(),
        )
        new_emp.set_password(password)
        db.session.add(new_emp)
        db.session.commit()

        # Set up initial leave balances for the current year based on leave types
        year = datetime.utcnow().year
        for lt in LeaveType.query.all():
            db.session.add(
                LeaveBalance(
                    employee_id=new_emp.id,
                    leave_type_id=lt.id,
                    year=year,
                    total_days=lt.default_days_per_year,
                    used_days=0,
                )
            )
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
