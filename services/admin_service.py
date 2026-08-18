# services/admin_service.py

from database.connection import create_connection

from utils.password_utils import hash_password

from utils.validators import (
    get_non_empty,
    get_valid_email,
    get_valid_phone,
    get_valid_date,
    get_valid_password,
)

from services.report_service import export_all_reports

from utils.branches import select_branch






def register_manager():
    print("\n--- Register Bank Manager ---")

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

        query = """
        INSERT INTO users(
        full_name, email, phone, password, address, date_of_birth, role_id, branch)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        hashed = hash_password(password)
        cursor.execute(query, (full_name, email, phone, hashed, address, date_of_birth, 4, branch))
        conn.commit()

        print("\nManager Registered Successfully!")


    except Exception as e:
        print("\nError: ", e)


    finally:
        cursor.close()
        conn.close()









def remove_manager():
    print("\n--- Remove Manager ---")


    conn = create_connection()
    cursor = conn.cursor()



    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 4
        """)
    
    managers = cursor.fetchall()

    if not managers:
        print("\nNo Managers Found")
        cursor.close()
        conn.close()
        return  
    

    for m in managers:
        print(f"""
        ID: MG{m[0]}
        NAME: {m[1]}
        EMAIL: {m[2]}
        PHONE: {m[3]}
        STATUS: {m[4]}
        BRANCH: {m[5]}
        ---------------------------""")


    manager_id = input("\nEnter Manager User ID to remove (numbers only, e.g. 8): ")
    manager_id = manager_id.replace("MG", "").replace("ST", "").replace("CU", "").strip()


    try:
        cursor.execute("""
            UPDATE users SET status = 'REMOVED'
            WHERE user_id = %s AND role_id = 4""", (manager_id,))
        
        conn.commit()
        print("\nManager Removed Successfully!")


    except Exception as e:
        print("\nError: ", e)


    finally:
        cursor.close()
        conn.close()






def view_managers():
    print("\n--- View Managers ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, full_name, email, phone, status, branch
        FROM users
        WHERE role_id = 4 AND status = 'ACTIVE'
    """)
    managers = cursor.fetchall()

    if not managers:
        print("\nNo Managers Found.")
    else:
        for m in managers:
            print(f"""
        ID: MG{m[0]}
        Name: {m[1]}
        Email: {m[2]}
        Phone: {m[3]}
        Status: {m[4]}
        Branch: {m[5]}
        ----------------------""")

    cursor.close()
    conn.close()










def view_staff():
    print("\n--- View Staff ---")

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT user_id, full_name, email, phone, status, branch
    FROM users
    WHERE role_id = 2
    """

    cursor.execute(query)
    staff = cursor.fetchall()

    if staff:
        for s in staff:
            print(f"""
            STAFF-ID: ST{s[0]}
            Name: {s[1]}
            Email: {s[2]}
            Phone: {s[3]}
            Status: {s[4]}
            Branch: {s[5]}
            ----------------------""")
    else:
        print("\nNo staff found.")

    cursor.close()
    conn.close()


def view_customers():
    print("\n--- View Customers ---")

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT user_id, full_name, email, phone, status, branch
    FROM users
    WHERE role_id = 3
    """

    cursor.execute(query)
    customers = cursor.fetchall()

    for c in customers:
        print(f"""
        CUSTOMER-ID: CU{c[0]}
        Name: {c[1]}
        Email: {c[2]}
        Phone: {c[3]}
        Status: {c[4]}
        Branch: {c[5]}
        ----------------------""")

    cursor.close()
    conn.close()











def system_reports():
    print("\n--- System Reports ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM accounts")
    accounts = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM accounts")
    total_money = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions")
    transactions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM loans WHERE status='pending'")
    pending_loans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='open'")
    open_complaints = cursor.fetchone()[0]

    print(f"""
    TOTAL USERS: {users}
    TOTAL ACCOUNTS: {accounts}
    TOTAL MONEY: {total_money}
    TOTAL TRANSACTIONS: {transactions}
    PENDING LOANS: {pending_loans}
    OPEN COMPLAINTS: {open_complaints}
    """)

    cursor.close()
    conn.close()










def admin_dashboard():
    while True:
        print("\n"+"-"*40)
        print("\n--- Admin Dashboard ---")
        print("="*40)

        print("1. Register Manager")
        print("2. Remove Manager")
        print("3. View Managers")
        print("4. View Customers")
        print("5. System Reports")
        print("6. Export Reports (CSV for Power BI)")
        print("7. Logout")
        

        choice = input("Please select an option: ")

        if choice == "1":
            register_manager()

        elif choice == "2":
            remove_manager()

        elif choice == "3":
            view_managers()

        elif choice == "4":
            view_customers()

        elif choice == "5":
            system_reports()

        elif choice == "6":
            export_all_reports()

        elif choice == "7":
            print("\n Logged Out Successfully!")
            break
            

        else:
            print("\n Invalid option. Please try again.")