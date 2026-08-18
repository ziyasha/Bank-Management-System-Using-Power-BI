# services/customer_service.py

from utils.id_formatter import format_user_id

from utils.validators import get_valid_amount, get_valid_pin

from services.loan_service import (
    apply_loan,
    view_my_loans
)

from services.complaint_service import submit_complaint

from database.connection import create_connection

from services.account_service import (
    create_account,
    view_user_accounts,
    view_balance,
    view_account_request_status
)

from services.transaction_service import (
    deposit,
    withdraw,
    transfer,
    view_transaction_history
)

from utils.password_utils import hash_password, verify_password, hash_pin, verify_pin

from services.notification_service import view_notifications, unread_count


def select_account(accounts):
    """
    Repeatedly prompts until the user picks a valid account from the list,
    or enters 0 to cancel. Returns the account_number, or None if cancelled.
    """
    while True:
        raw = input("\nSelect Account (0 to cancel): ").strip()

        if not raw.isdigit():
            print("Please enter numbers only.")
            continue

        selected = int(raw)

        if selected == 0:
            return None

        if selected < 1 or selected > len(accounts):
            print(f"Invalid selection. Please enter a number between 1 and {len(accounts)}.")
            continue

        return accounts[selected - 1][0]


def view_profile(user_id):

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT full_name, email, phone, address, date_of_birth, status, branch
    FROM users
    WHERE user_id = %s
    """

    cursor.execute(query, (user_id,))
    user = cursor.fetchone()

    if user:
        print("\n--- Profile Details ---")
        print(f"Name: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Phone: {user[2]}")
        print(f"Address: {user[3]}")
        print(f"Date Of Birth: {user[4]}")
        print(f"Status: {user[5]}")
        print(f"Branch: {user[6]}")
        print(f"User-ID: {format_user_id(user_id, 3)}")

    else:
        print("\nUser Not Found")

    cursor.close()
    conn.close()


def change_password(user_id):
    print("\n--- Change Password ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password FROM users
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    if not result:
        print("\nUser not found.")
        cursor.close()
        conn.close()
        return

    current_hashed = result[0]

    old_password = input("Enter Current Password: ")

    if not verify_password(old_password, current_hashed):
        print("\nIncorrect current password.")
        cursor.close()
        conn.close()
        return

    new_password = input("Enter New Password: ")
    confirm_password = input("Confirm New Password: ")

    if new_password != confirm_password:
        print("\nPasswords do not match.")
        cursor.close()
        conn.close()
        return

    if len(new_password) < 6:
        print("\nPassword must be at least 6 characters.")
        cursor.close()
        conn.close()
        return

    try:
        hashed = hash_password(new_password)

        cursor.execute("""
            UPDATE users SET password = %s
            WHERE user_id = %s
        """, (hashed, user_id))

        conn.commit()
        print("\nPassword Changed Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()


def set_transaction_pin(user_id):
    print("\n--- Set Transaction PIN ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_pin FROM users
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    if result and result[0]:
        print("\nPIN already set.")
        print("Use Change PIN option to update it.")
        cursor.close()
        conn.close()
        return

    pin = get_valid_pin("Set 4-digit PIN: ")
    confirm_pin = input("Confirm PIN: ")

    if pin != confirm_pin:
        print("\nPINs do not match.")
        cursor.close()
        conn.close()
        return

    try:
        hashed = hash_pin(pin)

        cursor.execute("""
            UPDATE users SET transaction_pin = %s
            WHERE user_id = %s
        """, (hashed, user_id))

        conn.commit()
        print("\nTransaction PIN Set Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()


def change_transaction_pin(user_id):
    print("\n--- Change Transaction PIN ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_pin FROM users
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    if not result or not result[0]:
        print("\nNo PIN set yet. Please set a PIN first.")
        cursor.close()
        conn.close()
        return

    old_pin = input("Enter Current PIN: ")

    if not verify_pin(old_pin, result[0]):
        print("\nIncorrect PIN.")
        cursor.close()
        conn.close()
        return

    new_pin = get_valid_pin("Enter New PIN: ")
    confirm_pin = input("Confirm New PIN: ")

    if new_pin != confirm_pin:
        print("\nPINs do not match.")
        cursor.close()
        conn.close()
        return

    try:
        hashed = hash_pin(new_pin)

        cursor.execute("""
            UPDATE users SET transaction_pin = %s
            WHERE user_id = %s
        """, (hashed, user_id))

        conn.commit()
        print("\nTransaction PIN Changed Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()


def verify_transaction_pin(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_pin FROM users
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result or not result[0]:
        print("\nNo Transaction PIN set.")
        print("Please set a PIN before making transactions.")
        return False

    pin = input("Enter Transaction PIN: ")

    if not verify_pin(pin, result[0]):
        print("\nIncorrect PIN. Transaction cancelled.")
        return False

    return True


def customer_dashboard(user_id):
    while True:
        print("\n" + "-"*40)
        print("\n--- Customer Dashboard ---")
        print("="*40)

        # Show unread notification count
        unread = unread_count(user_id)
        if unread > 0:
            print(f"🔔 You have {unread} unread notification(s)!")

        print("1. View Profile")
        print("2. Apply for Bank Account")
        print("3. Check Account Application Status")
        print("4. Deposit Money")
        print("5. Withdraw Money")
        print("6. Transfer Money")
        print("7. View Balance")
        print("8. View Transaction History")
        print("9. Apply for Loan")
        print("10. Submit Complaint")
        print("11. View Loan Status")
        print("12. Change Password")
        print("13. Set Transaction PIN")
        print("14. Change Transaction PIN")
        print("15. View Notifications")
        print("16. Logout")

        choice = input("Please select an option: ")

        if choice == "1":
            view_profile(user_id)

        elif choice == "2":
            create_account(user_id)

        elif choice == "3":
            view_account_request_status(user_id)

        elif choice == "4":
            accounts = view_user_accounts(user_id)

            if accounts:
                account_number = select_account(accounts)
                if not account_number:
                    continue

                amount = get_valid_amount("Enter Amount: ")

                if verify_transaction_pin(user_id):
                    deposit(account_number, amount)

        elif choice == "5":
            accounts = view_user_accounts(user_id)

            if accounts:
                account_number = select_account(accounts)
                if not account_number:
                    continue

                amount = get_valid_amount("Enter Amount: ")

                if verify_transaction_pin(user_id):
                    withdraw(account_number, amount)

        elif choice == "6":
            accounts = view_user_accounts(user_id)

            if accounts:
                from_account = select_account(accounts)
                if not from_account:
                    continue

                to_account = input("Receiver Account Number: ")
                amount = get_valid_amount("Amount: ")

                if verify_transaction_pin(user_id):
                    transfer(from_account, to_account, amount)

        elif choice == "7":
            accounts = view_user_accounts(user_id)

            if accounts:
                account_number = select_account(accounts)
                if not account_number:
                    continue

                view_balance(account_number)

        elif choice == "8":
            accounts = view_user_accounts(user_id)

            if accounts:
                account_number = select_account(accounts)
                if not account_number:
                    continue

                view_transaction_history(account_number)

        elif choice == "9":
            apply_loan(user_id)

        elif choice == "10":
            submit_complaint(user_id)

        elif choice == "11":
            view_my_loans(user_id)

        elif choice == "12":
            change_password(user_id)

        elif choice == "13":
            set_transaction_pin(user_id)

        elif choice == "14":
            change_transaction_pin(user_id)

        elif choice == "15":
            view_notifications(user_id)

        elif choice == "16":
            print("\nLogged Out Successfully!")
            break

        else:
            print("\nInvalid option. Please try again.")