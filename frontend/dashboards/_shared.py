# frontend/dashboards/_shared.py
#
# UI logic shared between the Staff and Manager dashboards.

import streamlit as st

from database.connection import create_connection
from services.notification_service import send_notification


def render_verify_bank_accounts_tab(user):
    st.subheader("Verify Bank Accounts")
    st.caption(f"Only pending requests from your branch ({user['branch']}) are shown — this is not optional scope.")

    branch = user["branch"]

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.account_id, u.full_name, u.phone,
               a.account_number, a.account_type, a.account_request_status
        FROM accounts a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.account_request_status = 'PENDING' AND u.branch = %s
    """, (branch,))
    accounts = cursor.fetchall()

    cursor.close()
    conn.close()

    if not accounts:
        st.info("No pending account verification for your branch.")
        return

    data = [
        {"Account ID": a[0], "Name": a[1], "Phone": a[2], "Account Number": a[3], "Type": a[4], "Status": a[5]}
        for a in accounts
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)

    options = {f"{a[3]} — {a[1]} ({a[4]})": a[3] for a in accounts}
    choice = st.selectbox("Select account", list(options.keys()), key="verify_acc_select")
    account_number = options[choice]

    col1, col2 = st.columns(2)

    if col1.button("Approve", type="primary", key="verify_acc_approve"):
        _act_on_account(account_number, branch, "APPROVED")

    if col2.button("Reject", key="verify_acc_reject"):
        _act_on_account(account_number, branch, "REJECTED")


def _act_on_account(account_number, branch, decision):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Re-check branch ownership right before acting.
        cursor.execute("""
            SELECT u.branch, a.user_id FROM accounts a
            JOIN users u ON a.user_id = u.user_id
            WHERE a.account_number = %s
        """, (account_number,))
        owner = cursor.fetchone()

        if not owner or owner[0] != branch:
            st.error("That account no longer belongs to your branch. You cannot act on this request.")
            return

        user_id = owner[1]

        if decision == "APPROVED":
            cursor.execute("""
                UPDATE accounts
                SET account_request_status = 'APPROVED', account_status = 'ACTIVE', is_verified = 1
                WHERE account_number = %s
            """, (account_number,))
            conn.commit()
            send_notification(user_id, f"Your account {account_number} has been verified and activated!")
            st.success("Account verified and activated!")

        else:
            cursor.execute("""
                UPDATE accounts
                SET account_request_status = 'REJECTED', account_status = 'REJECTED', is_verified = 0
                WHERE account_number = %s
            """, (account_number,))
            conn.commit()
            send_notification(user_id, f"Your account {account_number} application was rejected. Please contact staff.")
            st.success("Account rejected.")

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()