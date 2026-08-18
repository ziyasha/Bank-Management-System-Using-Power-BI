# frontend/dashboards/manager_dashboard.py

import os

from datetime import date

import streamlit as st

from database.connection import create_connection
from utils.password_utils import hash_password
from utils.validators import is_valid_email, is_valid_phone
from utils.branches import BRANCHES
from services.report_service import export_manager_reports, REPORTS_DIR
from services.loan_service import approve_loan, reject_loan
from services.notification_service import send_notification
from dashboards._shared import render_verify_bank_accounts_tab


def render_manager_dashboard(user):
    st.title("Manager Dashboard")

    tabs = st.tabs([
        "View Staff",
        "View Users",
        "Register Staff",
        "Remove Staff",
        "Verify Bank Accounts",
        "Review Verified Loans",
        "View Complaints",
        "Track User Activities",
        "Staff Summary",
        "User Summary",
        "Export Reports (CSV)",
    ])

    with tabs[0]:
        _view_staff_tab(user)

    with tabs[1]:
        _view_users_tab(user)

    with tabs[2]:
        _register_staff_tab()

    with tabs[3]:
        _remove_staff_tab()

    with tabs[4]:
        render_verify_bank_accounts_tab(user)

    with tabs[5]:
        _review_verified_loans_tab()

    with tabs[6]:
        _view_complaints_tab()

    with tabs[7]:
        _track_user_activities_tab()

    with tabs[8]:
        _staff_summary_tab()

    with tabs[9]:
        _user_summary_tab()

    with tabs[10]:
        _export_reports_tab(user)


def _branch_scope_choice(user, key):
    scope = st.radio(
        "Scope", [f"My Branch ({user['branch']})", "All Branches"],
        horizontal=True, key=key,
    )
    return None if scope == "All Branches" else user["branch"]


# ---------------------------------------------------------------------
# View Staff
# ---------------------------------------------------------------------

def _view_staff_tab(user):
    st.subheader("View Staff")

    branch = _branch_scope_choice(user, "staff_scope")

    conn = create_connection()
    cursor = conn.cursor()

    if branch:
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users WHERE role_id = 2 AND status = 'ACTIVE' AND branch = %s
        """, (branch,))
    else:
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users WHERE role_id = 2 AND status = 'ACTIVE'
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No staff found for this scope.")
        return

    data = [
        {"ID": f"ST{r[0]}", "Name": r[1], "Email": r[2], "Phone": r[3], "Status": r[4], "Branch": r[5]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# View Users
# ---------------------------------------------------------------------

def _view_users_tab(user):
    st.subheader("View Users")

    branch = _branch_scope_choice(user, "users_scope")

    conn = create_connection()
    cursor = conn.cursor()

    if branch:
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users WHERE role_id = 3 AND status = 'ACTIVE' AND branch = %s
        """, (branch,))
    else:
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users WHERE role_id = 3 AND status = 'ACTIVE'
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No users found for this scope.")
        return

    data = [
        {"ID": f"CU{r[0]}", "Name": r[1], "Email": r[2], "Phone": r[3], "Status": r[4], "Branch": r[5]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Register Staff
# ---------------------------------------------------------------------

def _register_staff_tab():
    st.subheader("Register Staff")

    with st.form("register_staff_form", clear_on_submit=True):
        full_name = st.text_input("Name")
        email = st.text_input("E-mail")
        phone = st.text_input("Phone (10 digits)")
        password = st.text_input("Password", type="password")
        address = st.text_input("Address")
        date_of_birth = st.date_input(
            "Date of Birth",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        branch = st.selectbox("Branch", BRANCHES)

        submitted = st.form_submit_button("Register Staff")

    if not submitted:
        return

    errors = []
    if not full_name.strip():
        errors.append("Name cannot be empty.")
    if not is_valid_email(email):
        errors.append("Invalid email format.")
    if not is_valid_phone(phone):
        errors.append("Phone must be exactly 10 digits.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if not address.strip():
        errors.append("Address cannot be empty.")

    if errors:
        for e in errors:
            st.error(e)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        if cursor.fetchone():
            st.error("This phone number is already registered. Please use a different phone number.")
            return

        hashed = hash_password(password)
        dob_str = date_of_birth.strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password, address, date_of_birth, role_id, branch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed, address, dob_str, 2, branch))

        conn.commit()
        st.success(f"Staff '{full_name}' registered successfully at the {branch} branch!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Remove Staff
# ---------------------------------------------------------------------

def _remove_staff_tab():
    st.subheader("Remove Staff")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users WHERE role_id = 2 AND status = 'ACTIVE'
    """)
    staff = cursor.fetchall()

    cursor.close()
    conn.close()

    if not staff:
        st.info("No active staff found.")
        return

    options = {f"ST{s[0]} — {s[1]} ({s[5]})": s[0] for s in staff}
    choice = st.selectbox("Select staff to remove", list(options.keys()))

    if st.button("Remove Selected Staff", type="primary"):
        staff_id = options[choice]

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users SET status = 'REMOVED'
                WHERE user_id = %s AND role_id = 2
            """, (staff_id,))
            conn.commit()

            st.success("Staff removed successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------

def _review_verified_loans_tab():
    st.subheader("Review Verified Loans")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.loan_id, u.full_name, u.phone, l.loan_amount, l.loan_type, l.duration
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        WHERE l.status = 'VERIFIED_BY_STAFF'
    """)
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    if not loans:
        st.info("No verified loans waiting for approval.")
        return

    data = [
        {"Loan ID": l[0], "Name": l[1], "Phone": l[2], "Amount": l[3], "Type": l[4], "Duration (months)": l[5]}
        for l in loans
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)

    options = {f"Loan {l[0]} — {l[1]} ({l[4]})": l[0] for l in loans}
    choice = st.selectbox("Select loan", list(options.keys()))
    loan_id = options[choice]

    col1, col2 = st.columns(2)

    if col1.button("Approve Loan", type="primary"):
        approve_loan(loan_id)
        _notify_loan_decision(loan_id, "APPROVED")
        st.success("Loan approved!")
        st.rerun()

    if col2.button("Reject Loan"):
        reject_loan(loan_id)
        _notify_loan_decision(loan_id, "REJECTED")
        st.success("Loan rejected.")
        st.rerun()


def _notify_loan_decision(loan_id, decision):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM loans WHERE loan_id = %s", (loan_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        send_notification(result[0], f"Your loan application (ID: {loan_id}) has been {decision}!")


# ---------------------------------------------------------------------
# View Complaints (global, read-only — matches CLI behavior)
# ---------------------------------------------------------------------

def _view_complaints_tab():
    st.subheader("View Complaints")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT complaint_id, user_id, subject, description, status, created_at, resolved_on
        FROM complaints
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        st.info("No complaints found.")
        return

    data = [
        {
            "Complaint ID": r[0], "User ID": f"CU{r[1]}", "Subject": r[2],
            "Description": r[3], "Status": r[4], "Submitted On": r[5],
            "Resolved On": r[6] if r[6] else "Not Resolved Yet",
        }
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Track User Activities (last 50, global — matches CLI behavior)
# ---------------------------------------------------------------------

def _track_user_activities_tab():
    st.subheader("Track User Activities")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.full_name, a.account_number, t.transaction_type,
               t.amount, t.balance_after, t.transaction_time
        FROM transactions t
        JOIN accounts a ON t.account_number = a.account_number
        JOIN users u ON a.user_id = u.user_id
        ORDER BY t.transaction_time DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        st.info("No activity found.")
        return

    data = [
        {
            "User": r[0], "Account": r[1], "Type": r[2],
            "Amount": r[3], "Balance After": r[4], "Time": r[5],
        }
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Staff Summary
# ---------------------------------------------------------------------

def _staff_summary_tab():
    st.subheader("Staff Dashboard Summary")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, phone, status
        FROM users WHERE role_id = 2
    """)
    staff_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'VERIFIED_BY_STAFF'")
    verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'resolved'")
    resolved = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    if not staff_list:
        st.info("No staff found.")
        return

    data = [
        {
            "ID": f"ST{s[0]}", "Name": s[1], "Phone": s[2], "Status": s[3],
            "Loans Verified (bank-wide)": verified, "Complaints Resolved (bank-wide)": resolved,
        }
        for s in staff_list
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.caption("Loan/complaint counts are bank-wide totals, matching the original CLI report — not per-staff attribution.")


# ---------------------------------------------------------------------
# User Summary
# ---------------------------------------------------------------------

def _user_summary_tab():
    st.subheader("User Dashboard Summary")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.user_id, u.full_name, u.phone,
               COUNT(a.account_id) AS total_accounts,
               COALESCE(SUM(a.balance), 0) AS total_balance
        FROM users u
        LEFT JOIN accounts a ON u.user_id = a.user_id
        WHERE u.role_id = 3
        GROUP BY u.user_id
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        st.info("No users found.")
        return

    data = [
        {"ID": f"CU{r[0]}", "Name": r[1], "Phone": r[2], "Total Accounts": r[3], "Total Balance": r[4]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Export Reports (CSV) — branch or all branches
# ---------------------------------------------------------------------

def _export_reports_tab(user):
    st.subheader("Export Reports (CSV)")

    branch = _branch_scope_choice(user, "export_scope")

    if st.button("Generate Reports", type="primary"):
        export_manager_reports(branch=branch)
        st.success("Reports generated.")

    if os.path.isdir(REPORTS_DIR):
        prefix = "manager_"
        files = sorted(f for f in os.listdir(REPORTS_DIR) if f.startswith(prefix) and f.endswith(".csv"))

        if files:
            st.write("Available manager reports:")
            for fname in files:
                fpath = os.path.join(REPORTS_DIR, fname)
                with open(fpath, "rb") as f:
                    st.download_button(
                        f"⬇ Download {fname}",
                        data=f.read(),
                        file_name=fname,
                        mime="text/csv",
                        key=f"dl_{fname}",
                    )
        else:
            st.info("No manager reports generated yet. Click 'Generate Reports' above.")