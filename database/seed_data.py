# database/seed_data.py
#
# WARNING: This DELETES ALL EXISTING DATA in every table and replaces it
# with a fixed set of realistic test data. Do not run this against a
# database you actually care about.
#
# Run with:  python -m database.seed_data
# (run from the project root, so the `services`/`utils`/`database` imports resolve)

from database.connection import create_connection
from utils.password_utils import hash_password, hash_pin

DEFAULT_PASSWORD = "Test@1234"   # login password for every seeded user
DEFAULT_PIN = "1234"             # transaction PIN for every seeded customer

BRANCHES = [
    "Koramangala",
    "Indiranagar",
    "Whitefield",
    "MG Road",
    "Jayanagar",
    "Electronic City",
]


def wipe_all_tables(cursor):
    print("Wiping existing data...")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables = [
        "notifications",
        "transactions",
        "complaints",
        "loans",
        "accounts",
        "bank_customers",
        "users",
    ]

    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("All tables cleared.\n")


def seed_users(cursor):
    print("Seeding users (admin, managers, staff, customers)...")

    hashed_pw = hash_password(DEFAULT_PASSWORD)

    users = []

    # role_id: 1 = admin, 2 = staff, 3 = customer, 4 = manager

    # --- Admin (1) ---
    users.append(("Ravi Shankar", "admin@electrobank.com", "9900000001", hashed_pw,
                   "12 MG Road, Bengaluru", "1985-04-12", 1, "MG Road"))

    # --- Managers (3) ---
    users.append(("Anita Rao", "anita.rao@electrobank.com", "9900000011", hashed_pw,
                   "45 Koramangala 4th Block, Bengaluru", "1980-06-23", 4, "Koramangala"))
    users.append(("Suresh Iyer", "suresh.iyer@electrobank.com", "9900000012", hashed_pw,
                   "22 Indiranagar 100ft Road, Bengaluru", "1979-11-05", 4, "Indiranagar"))
    users.append(("Meera Nair", "meera.nair@electrobank.com", "9900000013", hashed_pw,
                   "8 Whitefield Main Road, Bengaluru", "1982-02-17", 4, "Whitefield"))

    # --- Staff (5) ---
    users.append(("Kiran Kumar", "kiran.kumar@electrobank.com", "9900000021", hashed_pw,
                   "3 Koramangala 5th Block, Bengaluru", "1992-09-14", 2, "Koramangala"))
    users.append(("Divya Prasad", "divya.prasad@electrobank.com", "9900000022", hashed_pw,
                   "17 Koramangala 6th Block, Bengaluru", "1993-01-29", 2, "Koramangala"))
    users.append(("Arjun Reddy", "arjun.reddy@electrobank.com", "9900000023", hashed_pw,
                   "9 Indiranagar 12th Main, Bengaluru", "1990-07-08", 2, "Indiranagar"))
    users.append(("Sneha Gowda", "sneha.gowda@electrobank.com", "9900000024", hashed_pw,
                   "31 Indiranagar 2nd Stage, Bengaluru", "1991-03-22", 2, "Indiranagar"))
    users.append(("Manoj Pillai", "manoj.pillai@electrobank.com", "9900000025", hashed_pw,
                   "14 Whitefield ITPL Road, Bengaluru", "1989-12-01", 2, "Whitefield"))

    # --- Customers (10), spread across the same 3 branches so staff/manager
    # scoping is actually exercised ---
    customers = [
        ("Priya Sharma", "priya.sharma@gmail.com", "9900000101", "22 5th Cross, Koramangala, Bengaluru", "1995-05-11", "Koramangala"),
        ("Rahul Verma", "rahul.verma@gmail.com", "9900000102", "10 8th Main, Koramangala, Bengaluru", "1990-08-19", "Koramangala"),
        ("Ayesha Khan", "ayesha.khan@gmail.com", "9900000103", "5 100ft Road, Indiranagar, Bengaluru", "1993-02-27", "Indiranagar"),
        ("Vikram Singh", "vikram.singh@gmail.com", "9900000104", "19 12th Main, Indiranagar, Bengaluru", "1988-10-03", "Indiranagar"),
        ("Neha Joshi", "neha.joshi@gmail.com", "9900000105", "7 ITPL Main Road, Whitefield, Bengaluru", "1996-06-30", "Whitefield"),
        ("Karthik Nair", "karthik.nair@gmail.com", "9900000106", "45 Hope Farm, Whitefield, Bengaluru", "1991-01-15", "Whitefield"),
        ("Fatima Sheikh", "fatima.sheikh@gmail.com", "9900000107", "3 6th Block, Koramangala, Bengaluru", "1994-11-08", "Koramangala"),
        ("Deepak Mehta", "deepak.mehta@gmail.com", "9900000108", "27 2nd Stage, Indiranagar, Bengaluru", "1987-04-25", "Indiranagar"),
        ("Sanjana Rao", "sanjana.rao@gmail.com", "9900000109", "11 Varthur Road, Whitefield, Bengaluru", "1992-09-09", "Whitefield"),
        ("Amitabh Das", "amitabh.das@gmail.com", "9900000110", "33 Forum Mall Road, Koramangala, Bengaluru", "1985-07-20", "Koramangala"),
    ]

    for full_name, email, phone, address, dob, branch in customers:
        users.append((full_name, email, phone, hashed_pw, address, dob, 3, branch))

    query = """
        INSERT INTO users
        (full_name, email, phone, password, address, date_of_birth, role_id, branch)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, users)

    print(f"Inserted {len(users)} users.\n")

    return customers


def seed_bank_customers(cursor, matched_customers):
    print("Seeding bank_customers (branch KYC / enrollment records)...")

    rows = []

    # 10 records that match the 10 app-registered customers exactly
    # (same phone/DOB) and are marked as already claimed.
    id_proofs = [
        "234567890111", "234567890112", "234567890113", "234567890114",
        "234567890115", "234567890116", "234567890117", "234567890118",
        "234567890119", "234567890120",
    ]

    for (full_name, email, phone, address, dob, branch), id_proof in zip(matched_customers, id_proofs):
        rows.append((full_name, phone, dob, id_proof, address, branch, True))

    # 3 more who've been enrolled at the branch but have NOT self-registered
    # on the app yet — use these to test the "first-time app registration" flow.
    unclaimed = [
        ("Pooja Iyer", "9900000201", "1994-03-18", "234567890201", "8 Jayanagar 4th Block, Bengaluru", "Jayanagar", False),
        ("Rohan Kapoor", "9900000202", "1990-12-05", "234567890202", "14 Electronic City Phase 1, Bengaluru", "Electronic City", False),
        ("Lakshmi Menon", "9900000203", "1996-08-27", "234567890203", "21 Jayanagar 9th Block, Bengaluru", "Jayanagar", False),
    ]

    rows.extend(unclaimed)

    query = """
        INSERT INTO bank_customers
        (full_name, phone, date_of_birth, id_proof_number, address, branch, is_registered_on_app)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, rows)

    print(f"Inserted {len(rows)} bank_customers ({len(matched_customers)} claimed, {len(unclaimed)} unclaimed).\n")

    return unclaimed


def seed_accounts(cursor):
    print("Seeding accounts...")

    cursor.execute("SELECT user_id FROM users WHERE role_id = 3 ORDER BY user_id")
    customer_ids = [r[0] for r in cursor.fetchall()]

    balances = [15000.00, 8500.00, 42000.00, 3200.00, 67500.00,
                12000.00, 5400.00, 91000.00, 27600.00, 1500.00]

    accounts = []
    for i, (user_id, balance) in enumerate(zip(customer_ids, balances), start=1):
        acc_number = f"AC{20000000 + i}"
        accounts.append((user_id, acc_number, "SAVINGS", balance, "ACTIVE", "APPROVED", True))

    query = """
        INSERT INTO accounts
        (user_id, account_number, account_type, balance,
        account_status, account_request_status, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, accounts)

    print(f"Inserted {len(accounts)} accounts.\n")

    # Return (account_number, balance) pairs for transactions to reference
    return [(a[1], a[3]) for a in accounts]


def seed_transactions(cursor, account_info):
    print("Seeding transactions...")

    types_and_amounts = [
        ("DEPOSIT", 5000.00), ("DEPOSIT", 2000.00), ("WITHDRAW", 1000.00),
        ("DEPOSIT", 7500.00), ("WITHDRAW", 2500.00), ("DEPOSIT", 3000.00),
        ("TRANSFER_OUT", 1500.00), ("TRANSFER_IN", 1500.00),
    ]

    rows = []
    for (t_type, amount), (acc_number, balance) in zip(types_and_amounts, account_info):
        rows.append((acc_number, t_type, amount, balance, f"{t_type.title()} - seed data"))

    query = """
        INSERT INTO transactions
        (account_number, transaction_type, amount, balance_after, description)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.executemany(query, rows)

    print(f"Inserted {len(rows)} transactions.\n")


def seed_loans(cursor):
    print("Seeding loans...")

    cursor.execute("SELECT user_id FROM users WHERE role_id = 3 ORDER BY user_id LIMIT 5")
    customer_ids = [r[0] for r in cursor.fetchall()]

    loan_data = [
        ("HOME", 2500000.00, 240, "PAN1234A", "SAL0099A", "PENDING", "PENDING"),
        ("CAR", 800000.00, 60, "PAN2234B", "SAL0199B", "VERIFIED_BY_STAFF", "PENDING"),
        ("PERSONAL", 150000.00, 24, "PAN3234C", "SAL0299C", "APPROVED_BY_ADMIN", "APPROVED"),
        ("PERSONAL", 100000.00, 12, "PAN4234D", "SAL0399D", "REJECTED_BY_ADMIN", "REJECTED"),
        ("CAR", 600000.00, 48, "PAN5234E", "SAL0499E", "PENDING", "PENDING"),
    ]

    rows = []
    for user_id, (loan_type, amount, duration, id_proof, income_proof, status, admin_status) in zip(customer_ids, loan_data):
        rows.append((user_id, amount, loan_type, duration, id_proof, income_proof, status, admin_status))

    query = """
        INSERT INTO loans
        (user_id, loan_amount, loan_type, duration, id_proof, income_proof, status, admin_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, rows)

    print(f"Inserted {len(rows)} loans.\n")


def seed_complaints(cursor):
    print("Seeding complaints...")

    cursor.execute("SELECT user_id FROM users WHERE role_id = 3 ORDER BY user_id LIMIT 3")
    customer_ids = [r[0] for r in cursor.fetchall()]

    complaint_data = [
        ("ATM Card Not Working", "My debit card was declined twice at the ATM near Koramangala.", "OPEN"),
        ("Wrong Balance Shown", "The app shows a different balance than my passbook.", "OPEN"),
        ("Delayed Loan Approval", "My personal loan application has been pending for 3 weeks.", "resolved"),
    ]

    rows = []
    for user_id, (subject, desc, status) in zip(customer_ids, complaint_data):
        rows.append((user_id, subject, desc, status))

    query = """
        INSERT INTO complaints (user_id, subject, description, status)
        VALUES (%s, %s, %s, %s)
    """
    cursor.executemany(query, rows)

    print(f"Inserted {len(rows)} complaints.\n")


def seed_notifications(cursor):
    print("Seeding notifications...")

    cursor.execute("SELECT user_id FROM users WHERE role_id = 3 ORDER BY user_id LIMIT 2")
    customer_ids = [r[0] for r in cursor.fetchall()]

    messages = [
        "Your account AC20000001 has been verified and activated!",
        "Your loan application has been APPROVED!",
    ]

    rows = list(zip(customer_ids, messages))

    query = """
        INSERT INTO notifications (user_id, message)
        VALUES (%s, %s)
    """
    cursor.executemany(query, rows)

    print(f"Inserted {len(rows)} notifications.\n")


def seed_transaction_pins(cursor):
    print("Setting a default transaction PIN for all customers...")

    hashed_pin = hash_pin(DEFAULT_PIN)
    cursor.execute("UPDATE users SET transaction_pin = %s WHERE role_id = 3", (hashed_pin,))

    print("Done.\n")


def main():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        wipe_all_tables(cursor)
        conn.commit()

        matched_customers = seed_users(cursor)
        conn.commit()

        unclaimed = seed_bank_customers(cursor, matched_customers)
        conn.commit()

        account_info = seed_accounts(cursor)
        conn.commit()

        seed_transactions(cursor, account_info)
        conn.commit()

        seed_loans(cursor)
        conn.commit()

        seed_complaints(cursor)
        conn.commit()

        seed_notifications(cursor)
        conn.commit()

        seed_transaction_pins(cursor)
        conn.commit()

        total = 19 + 13 + 10 + 8 + 5 + 3 + 2
        print("=" * 55)
        print(f"Seed complete! ~{total} rows inserted across 7 tables.")
        print("=" * 55)

        print(f"\nLogin password for every seeded user : {DEFAULT_PASSWORD}")
        print(f"Transaction PIN for every seeded customer: {DEFAULT_PIN}")

        print("\nTry logging in as:")
        print("  Admin    : admin@electrobank.com")
        print("  Manager  : anita.rao@electrobank.com   (Koramangala)")
        print("  Staff    : kiran.kumar@electrobank.com (Koramangala)")
        print("  Customer : priya.sharma@gmail.com      (Koramangala)")

        u = unclaimed[0]
        print("\nTo test first-time self-registration (unclaimed bank_customers record):")
        print(f"  Phone: {u[1]} | DOB: {u[2]} | ID Proof: {u[3]}  ({u[0]}, {u[5]} branch)")

    except Exception as e:
        conn.rollback()
        print("\nSeeding failed:", e)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()