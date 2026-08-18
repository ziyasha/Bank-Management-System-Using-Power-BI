# services/report_service.py
#
# Exports snapshots of the core tables to CSV so they can be picked up
# by Power BI (or Excel) as a data source. This is the bridge between
# the Python/MySQL backend and the BI/reporting layer.
#
# Three tiers, each writing to their own files so they never collide:
#   - Admin   : export_all_reports()        -> full data, all branches
#   - Manager : export_manager_reports()     -> full data, own branch or all
#   - Staff   : export_customer_report()     -> customers only, own branch or all

import csv
import os
import re

from database.connection import create_connection

REPORTS_DIR = "reports"


def _safe_slug(text):
    """Turns a branch name into something safe to use in a filename."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return slug or "branch"


def _write_csv(filename, headers, rows):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return filepath


# ---------- Core exports (each supports an optional branch filter) ----------

def export_accounts_csv(branch=None, filename=None):
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT a.account_number, a.account_type, a.balance,
               a.account_status, a.account_request_status,
               u.user_id, u.full_name, u.branch
        FROM accounts a
        JOIN users u ON a.user_id = u.user_id
    """
    params = ()

    if branch:
        query += " WHERE u.branch = %s"
        params = (branch,)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    headers = [
        "account_number", "account_type", "balance",
        "account_status", "account_request_status",
        "user_id", "full_name", "branch"
    ]

    return _write_csv(filename or "accounts_report.csv", headers, rows)


def export_transactions_csv(branch=None, filename=None):
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.transaction_id, t.account_number, t.transaction_type,
               t.amount, t.balance_after, t.transaction_time,
               u.branch
        FROM transactions t
        JOIN accounts a ON t.account_number = a.account_number
        JOIN users u ON a.user_id = u.user_id
    """
    params = ()

    if branch:
        query += " WHERE u.branch = %s"
        params = (branch,)

    query += " ORDER BY t.transaction_time DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    headers = [
        "transaction_id", "account_number", "transaction_type",
        "amount", "balance_after", "transaction_time", "branch"
    ]

    return _write_csv(filename or "transactions_report.csv", headers, rows)


def export_loans_csv(branch=None, filename=None):
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT l.loan_id, u.full_name, u.branch, l.loan_amount,
               l.loan_type, l.duration, l.status, l.admin_status
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
    """
    params = ()

    if branch:
        query += " WHERE u.branch = %s"
        params = (branch,)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    headers = [
        "loan_id", "full_name", "branch", "loan_amount",
        "loan_type", "duration", "status", "admin_status"
    ]

    return _write_csv(filename or "loans_report.csv", headers, rows)


def export_complaints_csv(branch=None, filename=None):
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.complaint_id, u.full_name, u.branch, c.subject,
               c.status, c.created_at, c.resolved_on
        FROM complaints c
        JOIN users u ON c.user_id = u.user_id
    """
    params = ()

    if branch:
        query += " WHERE u.branch = %s"
        params = (branch,)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    headers = [
        "complaint_id", "full_name", "branch", "subject",
        "status", "created_at", "resolved_on"
    ]

    return _write_csv(filename or "complaints_report.csv", headers, rows)


def export_customers_csv(branch=None, filename=None):
    """Customers only (role_id = 3) — this is the report staff are allowed to pull."""
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT u.user_id, u.full_name, u.email, u.phone,
               u.branch, u.status,
               COUNT(a.account_id) AS total_accounts,
               COALESCE(SUM(a.balance), 0) AS total_balance
        FROM users u
        LEFT JOIN accounts a ON u.user_id = a.user_id
        WHERE u.role_id = 3
    """
    params = ()

    if branch:
        query += " AND u.branch = %s"
        params = (branch,)

    query += " GROUP BY u.user_id"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    headers = [
        "user_id", "full_name", "email", "phone",
        "branch", "status", "total_accounts", "total_balance"
    ]

    return _write_csv(filename or "customers_report.csv", headers, rows)


# ---------- Role-level entry points ----------

def export_all_reports():
    """Admin: full data, every branch, in the default filenames."""
    print("\n--- Exporting Reports for Power BI ---")

    try:
        paths = [
            export_accounts_csv(),
            export_transactions_csv(),
            export_loans_csv(),
            export_complaints_csv(),
        ]

        print("\nReports exported successfully:")
        for p in paths:
            print(f" - {p}")

        print("\nPoint Power BI at the 'reports' folder as a data source and refresh.")

    except Exception as e:
        print("\nError exporting reports:", e)


def export_manager_reports(branch=None):
    """Manager: full data (accounts/transactions/loans/complaints), own branch or all."""
    print("\n--- Exporting Reports ---")

    try:
        suffix = f"_{_safe_slug(branch)}" if branch else "_all_branches"

        paths = [
            export_accounts_csv(branch=branch, filename=f"manager_accounts{suffix}.csv"),
            export_transactions_csv(branch=branch, filename=f"manager_transactions{suffix}.csv"),
            export_loans_csv(branch=branch, filename=f"manager_loans{suffix}.csv"),
            export_complaints_csv(branch=branch, filename=f"manager_complaints{suffix}.csv"),
        ]

        print("\nReports exported successfully:")
        for p in paths:
            print(f" - {p}")

    except Exception as e:
        print("\nError exporting reports:", e)


def export_customer_report(branch=None):
    """Staff: customers only, own branch or all."""
    print("\n--- Exporting Customer Report ---")

    try:
        suffix = f"_{_safe_slug(branch)}" if branch else "_all_branches"
        path = export_customers_csv(branch=branch, filename=f"staff_customers{suffix}.csv")

        print(f"\nCustomer report exported successfully:\n - {path}")

    except Exception as e:
        print("\nError exporting report:", e)