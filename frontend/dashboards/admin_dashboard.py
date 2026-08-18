# frontend/dashboards/admin_dashboard.py

import os

from datetime import date

import streamlit as st

from database.connection import create_connection
from utils.password_utils import hash_password
from utils.validators import is_valid_email, is_valid_phone
from utils.branches import BRANCHES
from services.report_service import export_all_reports, REPORTS_DIR


def render_admin_dashboard(user):
    st.title("Admin Dashboard")

    tabs = st.tabs([
        "Register Manager",
        "Remove Manager",
        "View Managers",
        "View Customers",
        "System Reports",
        "Export Reports (CSV)",
    ])

    with tabs[0]:
        _register_manager_tab()

    with tabs[1]:
        _remove_manager_tab()

    with tabs[2]:
        _view_managers_tab()

    with tabs[3]:
        _view_customers_tab()

    with tabs[4]:
        _system_reports_tab()

    with tabs[5]:
        _export_reports_tab()


# ---------------------------------------------------------------------
# Register Manager
# ---------------------------------------------------------------------

def _register_manager_tab():
    st.subheader("Register Bank Manager")

    with st.form("register_manager_form", clear_on_submit=True):
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

        submitted = st.form_submit_button("Register Manager")

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
        # Phone numbers must be unique. Email is allowed to repeat.
        cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        if cursor.fetchone():
            st.error("This phone number is already registered. Please use a different phone number.")
            return

        hashed = hash_password(password)
        dob_str = date_of_birth.strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password, address, date_of_birth, role_id, branch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed, address, dob_str, 4, branch))

        conn.commit()
        st.success(f"Manager '{full_name}' registered successfully at the {branch} branch!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Remove Manager
# ---------------------------------------------------------------------

def _remove_manager_tab():
    st.subheader("Remove Manager")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 4 AND status = 'ACTIVE'
    """)
    managers = cursor.fetchall()

    cursor.close()
    conn.close()

    if not managers:
        st.info("No active managers found.")
        return

    options = {
        f"MG{m[0]} — {m[1]} ({m[5]})": m[0]
        for m in managers
    }

    choice = st.selectbox("Select manager to remove", list(options.keys()))

    if st.button("Remove Selected Manager", type="primary"):
        manager_id = options[choice]

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users SET status = 'REMOVED'
                WHERE user_id = %s AND role_id = 4
            """, (manager_id,))
            conn.commit()

            st.success("Manager removed successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------
# View Managers
# ---------------------------------------------------------------------

def _view_managers_tab():
    st.subheader("View Managers")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 4 AND status = 'ACTIVE'
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        st.info("No active managers found.")
        return

    data = [
        {
            "ID": f"MG{r[0]}", "Name": r[1], "Email": r[2],
            "Phone": r[3], "Status": r[4], "Branch": r[5],
        }
        for r in rows
    ]

    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# View Customers
# ---------------------------------------------------------------------

def _view_customers_tab():
    st.subheader("View Customers")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 3
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        st.info("No customers found.")
        return

    data = [
        {
            "ID": f"CU{r[0]}", "Name": r[1], "Email": r[2],
            "Phone": r[3], "Status": r[4], "Branch": r[5],
        }
        for r in rows
    ]

    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# System Reports
# ---------------------------------------------------------------------

def _system_reports_tab():
    st.subheader("System Reports")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM accounts")
    total_accounts = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM accounts")
    total_money = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'pending'")
    pending_loans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'open'")
    open_complaints = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", total_users)
    col2.metric("Total Accounts", total_accounts)
    col3.metric("Total Money", f"₹{total_money:,.2f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Total Transactions", total_transactions)
    col5.metric("Pending Loans", pending_loans)
    col6.metric("Open Complaints", open_complaints)


# ---------------------------------------------------------------------
# Export Reports (CSV)
# ---------------------------------------------------------------------

def _export_reports_tab():
    st.subheader("Export Reports (CSV for Power BI)")
    st.caption("Generates a full, unscoped snapshot of every table — accounts, transactions, loans, and complaints.")

    if st.button("Generate Reports", type="primary"):
        export_all_reports()
        st.success("Reports generated.")

    if os.path.isdir(REPORTS_DIR):
        files = sorted(f for f in os.listdir(REPORTS_DIR) if f.endswith(".csv"))

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
            st.info("No reports generated yet. Click 'Generate Reports' above.")