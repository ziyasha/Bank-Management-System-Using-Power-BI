#services/manager_service.py


from database.connection import create_connection

from services.notification_service import send_notification

from utils.password_utils import hash_password

from services.loan_service import approve_loan, reject_loan

from services.complaint_service import view_complaints

from services.report_service import export_manager_reports

from services.account_service import review_pending_accounts

from utils.branches import select_branch

from utils.validators import (
    get_non_empty,
    get_valid_email,
    get_valid_phone,
    get_valid_date,
    get_valid_password,
)


def get_user_branch(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT branch FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else None


def view_staff(user_id):
    print("\n--- View Staff ---")

    branch = get_user_branch(user_id)

    scope = input(f"View (1) My Branch [{branch}] Only or (2) All Branches: ")

    conn = create_connection()
    cursor = conn.cursor()

    if scope == "2":
        cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 2 AND status = 'ACTIVE'""")
    else:
        cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 2 AND status = 'ACTIVE' AND branch = %s""", (branch,))

    staff = cursor.fetchall()


    if not staff:
        print("\nNo Staff Found.")

    else:
        for s in staff:
            print(f"""ID: ST{s[0]} 
            Name: {s[1]}
            Email: {s[2]}
            Phone: {s[3]}
            Status: {s[4]}
            Branch: {s[5]}
            ------------------------------------------""")


    cursor.close()
    conn.close()





def view_users(user_id):
    print("\n--- View Users ---")

    branch = get_user_branch(user_id)

    scope = input(f"View (1) My Branch [{branch}] Only or (2) All Branches: ")

    conn = create_connection()
    cursor = conn.cursor()

    if scope == "2":
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users
            WHERE role_id = 3 AND status = 'ACTIVE'
        """)
    else:
        cursor.execute("""
            SELECT user_id, full_name, email, phone, status, branch
            FROM users
            WHERE role_id = 3 AND status = 'ACTIVE' AND branch = %s
        """, (branch,))


    users = cursor.fetchall()


    if not users:
        print("\nNo Users Found.")



    else:
        for u in users:
            print(f"""ID: CU{u[0]}
        Name: {u[1]}
        Email: {u[2]}
        Phone: {u[3]}
        Status: {u[4]}
        Branch: {u[5]}
        ----------------------""")
            

    cursor.close()
    conn.close()









def register_staff():
    print("\n--- Register Staff ---")

    full_name = get_non_empty("Name: ")
    email = get_valid_email()
    phone = get_valid_phone()
    password = get_valid_password()
    address = get_non_empty("Address: ")
    date_of_birth = get_valid_date()
    branch = select_branch()

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Phone numbers must be unique. Email is allowed to repeat.
        cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        existing_phone = cursor.fetchone()

        if existing_phone:
            print("\nThis phone number is already registered.")
            print("Please use a different phone number.")
            cursor.close()
            conn.close()
            return

        hashed = hash_password(password)
        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password, address, date_of_birth, role_id, branch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed, address, date_of_birth, 2, branch))

        conn.commit()
        print("\nStaff Registered Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()







def remove_staff():
    print("\n--- Remove Staff ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 2 AND status = 'ACTIVE'
    """)
    staff = cursor.fetchall()

    if not staff:
        print("\nNo Staff Found.")
        cursor.close()
        conn.close()
        return

    for s in staff:
        print(f"""
        ID: ST{s[0]}
        Name: {s[1]}
        Email: {s[2]}
        Phone: {s[3]}
        Status: {s[4]}
        Branch: {s[5]}
        ----------------------""")

    staff_id = input("\nEnter Staff User ID to remove (numbers only, e.g. 10): ")
    staff_id = staff_id.replace("ST", "").replace("MG", "").replace("CU", "").strip()

    try:
        cursor.execute("""
            UPDATE users
            SET status = 'REMOVED'
            WHERE user_id = %s AND role_id = 2
        """, (staff_id,))
        conn.commit()
        print("\nStaff Removed Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()








def review_verified_loans():
    print("\n--- Review Verified Loans ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.loan_id, u.full_name, u.phone,
               l.loan_amount, l.loan_type, l.duration
        FROM loans l
        JOIN users u ON l.user_id = u.user_id
        WHERE l.status = 'VERIFIED_BY_STAFF'
    """)
    loans = cursor.fetchall()

    if not loans:
        print("\nNo Verified Loans Waiting for Approval.")
        cursor.close()
        conn.close()
        return

    for loan in loans:
        print(f"""
        Loan ID: {loan[0]}
        Name: {loan[1]}
        Phone: {loan[2]}
        Amount: {loan[3]}
        Type: {loan[4]}
        Duration: {loan[5]} months
        -------------------------""")

    loan_id = input("\nEnter Loan ID: ")
    action = input("Approve or Reject (A/R): ").upper()

    if action == "A":
        approve_loan(loan_id)

        # Get user_id for notification
        conn2 = create_connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT user_id FROM loans WHERE loan_id = %s", (loan_id,))
        result = cursor2.fetchone()
        if result:
            send_notification(
                result[0],
                f"Your loan application (ID: {loan_id}) has been APPROVED!"
            )
        cursor2.close()
        conn2.close()

    elif action == "R":
        reject_loan(loan_id)

        # Get user_id for notification
        conn2 = create_connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT user_id FROM loans WHERE loan_id = %s", (loan_id,))
        result = cursor2.fetchone()
        if result:
            send_notification(
                result[0],
                f"Your loan application (ID: {loan_id}) has been REJECTED."
            )
        cursor2.close()
        conn2.close()

    else:
        print("\nInvalid option.")

    cursor.close()
    conn.close()











def track_user_activities():
    print("\n--- Track User Activities ---")


    conn = create_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            u.full_name,
            a.account_number,
            t.transaction_type,
            t.amount,
            t.balance_after,
            t.transaction_time
        From transactions t
        JOIN accounts a ON t.account_number = a.account_number
        JOIN users u ON a.user_id = u.user_id
        ORDER BY t.transaction_time DESC
        LIMIT 50""")
        

    activities = cursor.fetchall()


    if not activities:
        print("\nNo Activities Found")

    else:
        print("\n" + "-" * 70)

        for act in activities:
            print(
            f"User: {act[0]} | "
            f"Account: {act[1]} | "
            f"{act[2]} | "
            f"Amount: ₹{act[3]} | "
            f"Balance: ₹{act[4]} | "
            f"{act[5]}"
            )

        print("-" * 70)


        cursor.close()
        conn.close()









def view_staff_dashboard_summary():
    print("\n--- Staff Dashboard Summary ---")


    conn = create_connection()
    cursor = conn.cursor()



    cursor.execute("""
        SELECT user_id, full_name, phone, status
        FROM users
        WHERE role_id = 2
    """)

    staff_list = cursor.fetchall()


    if not staff_list:
        print("\nNo Staff Found.")
        cursor.close()
        conn.close()
        return
    
    for s in staff_list:
        print(f"\n Staff : ST{s[0]} | {s[1]} | {s[2]} | {s[3]}")


        cursor.execute("""
            SELECT COUNT(*) FROM loans
            WHERE status = 'VERIFIED_BY_STAFF'
        """)

        verified = cursor.fetchall()[0]


        cursor.execute("""
            SELECT COUNT(*) FROM complaints
            WHERE status = 'resolved'
        """)


        resolved = cursor.fetchall()[0]



        print(f"  Loans Verified     : {verified[0]}")
        print(f"  Complaints Resolved: {resolved[0]}")
        print("  ----------------------")


    cursor.close()
    conn.close()













def view_user_dashboard_summary():
    print("\n--- User Dashboard Summary ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.user_id, u.full_name, u.phone,
               COUNT(a.account_id) as total_accounts,
               COALESCE(SUM(a.balance), 0) as total_balance
        FROM users u
        LEFT JOIN accounts a ON u.user_id = a.user_id
        WHERE u.role_id = 3
        GROUP BY u.user_id
    """)

    users = cursor.fetchall()

    if not users:
        print("\nNo Users Found.")
    else:
        for u in users:
            print(f"""
        ID: CU{u[0]}
        Name: {u[1]}
        Phone: {u[2]}
        Total Accounts: {u[3]}
        Total Balance: ₹{u[4]}
        ----------------------""")

    cursor.close()
    conn.close()












def verify_bank_accounts(user_id):
    branch = get_user_branch(user_id)
    review_pending_accounts(branch)


def export_reports(user_id):
    branch = get_user_branch(user_id)

    scope = input(f"Export (1) My Branch [{branch}] Only or (2) All Branches: ")

    if scope == "2":
        export_manager_reports(branch=None)
    else:
        export_manager_reports(branch=branch)


def manager_dashboard(user_id):
    while True:
        print("\n" + "-"*40)
        print("\n--- Bank Manager Dashboard ---")
        print("="*40)

        print("1. View Staff")
        print("2. View Users")
        print("3. Register Staff")
        print("4. Remove Staff")
        print("5. Review Verified Loans")
        print("6. View Complaints")
        print("7. Track User Activities")
        print("8. Staff Dashboard Summary")
        print("9. User Dashboard Summary")
        print("10. Export Reports (CSV)")
        print("11. Verify Bank Accounts")
        print("12. Logout")


        choice = input("Please select an option: ")

        if choice == "1":
            view_staff(user_id)

        elif choice == "2":
            view_users(user_id)

        elif choice == "3":
            register_staff()

        elif choice == "4":
            remove_staff()

        elif choice == "5":
            review_verified_loans()

        elif choice == "6":
            view_complaints()

        elif choice == "7":
            track_user_activities()

        elif choice == "8":
            view_staff_dashboard_summary()

        elif choice == "9":
            view_user_dashboard_summary()

        elif choice == "10":
            export_reports(user_id)

        elif choice == "11":
            verify_bank_accounts(user_id)

        elif choice == "12":
            print("\nLogged Out Successfully!")
            break

        else:
            print("\nInvalid option. Please try again.")