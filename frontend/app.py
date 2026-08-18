# frontend/app.py
#
# Run with:  streamlit run frontend/app.py
# (run from the project root, so imports of database/services/utils resolve)

import sys
import os

from datetime import date

# Make sure the project root (parent of this frontend/ folder) is importable,
# regardless of the working directory Streamlit was launched from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from database.connection import create_connection, DatabaseConnectionError
from utils.password_utils import verify_password, hash_password
from utils.validators import is_valid_email, is_valid_phone, is_valid_date
from theme import inject_theme, render_bank_header, render_account_bar, render_bank_footer

st.set_page_config(page_title="ElectroBank | Net Banking", page_icon="🏦", layout="wide")
inject_theme()

ROLE_NAMES = {1: "Admin", 2: "Staff", 3: "Customer", 4: "Manager"}


def attempt_login(email, password):
    try:
        conn = create_connection()
    except DatabaseConnectionError as e:
        st.error(str(e))
        return None

    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, role_id, password, branch
        FROM users
        WHERE email = %s AND status = 'ACTIVE'
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and verify_password(password, user[3]):
        return {
            "user_id": user[0],
            "full_name": user[1],
            "role_id": user[2],
            "branch": user[4],
        }

    return None


def register_customer(phone, dob_str, id_proof_number, email, password):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT bank_customer_id, full_name, address, branch, is_registered_on_app
            FROM bank_customers
            WHERE phone = %s AND date_of_birth = %s AND id_proof_number = %s
        """, (phone, dob_str, id_proof_number))

        record = cursor.fetchone()

        if not record:
            return False, "No matching bank record found. Please visit your branch to open an account first."

        bank_customer_id, full_name, address, branch, already_registered = record

        if already_registered:
            return False, "This account has already registered for app access. Please log in instead."

        cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        if cursor.fetchone():
            return False, "This phone number is already registered for app access."

        hashed = hash_password(password)

        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password, address, date_of_birth, role_id, branch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed, address, dob_str, 3, branch))

        cursor.execute("""
            UPDATE bank_customers SET is_registered_on_app = TRUE
            WHERE bank_customer_id = %s
        """, (bank_customer_id,))

        conn.commit()
        return True, f"Welcome, {full_name}! Your app access has been created. You can now log in."

    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}"

    finally:
        cursor.close()
        conn.close()


def show_register_form():
    st.info("You must already have an account with us to register for app access. "
            "Enter your details exactly as given at your branch.")

    with st.form("register_form"):
        phone = st.text_input("Phone (10 digits)")
        date_of_birth = st.date_input(
            "Date of Birth",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        id_proof_number = st.text_input("ID Proof Number (Aadhar/PAN)")
        email = st.text_input("E-mail")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

    if not submitted:
        return

    errors = []
    if not is_valid_phone(phone):
        errors.append("Phone must be exactly 10 digits.")
    if not id_proof_number.strip():
        errors.append("ID proof number cannot be empty.")
    if not is_valid_email(email):
        errors.append("Invalid email format.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")

    if errors:
        for e in errors:
            st.error(e)
        return

    dob_str = date_of_birth.strftime("%Y-%m-%d")
    success, message = register_customer(phone, dob_str, id_proof_number, email, password)

    if success:
        st.success(message)
    else:
        st.error(message)


def show_login():
    render_bank_header()

    left, center, right = st.columns([1, 1.3, 1])

    with center:
        st.markdown("#### Access Your Account")
        st.caption("Please use your registered credentials to sign in securely.")

        login_tab, register_tab = st.tabs(["Login", "New Customer? Register"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("E-mail")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submitted:
                user = attempt_login(email, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with register_tab:
            show_register_form()

        st.caption("🔒 For your security, never share your password or transaction PIN with anyone, "
                   "including bank staff.")

    render_bank_footer()


def show_dashboard():
    user = st.session_state["user"]
    role_id = user["role_id"]
    role_label = ROLE_NAMES.get(role_id, "Unknown")

    render_bank_header()

    with st.sidebar:
        st.markdown(f"### {user['full_name']}")
        st.caption(f"{role_label} · {user['branch']} branch")
        st.divider()
        if st.button("Logout", use_container_width=True):
            del st.session_state["user"]
            st.rerun()

    render_account_bar(user, role_label)

    if role_id == 1:
        from dashboards.admin_dashboard import render_admin_dashboard
        render_admin_dashboard(user)

    elif role_id == 4:
        from dashboards.manager_dashboard import render_manager_dashboard
        render_manager_dashboard(user)

    elif role_id == 2:
        from dashboards.staff_dashboard import render_staff_dashboard
        render_staff_dashboard(user)

    elif role_id == 3:
        from dashboards.customer_dashboard import render_customer_dashboard
        render_customer_dashboard(user)

    else:
        st.error("Unknown role assigned to this account.")

    render_bank_footer()


def main():
    if "user" not in st.session_state:
        show_login()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()