# frontend/dashboards/customer_dashboard.py

from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st

from database.connection import create_connection
from utils.password_utils import hash_password, verify_password, hash_pin, verify_pin
from services.account_service import generate_account_number
from services.transaction_service import DAILY_WITHDRAWAL_LIMIT


def render_customer_dashboard(user):
    st.title("Customer Dashboard")

    unread = _unread_notification_count(user["user_id"])
    if unread:
        st.warning(f"🔔 You have {unread} unread notification(s) — see the Notifications tab.")

    tabs = st.tabs([
        "Profile",
        "Apply for Account",
        "Account Status",
        "Deposit",
        "Withdraw",
        "Transfer",
        "Balance",
        "Transaction History",
        "Apply for Loan",
        "Loan Status",
        "Submit Complaint",
        "Notifications",
        "Change Password",
        "Transaction PIN",
    ])

    with tabs[0]:
        _profile_tab(user)
    with tabs[1]:
        _apply_account_tab(user)
    with tabs[2]:
        _account_status_tab(user)
    with tabs[3]:
        _deposit_tab(user)
    with tabs[4]:
        _withdraw_tab(user)
    with tabs[5]:
        _transfer_tab(user)
    with tabs[6]:
        _balance_tab(user)
    with tabs[7]:
        _transaction_history_tab(user)
    with tabs[8]:
        _apply_loan_tab(user)
    with tabs[9]:
        _loan_status_tab(user)
    with tabs[10]:
        _submit_complaint_tab(user)
    with tabs[11]:
        _notifications_tab(user)
    with tabs[12]:
        _change_password_tab(user)
    with tabs[13]:
        _transaction_pin_tab(user)


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------

def _unread_notification_count(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE
    """, (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def _get_active_accounts(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_number, account_type, balance
        FROM accounts
        WHERE user_id = %s AND account_status = 'ACTIVE'
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def _verify_pin_input(user_id, pin):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT transaction_pin FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not result[0]:
        return False, "No transaction PIN set. Please set one in the Transaction PIN tab first."
    if not verify_pin(pin, result[0]):
        return False, "Incorrect PIN. Transaction cancelled."
    return True, None


def _parse_amount(raw):
    try:
        amount = Decimal(raw)
        if amount <= 0:
            return None
        return amount
    except (InvalidOperation, ValueError):
        return None


# ---------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------

def _profile_tab(user):
    st.subheader("Profile Details")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, email, phone, address, date_of_birth, status, branch
        FROM users WHERE user_id = %s
    """, (user["user_id"],))
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not data:
        st.error("Profile not found.")
        return

    st.write(f"**Name:** {data[0]}")
    st.write(f"**Email:** {data[1]}")
    st.write(f"**Phone:** {data[2]}")
    st.write(f"**Address:** {data[3]}")
    st.write(f"**Date of Birth:** {data[4]}")
    st.write(f"**Status:** {data[5]}")
    st.write(f"**Branch:** {data[6]}")
    st.write(f"**User ID:** CU{user['user_id']}")


# ---------------------------------------------------------------------
# Apply for Account
# ---------------------------------------------------------------------

def _apply_account_tab(user):
    st.subheader("Apply for Bank Account")
    st.caption("Your request will be reviewed by staff/manager at your branch before it becomes active.")

    with st.form("apply_account_form"):
        account_type = st.selectbox("Account Type", ["SAVINGS", "CURRENT"])
        submitted = st.form_submit_button("Submit Application")

    if not submitted:
        return

    account_number = generate_account_number()

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO accounts
            (user_id, account_number, account_type, balance,
            account_status, account_request_status, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user["user_id"], account_number, account_type, 0.00, "INACTIVE", "PENDING", False))

        conn.commit()

        st.success("Bank account application submitted!")
        st.write(f"**Account Number:** {account_number}")
        st.write(f"**Type:** {account_type}")
        st.write("**Status:** Pending Verification")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Account Status
# ---------------------------------------------------------------------

def _account_status_tab(user):
    st.subheader("Account Application Status")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_number, account_type, account_status, account_request_status
        FROM accounts WHERE user_id = %s
    """, (user["user_id"],))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No account applications found.")
        return

    data = [
        {"Account Number": r[0], "Type": r[1], "Account Status": r[2], "Request Status": r[3]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------

def _deposit_tab(user):
    st.subheader("Deposit Money")

    accounts = _get_active_accounts(user["user_id"])
    if not accounts:
        st.info("No active accounts available.")
        return

    options = {f"{a[0]} — {a[1]} (₹{a[2]:,.2f})": a[0] for a in accounts}
    choice = st.selectbox("Account", list(options.keys()), key="deposit_acc")
    account_number = options[choice]

    amount_raw = st.text_input("Amount", key="deposit_amount")
    pin = st.text_input("Transaction PIN", type="password", key="deposit_pin")

    if not st.button("Deposit", type="primary"):
        return

    amount = _parse_amount(amount_raw)
    if amount is None:
        st.error("Enter a valid positive amount.")
        return

    ok, err = _verify_pin_input(user["user_id"], pin)
    if not ok:
        st.error(err)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT balance, account_status FROM accounts WHERE account_number = %s
        """, (account_number,))
        result = cursor.fetchone()

        if not result:
            st.error("Account not found.")
            return
        if result[1] != "ACTIVE":
            st.error(f"Transaction failed! Account is {result[1]}.")
            return

        new_balance = result[0] + amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_balance, account_number))
        cursor.execute("""
            INSERT INTO transactions (account_number, transaction_type, amount, balance_after, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (account_number, "DEPOSIT", amount, new_balance, "Money Deposited"))

        conn.commit()
        st.success(f"Deposit successful! New balance: ₹{new_balance:,.2f}")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------

def _withdraw_tab(user):
    st.subheader("Withdraw Money")

    accounts = _get_active_accounts(user["user_id"])
    if not accounts:
        st.info("No active accounts available.")
        return

    options = {f"{a[0]} — {a[1]} (₹{a[2]:,.2f})": a[0] for a in accounts}
    choice = st.selectbox("Account", list(options.keys()), key="withdraw_acc")
    account_number = options[choice]

    amount_raw = st.text_input("Amount", key="withdraw_amount")
    pin = st.text_input("Transaction PIN", type="password", key="withdraw_pin")

    if not st.button("Withdraw", type="primary"):
        return

    amount = _parse_amount(amount_raw)
    if amount is None:
        st.error("Enter a valid positive amount.")
        return

    ok, err = _verify_pin_input(user["user_id"], pin)
    if not ok:
        st.error(err)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT balance, account_status FROM accounts WHERE account_number = %s
        """, (account_number,))
        result = cursor.fetchone()

        if not result:
            st.error("Account not found.")
            return
        if result[1] != "ACTIVE":
            st.error(f"Transaction failed! Account is {result[1]}.")
            return

        current_balance = result[0]
        if amount > current_balance:
            st.error("Insufficient funds.")
            return

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE account_number = %s AND transaction_type = 'WITHDRAW' AND DATE(transaction_time) = CURDATE()
        """, (account_number,))
        todays_total = Decimal(str(cursor.fetchone()[0]))

        if todays_total + amount > DAILY_WITHDRAWAL_LIMIT:
            remaining = max(DAILY_WITHDRAWAL_LIMIT - todays_total, Decimal("0.00"))
            st.error(
                f"Daily withdrawal limit exceeded! Limit: ₹{DAILY_WITHDRAWAL_LIMIT} | "
                f"Already withdrawn today: ₹{todays_total} | You can withdraw up to ₹{remaining} more today."
            )
            return

        new_balance = current_balance - amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_balance, account_number))
        cursor.execute("""
            INSERT INTO transactions (account_number, transaction_type, amount, balance_after, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (account_number, "WITHDRAW", amount, new_balance, "Money Withdrawn"))

        conn.commit()
        st.success(f"Withdrawal successful! New balance: ₹{new_balance:,.2f}")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------

def _transfer_tab(user):
    st.subheader("Transfer Money")

    accounts = _get_active_accounts(user["user_id"])
    if not accounts:
        st.info("No active accounts available.")
        return

    options = {f"{a[0]} — {a[1]} (₹{a[2]:,.2f})": a[0] for a in accounts}
    choice = st.selectbox("From Account", list(options.keys()), key="transfer_from")
    from_account = options[choice]

    to_account = st.text_input("Receiver Account Number", key="transfer_to")
    amount_raw = st.text_input("Amount", key="transfer_amount")
    pin = st.text_input("Transaction PIN", type="password", key="transfer_pin")

    if not st.button("Transfer", type="primary"):
        return

    amount = _parse_amount(amount_raw)
    if amount is None:
        st.error("Enter a valid positive amount.")
        return

    if not to_account.strip():
        st.error("Enter a receiver account number.")
        return

    ok, err = _verify_pin_input(user["user_id"], pin)
    if not ok:
        st.error(err)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT balance, account_status FROM accounts WHERE account_number = %s", (from_account,))
        sender = cursor.fetchone()

        cursor.execute("SELECT balance, account_status FROM accounts WHERE account_number = %s", (to_account,))
        receiver = cursor.fetchone()

        if not sender:
            st.error("Sender account not found.")
            return
        if not receiver:
            st.error("Receiver account not found.")
            return
        if sender[1] != "ACTIVE":
            st.error(f"Transaction failed! Your account is {sender[1]}.")
            return
        if receiver[1] != "ACTIVE":
            st.error(f"Transaction failed! Receiver account is {receiver[1]}.")
            return

        sender_balance = sender[0]
        receiver_balance = receiver[0]

        if amount > sender_balance:
            st.error("Insufficient balance.")
            return

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE account_number = %s AND transaction_type IN ('WITHDRAW', 'TRANSFER_OUT')
            AND DATE(transaction_time) = CURDATE()
        """, (from_account,))
        todays_total = Decimal(str(cursor.fetchone()[0]))

        if todays_total + amount > DAILY_WITHDRAWAL_LIMIT:
            remaining = max(DAILY_WITHDRAWAL_LIMIT - todays_total, Decimal("0.00"))
            st.error(
                f"Daily transaction limit exceeded! Limit: ₹{DAILY_WITHDRAWAL_LIMIT} | "
                f"Already used today: ₹{todays_total} | You can send up to ₹{remaining} more today."
            )
            return

        new_sender = sender_balance - amount
        new_receiver = receiver_balance + amount

        cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_sender, from_account))
        cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_receiver, to_account))

        cursor.execute("""
            INSERT INTO transactions (account_number, transaction_type, amount, balance_after, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (from_account, "TRANSFER_OUT", amount, new_sender, "Send Money"))

        cursor.execute("""
            INSERT INTO transactions (account_number, transaction_type, amount, balance_after, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (to_account, "TRANSFER_IN", amount, new_receiver, "Received Money"))

        conn.commit()
        st.success(f"Transfer successful! ₹{amount:,.2f} sent to {to_account}.")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------

def _balance_tab(user):
    st.subheader("View Balance")

    accounts = _get_active_accounts(user["user_id"])
    if not accounts:
        st.info("No active accounts available.")
        return

    options = {f"{a[0]} — {a[1]}": a[0] for a in accounts}
    choice = st.selectbox("Account", list(options.keys()), key="balance_acc")
    account_number = options[choice]

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE account_number = %s", (account_number,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        st.metric("Current Balance", f"₹{result[0]:,.2f}")


# ---------------------------------------------------------------------
# Transaction History
# ---------------------------------------------------------------------

def _transaction_history_tab(user):
    st.subheader("Transaction History")

    accounts = _get_active_accounts(user["user_id"])
    if not accounts:
        st.info("No active accounts available.")
        return

    options = {f"{a[0]} — {a[1]}": a[0] for a in accounts}
    choice = st.selectbox("Account", list(options.keys()), key="history_acc")
    account_number = options[choice]

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT transaction_type, amount, balance_after, transaction_time
        FROM transactions WHERE account_number = %s ORDER BY transaction_time DESC
    """, (account_number,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No transactions found.")
        return

    data = [
        {"Type": r[0], "Amount": r[1], "Balance After": r[2], "Time": r[3]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Apply for Loan
# ---------------------------------------------------------------------

def _apply_loan_tab(user):
    st.subheader("Apply for Loan")

    with st.form("apply_loan_form", clear_on_submit=True):
        loan_type = st.selectbox("Loan Type", ["HOME", "CAR", "PERSONAL"])
        id_proof = st.text_input("ID Proof Number (Aadhar/PAN)")
        income_proof = st.text_input("Income Proof Number")
        amount_raw = st.text_input("Loan Amount")
        duration = st.number_input("Duration (months)", min_value=1, max_value=360, value=12, step=1)

        submitted = st.form_submit_button("Submit Application")

    if not submitted:
        return

    amount = _parse_amount(amount_raw)

    errors = []
    if not id_proof.strip():
        errors.append("ID proof number cannot be empty.")
    if not income_proof.strip():
        errors.append("Income proof number cannot be empty.")
    if amount is None:
        errors.append("Enter a valid positive loan amount.")

    if errors:
        for e in errors:
            st.error(e)
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO loans (user_id, loan_amount, loan_type, duration, id_proof, income_proof, status, admin_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user["user_id"], amount, loan_type, int(duration), id_proof, income_proof, "PENDING", "PENDING"))

        conn.commit()
        st.success("Loan application submitted!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Loan Status
# ---------------------------------------------------------------------

def _loan_status_tab(user):
    st.subheader("My Loans")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT loan_id, loan_amount, loan_type, status, remarks
        FROM loans WHERE user_id = %s
    """, (user["user_id"],))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        st.info("No loan applications found.")
        return

    data = [
        {"Loan ID": r[0], "Amount": r[1], "Type": r[2], "Status": r[3], "Remarks": r[4] or "—"}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Submit Complaint
# ---------------------------------------------------------------------

def _submit_complaint_tab(user):
    st.subheader("Submit Complaint")

    with st.form("submit_complaint_form", clear_on_submit=True):
        subject = st.text_input("Subject")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Submit")

    if not submitted:
        return

    if not subject.strip() or not description.strip():
        st.error("Subject and description cannot be empty.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO complaints (user_id, subject, description, status)
            VALUES (%s, %s, %s, %s)
        """, (user["user_id"], subject, description, "OPEN"))

        conn.commit()
        st.success("Complaint submitted!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------

def _notifications_tab(user):
    st.subheader("Notifications")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT notification_id, message, is_read, created_at
        FROM notifications WHERE user_id = %s ORDER BY created_at DESC
    """, (user["user_id"],))
    rows = cursor.fetchall()

    if not rows:
        st.info("No notifications found.")
        cursor.close()
        conn.close()
        return

    data = [
        {"Status": "🔴 NEW" if not r[2] else "✅ READ", "Message": r[1], "Time": r[3]}
        for r in rows
    ]
    st.dataframe(data, use_container_width=True, hide_index=True)

    unread_ids = [r[0] for r in rows if not r[2]]
    if unread_ids:
        placeholders = ",".join(["%s"] * len(unread_ids))
        cursor.execute(f"UPDATE notifications SET is_read = TRUE WHERE notification_id IN ({placeholders})", unread_ids)
        conn.commit()

    cursor.close()
    conn.close()


# ---------------------------------------------------------------------
# Change Password
# ---------------------------------------------------------------------

def _change_password_tab(user):
    st.subheader("Change Password")

    with st.form("change_password_form", clear_on_submit=True):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Change Password")

    if not submitted:
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT password FROM users WHERE user_id = %s", (user["user_id"],))
        result = cursor.fetchone()

        if not result:
            st.error("User not found.")
            return
        if not verify_password(old_password, result[0]):
            st.error("Incorrect current password.")
            return
        if new_password != confirm_password:
            st.error("Passwords do not match.")
            return
        if len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
            return

        hashed = hash_password(new_password)
        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed, user["user_id"]))
        conn.commit()

        st.success("Password changed successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------
# Transaction PIN — combined Set/Change based on current state
# ---------------------------------------------------------------------

def _transaction_pin_tab(user):
    st.subheader("Transaction PIN")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT transaction_pin FROM users WHERE user_id = %s", (user["user_id"],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    has_pin = bool(result and result[0])

    if not has_pin:
        st.caption("No PIN set yet — set one below to enable deposits, withdrawals, and transfers.")

        with st.form("set_pin_form", clear_on_submit=True):
            pin = st.text_input("New 4-digit PIN", type="password", max_chars=4)
            confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4)
            submitted = st.form_submit_button("Set PIN")

        if not submitted:
            return

        if not pin.isdigit() or len(pin) != 4:
            st.error("PIN must be exactly 4 digits.")
            return
        if pin != confirm_pin:
            st.error("PINs do not match.")
            return

        conn = create_connection()
        cursor = conn.cursor()
        try:
            hashed = hash_pin(pin)
            cursor.execute("UPDATE users SET transaction_pin = %s WHERE user_id = %s", (hashed, user["user_id"]))
            conn.commit()
            st.success("Transaction PIN set successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

    else:
        st.caption("A PIN is already set. Enter your current PIN to change it.")

        with st.form("change_pin_form", clear_on_submit=True):
            old_pin = st.text_input("Current PIN", type="password", max_chars=4)
            new_pin = st.text_input("New PIN", type="password", max_chars=4)
            confirm_pin = st.text_input("Confirm New PIN", type="password", max_chars=4)
            submitted = st.form_submit_button("Change PIN")

        if not submitted:
            return

        if not verify_pin(old_pin, result[0]):
            st.error("Incorrect current PIN.")
            return
        if not new_pin.isdigit() or len(new_pin) != 4:
            st.error("PIN must be exactly 4 digits.")
            return
        if new_pin != confirm_pin:
            st.error("PINs do not match.")
            return

        conn = create_connection()
        cursor = conn.cursor()
        try:
            hashed = hash_pin(new_pin)
            cursor.execute("UPDATE users SET transaction_pin = %s WHERE user_id = %s", (hashed, user["user_id"]))
            conn.commit()
            st.success("Transaction PIN changed successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()