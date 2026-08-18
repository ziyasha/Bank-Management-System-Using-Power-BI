# services/bank_customer_service.py
#
# This represents the "counter" side of onboarding: staff manually enter
# a customer's details after verifying their KYC documents in person.
# The customer can only self-register for app access afterwards, and
# only if their details match a record created here.

from database.connection import create_connection

from utils.validators import get_non_empty, get_valid_phone, get_valid_date


def enroll_bank_customer(branch):
    """
    branch: the enrolling staff/manager's own branch. New customers are
    always enrolled under the branch of the staff member handling them.
    """
    print("\n--- Enroll New Bank Customer ---")
    print(f"Branch: {branch}")

    full_name = get_non_empty("Customer Full Name: ")
    phone = get_valid_phone()
    date_of_birth = get_valid_date()
    id_proof_number = get_non_empty("ID Proof Number (Aadhar/PAN): ")
    address = get_non_empty("Address: ")

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT bank_customer_id FROM bank_customers
            WHERE phone = %s OR id_proof_number = %s
        """, (phone, id_proof_number))

        existing = cursor.fetchone()

        if existing:
            print("\nA customer record with this phone or ID proof already exists.")
            cursor.close()
            conn.close()
            return

        cursor.execute("""
            INSERT INTO bank_customers
            (full_name, phone, date_of_birth, id_proof_number, address, branch, is_registered_on_app)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
        """, (full_name, phone, date_of_birth, id_proof_number, address, branch))

        conn.commit()

        print(f"\nCustomer enrolled successfully under {branch} branch.")
        print("They can now self-register for app access using their phone, date of birth, and ID proof.")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()