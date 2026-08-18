# services/staff_service.py

from database.connection import create_connection

from services.notification_service import send_notification

from services.loan_service import view_loans, update_loan_status

from services.complaint_service import view_complaints, resolve_complaint

from services.loan_service import (
    view_loans,
    verify_loan
)

from services.report_service import export_customer_report

from services.account_service import review_pending_accounts

from services.bank_customer_service import enroll_bank_customer


def get_user_branch(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT branch FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else None


def search_customer(user_id):

    branch = get_user_branch(user_id)

    scope = input(f"Search (1) My Branch [{branch}] Only or (2) All Branches: ")

    conn = create_connection()
    cursor = conn.cursor()

    keyword = input("Enter Name / Account Number: ")

    print("\n--- SEARCH RESULTS ---")

    if scope == "2":
        query = """
        SELECT u.user_id, u.full_name, u.phone, a.account_number, a.account_type, a.balance, u.branch
        FROM users u
        JOIN accounts a ON u.user_id = a.user_id
        WHERE u.full_name LIKE %s OR a.account_number = %s
        """
        cursor.execute(query, (f"%{keyword}%", keyword))
    else:
        query = """
        SELECT u.user_id, u.full_name, u.phone, a.account_number, a.account_type, a.balance, u.branch
        FROM users u
        JOIN accounts a ON u.user_id = a.user_id
        WHERE (u.full_name LIKE %s OR a.account_number = %s) AND u.branch = %s
        """
        cursor.execute(query, (f"%{keyword}%", keyword, branch))

    results = cursor.fetchall()

    if results:
        print("\n--- Search Results ---")
        for row in results:
            print(f"""
            Name: {row[1]}
            Phone: {row[2]}
            Account: {row[3]}
            Type: {row[4]}
            Balance: {row[5]}
            Branch: {row[6]}
            ----------------------""")
    else:
        print("\nNo customer found.")

    cursor.close()
    conn.close()


def view_customer():
    print("\n--- View Customer ---")

    account_number = input("Enter Account Number: ")

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT u.full_name, u.email, u.phone, u.address,
           a.account_number, a.account_type, a.balance, u.branch
    FROM users u
    JOIN accounts a ON u.user_id = a.user_id
    WHERE a.account_number = %s
    """

    cursor.execute(query, (account_number,))
    data = cursor.fetchone()

    if data:
        print("\n--- Customer Details ---")
        print(f"Name: {data[0]}")
        print(f"Email: {data[1]}")
        print(f"Phone: {data[2]}")
        print(f"Address: {data[3]}")
        print(f"Account: {data[4]}")
        print(f"Type: {data[5]}")
        print(f"Balance: {data[6]}")
        print(f"Branch: {data[7]}")
    else:
        print("\nCustomer not found.")

    cursor.close()
    conn.close()




















def process_loan_application():

    view_loans()

    loan_id = input("\nEnter Loan ID: ")

    choice = input("Verify or Reject (V/R): ").upper()

    if choice == "V":

        verify_loan(loan_id)

    elif choice == "R":

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE loans
            SET status='REJECTED_BY_STAFF'
            WHERE loan_id=%s
        """, (loan_id,))

        conn.commit()

        print("\nLoan Rejected!")

        cursor.close()
        conn.close()


















def resolve_complaints():
    print("\n--- Complaints ---")

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT c.complaint_id, u.full_name, u.phone,
           c.subject, c.description, c.status
    FROM complaints c
    JOIN users u ON c.user_id = u.user_id
    WHERE c.status = 'open'
    """

    cursor.execute(query)
    complaints = cursor.fetchall()

    if complaints:
        for c in complaints:
            print(f"""
            Complaint ID: {c[0]}
            Name: {c[1]}
            Phone: {c[2]}
            Subject: {c[3]}
            Description: {c[4]}
            Status: {c[5]}
            ----------------------""")

        cid = input("\nEnter Complaint ID to resolve: ")

        cursor.execute(
            "UPDATE complaints SET status = 'resolved' WHERE complaint_id = %s",
            (cid,)
        )

        conn.commit()
        print("\nComplaint resolved!")

    else:
        print("\nNo open complaints.")

    cursor.close()
    conn.close()












def verify_bank_accounts(user_id):
    branch = get_user_branch(user_id)
    review_pending_accounts(branch)


def enroll_customer(user_id):
    branch = get_user_branch(user_id)
    enroll_bank_customer(branch)


def generate_reports():
    print("\n--- System Reports ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM accounts")
    accounts = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM accounts")
    total_balance = cursor.fetchone()[0]

    print(f"""
    Total Users: {users}
    Total Accounts: {accounts}
    Total Bank Balance: {total_balance}
    """)

    cursor.close()
    conn.close()


def export_customers(user_id):
    branch = get_user_branch(user_id)

    scope = input(f"Export (1) My Branch [{branch}] Only or (2) All Branches: ")

    if scope == "2":
        export_customer_report(branch=None)
    else:
        export_customer_report(branch=branch)


def staff_dashboard(user_id):
    while True:
        print("\n"+"-"*40)
        print("\n--- Staff Dashboard ---")
        print("="*40)

        print("1. Search Customer")
        print("2. View Customer")
        print("3. Process Loan Application")
        print("4. Resolve Complaints")
        print("5. Generate Reports")
        print("6. Verify Bank Accounts")
        print("7. Export Customer Report (CSV)")
        print("8. Enroll New Customer")
        print("9. Logout")

        choice = input("Please select an option: ")

        if choice == "1":
            search_customer(user_id)

        elif choice == "2":
            view_customer()

        elif choice == "3":
            process_loan_application()

        elif choice == "4":
            view_complaints()
            resolve_complaint()

        elif choice == "5":
            generate_reports()

        elif choice == "6":
            verify_bank_accounts(user_id)

        elif choice == "7":
            export_customers(user_id)

        elif choice == "8":
            enroll_customer(user_id)

        elif choice == "9":
            print("\nLogged Out Successfully!")
            break

        else:
            print("\n Invalid option. Please try again.")