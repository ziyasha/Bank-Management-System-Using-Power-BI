# services/account_service.py

from database.connection import create_connection
from services.notification_service import send_notification
import random


def generate_account_number():
    return "AC" + str(random.randint(10000000, 99999999))


def create_account(user_id):
    print("\n--- Apply for Bank Account ---")

    account_type = input("Account Type (SAVINGS/CURRENT): ").upper()

    # Validation
    if account_type not in ["SAVINGS", "CURRENT"]:
        print("\nInvalid Account Type")
        return

    account_number = generate_account_number()

    conn = create_connection()
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO accounts
        (user_id, account_number, account_type, balance,
        account_status, account_request_status, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            user_id,
            account_number,
            account_type,
            0.00,           # Initial balance
            "INACTIVE",     # Account is inactive until verified
            "PENDING",      # Needs staff verification
            False           # Not verified yet
        )

        cursor.execute(query, values)
        conn.commit()

        print("\nBank Account Application Submitted!")
        print(f"Account Number  : {account_number}")
        print(f"Type            : {account_type}")
        print(f"Status          : Pending Verification")
        print("\nPlease wait for staff to verify your account.")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()




def view_user_accounts(user_id):

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT account_number, account_type, balance,
    account_status, account_request_status
    FROM accounts
    WHERE user_id = %s
    """

    cursor.execute(query,(user_id,))
    accounts = cursor.fetchall()

    if not accounts:
        print("\nNo Bank Accounts Found")
        return[]
    
    print("\n--- Your Accounts ---")


    for index, account in enumerate(accounts, start=1):
        account_number = account[0]
        account_type = account[1]
        balance = account[2]
        account_status = account[3]
        request_status = account[4]

        print(
            f"{index}. "
            f"{account_number} | "
            f"{account_type} | "
            f"₹{balance} | "
            f"{account_status} | "
            f"Verification: {request_status}"
        )


    cursor.close()
    conn.close()


    return accounts



def view_balance(account_number):

    conn = create_connection()
    cursor = conn.cursor()


    query = """
    SELECT balance FROM accounts 
    WHERE account_number = %s
    """


    cursor.execute(query,(account_number,))
    result = cursor.fetchone()

    if result:
        print(f"\nCurrent Balance: ₹{result[0]}")

    else:
        print("\nAccount not Found")


    cursor.close()
    conn.close()











def view_account_request_status(user_id):
    print("\n--- Account Application Status ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT account_number, account_type,
               account_status, account_request_status
        FROM accounts
        WHERE user_id = %s
    """, (user_id,))

    accounts = cursor.fetchall()

    if not accounts:
        print("\nNo Account Applications Found.")
    else:
        for acc in accounts:
            print(f"""
        Account Number  : {acc[0]}
        Type            : {acc[1]}
        Account Status  : {acc[2]}
        Request Status  : {acc[3]}
        ----------------------""")

    cursor.close()
    conn.close()


def review_pending_accounts(branch):
    """
    Shows and lets staff/manager act on PENDING account requests —
    but only for customers in their own branch. A staff or manager
    from a different branch will never see this customer's request.
    """
    print("\n--- Pending Bank Account Verification ---")
    print(f"(Branch: {branch})")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.account_id, u.full_name, u.phone,
               a.account_number, a.account_type,
               a.account_request_status
        FROM accounts a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.account_request_status = 'PENDING' AND u.branch = %s
    """, (branch,))

    accounts = cursor.fetchall()

    if not accounts:
        print("\nNo Pending Account Verification for your branch.")
        cursor.close()
        conn.close()
        return

    for acc in accounts:
        print(f"""
        Account ID  : {acc[0]}
        Name        : {acc[1]}
        Phone       : {acc[2]}
        Acc Number  : {acc[3]}
        Type        : {acc[4]}
        Status      : {acc[5]}
        ----------------------""")

    account_number = input("\nEnter Account Number to verify: ")
    action = input("Approve or Reject (A/R): ").upper()

    # Re-check branch ownership right before acting, in case the account
    # number was typed for something outside this branch.
    cursor.execute("""
        SELECT u.branch FROM accounts a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.account_number = %s
    """, (account_number,))
    owner = cursor.fetchone()

    if not owner:
        print("\nAccount not found.")
        cursor.close()
        conn.close()
        return

    if owner[0] != branch:
        print("\nThat account belongs to a different branch. You cannot act on this request.")
        cursor.close()
        conn.close()
        return

    try:
        if action == "A":
            cursor.execute("""
                UPDATE accounts
                SET account_request_status = 'APPROVED',
                    account_status = 'ACTIVE',
                    is_verified = 1
                WHERE account_number = %s
            """, (account_number,))
            conn.commit()

            cursor.execute("SELECT user_id FROM accounts WHERE account_number = %s", (account_number,))
            result = cursor.fetchone()

            if result:
                send_notification(
                    result[0],
                    f"Your account {account_number} has been verified and activated!"
                )

            print("\nAccount Verified & Activated Successfully!")

        elif action == "R":
            cursor.execute("""
                UPDATE accounts
                SET account_request_status = 'REJECTED',
                    account_status = 'REJECTED',
                    is_verified = 0
                WHERE account_number = %s
            """, (account_number,))
            conn.commit()

            cursor.execute("SELECT user_id FROM accounts WHERE account_number = %s", (account_number,))
            result = cursor.fetchone()

            if result:
                send_notification(
                    result[0],
                    f"Your account {account_number} application was rejected. Please contact staff."
                )

            print("\nAccount Rejected!")

        else:
            print("\nInvalid Option.")

    except Exception as e:
        print("\nError: ", e)

    finally:
        cursor.close()
        conn.close()