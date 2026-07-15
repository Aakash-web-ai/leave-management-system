-- Employee Leave Management System - Database Schema
-- Run this once to set up the database: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS leave_management;
USE leave_management;

-- ============================================
-- EMPLOYEES (also acts as users table for login)
-- ============================================
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('employee', 'manager', 'admin') NOT NULL DEFAULT 'employee',
    department VARCHAR(100),
    manager_id INT DEFAULT NULL,
    joining_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
);

-- ============================================
-- LEAVE TYPES (Casual, Sick, Earned, etc.)
-- ============================================
CREATE TABLE IF NOT EXISTS leave_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    default_days_per_year INT NOT NULL DEFAULT 12,
    description VARCHAR(255)
);

-- ============================================
-- LEAVE BALANCES (per employee, per leave type, per year)
-- ============================================
CREATE TABLE IF NOT EXISTS leave_balances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type_id INT NOT NULL,
    year INT NOT NULL,
    total_days DECIMAL(5,1) NOT NULL DEFAULT 0,
    used_days DECIMAL(5,1) NOT NULL DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id) ON DELETE CASCADE,
    UNIQUE KEY unique_balance (employee_id, leave_type_id, year)
);

-- ============================================
-- LEAVE REQUESTS
-- ============================================
CREATE TABLE IF NOT EXISTS leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days DECIMAL(5,1) NOT NULL,
    reason VARCHAR(500),
    status ENUM('pending', 'approved', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
    applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT DEFAULT NULL,
    reviewed_on TIMESTAMP NULL DEFAULT NULL,
    review_comment VARCHAR(500),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES employees(id) ON DELETE SET NULL
);

-- ============================================
-- SEED DATA: default leave types
-- ============================================
INSERT INTO leave_types (name, default_days_per_year, description) VALUES
('Casual Leave', 12, 'For personal/short-notice needs'),
('Sick Leave', 10, 'For medical/health reasons'),
('Earned Leave', 15, 'Accrued leave, plannable in advance')
ON DUPLICATE KEY UPDATE name = name;

-- ============================================
-- SEED DATA: one admin account (password: Admin@123)
-- Password hash below corresponds to 'Admin@123' using werkzeug's
-- generate_password_hash - the app will also auto-create this on first run.
-- ============================================
-- (Left to app.py's init-db step so hashes match the app's exact hashing method.)
