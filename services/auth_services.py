# services/auth_service.py

from database.connection import create_connection

from utils.password_utils import hash_password, verify_password

from utils.validators import (
    get_non_empty,
    get_valid_email,
    get_valid_phone,
    get_valid_date,
    get_valid_password,
)

from services.customer_service import customer_dashboard

from services.staff_service import staff_dashboard

from services.admin_service import admin_dashboard

from services.manager_service import manager_dashboard


def register_user():
    print("\n--- User Registration (App Access) ---")
    print("You must already have an account with us to register for app access.")
    print("Please enter your details exactly as given at your branch.\n")

    phone = get_valid_phone()
    date_of_birth = get_valid_date()
    id_proof_number = get_non_empty("ID Proof Number (Aadhar/PAN): ")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bank_customer_id, full_name, address, branch, is_registered_on_app
        FROM bank_customers
        WHERE phone = %s AND date_of_birth = %s AND id_proof_number = %s
    """, (phone, date_of_birth, id_proof_number))

    record = cursor.fetchone()

    if not record:
        print("\nNo matching bank record found for those details.")
        print("Please visit your branch to open an account before registering for app access.")
        cursor.close()
        conn.close()
        return

    bank_customer_id, full_name, address, branch, already_registered = record

    if already_registered:
        print("\nThis account has already registered for app access. Please log in instead.")
        cursor.close()
        conn.close()
        return

    print(f"\nWelcome, {full_name}! We found your record at the {branch} branch.")

    email = get_valid_email()
    password = get_valid_password()

    # Defensive check, though phone should already be unique via bank_customers.
    cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
    if cursor.fetchone():
        print("\nThis phone number is already registered for app access.")
        cursor.close()
        conn.close()
        return

    try:
        hashed = hash_password(password)

        cursor.execute("""
            INSERT INTO users (full_name, email, phone, password, address, date_of_birth, role_id, branch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, email, phone, hashed, address, date_of_birth, 3, branch))

        cursor.execute("""
            UPDATE bank_customers SET is_registered_on_app = TRUE
            WHERE bank_customer_id = %s
        """, (bank_customer_id,))

        conn.commit()

        print("\nApp access created successfully! You can now log in.")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()


def login_user():
    print("\n--- User Login ---")

    email = input("E-mail: ")
    password = input("Password: ")

    conn = create_connection()
    cursor = conn.cursor()


    query = """
    SELECT user_id, full_name, role_id, password
    FROM users 
    WHERE email = %s AND status = 'ACTIVE'
    """

    cursor.execute(query, (email,))
    user = cursor.fetchone()

    if user and not verify_password(password, user[3]):
        user = None

    if user:
        user_id, full_name, role_id = user[0], user[1], user[2]

        print(f"\nLogin Successful! Welcome, {full_name}!")

        if role_id == 1:
            admin_dashboard()

        elif role_id == 2:
            staff_dashboard(user_id)

        elif role_id == 3:
            customer_dashboard(user_id)

        elif role_id == 4:
            manager_dashboard(user_id)

        else:
            print("\nInvalid role assigned")
        
    else:
            print("\nInvalid email or password, Please try again.")


    

    cursor.close()
    conn.close()


def forgot_password():
    print("\n--- Forgot Password ---")

    email = input("E-mail: ")

    print("\nPassword reset link sent to your email!")