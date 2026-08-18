# frontend/dashboards/staff_dashboard.py

import os

from datetime import date

import streamlit as st

from database.connection import create_connection
from utils.validators import is_valid_phone
from services.report_service import export_customer_report, REPORTS_DIR
from services.loan_service import verify_loan
from services.notification_service import send_notification
from dashboards._shared import render_verify_bank_accounts_tab


def render_staff_dashboard(user):
    st.title("Staff Dashboard")

    tabs = st.tabs([
        "Search Customer",
        "View Customer",
        "Process Loan Application",
        "Resolve Complaints",
        "Generate Reports",
        "Verify Bank Accounts",
        "Export Customer Report (CSV)",
        "Enroll New Customer",
    ])

    with tabs[0]:
        _search_customer_tab(user)

    with tabs[1]:
        _view_customer_tab()

    with tabs[2]:
        _process_loan_application_tab()

    with tabs[3]:
        _resolve_complaints_tab()

    with tabs[4]:
        _generate_reports_tab()

    with tabs[5]:
        render_verify_bank_accounts_tab(user)

    with tabs[6]:
        _export_customer_report_tab(user)

    with tabs[7]:
        _enroll_customer_tab(user)


def _branch_scope_choice(user, key):
    scope = st.radio(
        "Scope", [f"My Branch ({user['branch']})", "All Branches"],
        horizontal=True, key=key,
    )
    return None if scope == "All Branches" else user["branch"]


# ---------------------------------------------------------------------
# Search Customer
# ---------------------------------------------------------------------

def _search_customer_tab(user):
    st.subheader("Search Customer")

    branch = _branch_scope_choice(user, "search_scope")
    keyword = st.text_input("Name or Account Number")

    if not st.button("Search"):
        return

    if not keyword.strip():
        st.warning("Enter a name or account number to search.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    if branch:
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.phone, a.account_number,
                   a.account_type, a.balance, u.branch
            FROM users u
            JOIN accounts a ON u.user_id = a.user_id
            WHERE (u.full_name LIKE %s OR a.account_number = %s) AND u.branch = %s
        """, (f"%{keyword}%", keyword, branch))
    else:
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.phone, a.account_number,
                   a.account_type, a.balance, u.branch
            FROM users u
            JOIN accounts a ON u.user_id = a.user_id
            WHERE u.full_name LIKE %s OR a.account_number = %s
        """, (f"%{keyword}%", keyword))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No customer found.")
        return

    data = [
        {
            "Name": r[1], "Phone": r[2], "Account": r[3],
            "Type": r[4], "Balance": r[5], "Branch": r[6],
        }
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# View Customer
# ---------------------------------------------------------------------

def _view_customer_tab():
    st.subheader("View Customer")

    account_number = st.text_input("Account Number", key="view_customer_acc")

    if not st.button("View"):
        return

    if not account_number.strip():
        st.warning("Enter an account number.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.full_name, u.email, u.phone, u.address,
               a.account_number, a.account_type, a.balance, u.branch
        FROM users u
        JOIN accounts a ON u.user_id = a.user_id
        WHERE a.account_number = %s
    """, (account_number,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not data:
        st.info("Customer not found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Name:** {data[0]}")
        st.write(f"**Email:** {data[1]}")
        st.write(f"**Phone:** {data[2]}")
        st.write(f"**Address:** {data[3]}")
    with col2:
        st.write(f"**Account:** {data[4]}")
        st.write(f"**Type:** {data[5]}")
        st.write(f"**Balance:** ₹{data[6]:,.2f}")
        st.write(f"**Branch:** {data[7]}")


# ---------------------------------------------------------------------
# Process Loan Application
# ---------------------------------------------------------------------

def _process_loan_application_tab():
    st.subheader("Process Loan Application")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.loan_id, u.full_name, u.phone, l.loan_amount, l.loan_type, l.duration
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        WHERE l.status = 'PENDING'
    """)
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    if not loans:
        st.info("No pending loan applications.")
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

    if col1.button("Verify (send to Manager)", type="primary"):
        verify_loan(loan_id)
        st.success("Documents verified! Waiting for manager approval.")
        st.rerun()

    if col2.button("Reject"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE loans SET status = 'REJECTED_BY_STAFF' WHERE loan_id = %s
            """, (loan_id,))
            conn.commit()
            st.success("Loan rejected.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------
# Resolve Complaints
# ---------------------------------------------------------------------

def _resolve_complaints_tab():
    st.subheader("Resolve Complaints")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.complaint_id, u.full_name, u.phone, c.subject, c.description, c.status
        FROM complaints c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.status = 'open'
    """)
    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    if not complaints:
        st.info("No open complaints.")
        return

    data = [
        {"Complaint ID": c[0], "Name": c[1], "Phone": c[2], "Subject": c[3], "Description": c[4], "Status": c[5]}
        for c in complaints
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)

    options = {f"Complaint {c[0]} — {c[3]}": c[0] for c in complaints}
    choice = st.selectbox("Select complaint to resolve", list(options.keys()))
    complaint_id = options[choice]

    if st.button("Mark as Resolved", type="primary"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE complaints
                SET status = 'RESOLVED', resolved_on = CURRENT_TIMESTAMP
                WHERE complaint_id = %s
            """, (complaint_id,))
            conn.commit()

            cursor.execute("SELECT user_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
            result = cursor.fetchone()
            if result:
                send_notification(result[0], f"Your complaint (ID: {complaint_id}) has been resolved!")

            st.success("Complaint resolved!")
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------
# Generate Reports
# ---------------------------------------------------------------------

def _generate_reports_tab():
    st.subheader("System Reports")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM accounts")
    accounts = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM accounts")
    total_balance = cursor.fetchone()[0] or 0

    cursor.close()
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", users)
    col2.metric("Total Accounts", accounts)
    col3.metric("Total Bank Balance", f"₹{total_balance:,.2f}")


# ---------------------------------------------------------------------
# Export Customer Report (CSV) — customers only, branch or all
# ---------------------------------------------------------------------

def _export_customer_report_tab(user):
    st.subheader("Export Customer Report (CSV)")
    st.caption("Customers only — no staff or manager data, matching your Search Customer access.")

    branch = _branch_scope_choice(user, "export_scope")

    if st.button("Generate Report", type="primary"):
        export_customer_report(branch=branch)
        st.success("Report generated.")

    if os.path.isdir(REPORTS_DIR):
        prefix = "staff_customers"
        files = sorted(f for f in os.listdir(REPORTS_DIR) if f.startswith(prefix) and f.endswith(".csv"))

        if files:
            st.write("Available reports:")
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
            st.info("No reports generated yet. Click 'Generate Report' above.")


# ---------------------------------------------------------------------
# Enroll New Customer
# ---------------------------------------------------------------------

def _enroll_customer_tab(user):
    st.subheader("Enroll New Customer")
    st.caption(f"Branch: {user['branch']} (your branch)")

    with st.form("enroll_customer_form", clear_on_submit=True):
        full_name = st.text_input("Customer Full Name")
        phone = st.text_input("Phone (10 digits)")
        date_of_birth = st.date_input(
            "Date of Birth",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        id_proof_number = st.text_input("ID Proof Number (Aadhar/PAN)")
        address = st.text_input("Address")

        submitted = st.form_submit_button("Enroll Customer")

    if not submitted:
        return

    errors = []
    if not full_name.strip():
        errors.append("Name cannot be empty.")
    if not is_valid_phone(phone):
        errors.append("Phone must be exactly 10 digits.")
    if not id_proof_number.strip():
        errors.append("ID proof number cannot be empty.")
    if not address.strip():
        errors.append("Address cannot be empty.")

    if errors:
        for e in errors:
            st.error(e)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT bank_customer_id FROM bank_customers
            WHERE phone = %s OR id_proof_number = %s
        """, (phone, id_proof_number))

        if cursor.fetchone():
            st.error("A customer record with this phone or ID proof already exists.")
            return

        dob_str = date_of_birth.strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO bank_customers
            (full_name, phone, date_of_birth, id_proof_number, address, branch, is_registered_on_app)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
        """, (full_name, phone, dob_str, id_proof_number, address, user["branch"]))

        conn.commit()

        st.success(f"Customer '{full_name}' enrolled under {user['branch']} branch.")
        st.caption("They can now self-register for app access using their phone, date of birth, and ID proof.")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()