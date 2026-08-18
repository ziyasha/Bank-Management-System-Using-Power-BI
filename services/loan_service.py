#services/loan_service.py



from database.connection import create_connection
from decimal import Decimal
from utils.validators import get_non_empty, get_valid_amount, get_valid_int, get_valid_choice

def apply_loan(user_id):
    print("\n--- Apply Loan ---")

    loan_type = get_valid_choice("Loan Type (HOME/CAR/PERSONAL): ", ["HOME", "CAR", "PERSONAL"])
    id_proof = get_non_empty("ID Proof Number (Aadhar/PAN): ")
    income_proof = get_non_empty("Income Proof Number: ")
    amount = get_valid_amount("Loan Amount: ")
    duration = get_valid_int("Duration (months): ", min_value=1, max_value=360)

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO loans (user_id, loan_amount, loan_type,
    duration, id_proof, income_proof, status, admin_status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
    query,
    (
        user_id,
        amount,
        loan_type,
        duration,
        id_proof,
        income_proof,
        "PENDING",
        "PENDING"
    ))
    conn.commit()

    print("\nLoan Application Submitted!")

    cursor.close()
    conn.close()











def view_loans():

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT
    l.loan_id,
    u.full_name,
    u.phone,
    u.address,
    MAX(a.balance) as balance,
    l.loan_amount,
    l.loan_type,
    l.duration,
    l.id_proof,
    l.income_proof,
    l.status
    FROM loans l
    JOIN users u ON l.user_id = u.user_id
    LEFT JOIN accounts a ON u.user_id = a.user_id
    GROUP BY l.loan_id, u.full_name, u.phone, u.address,
             l.loan_amount, l.loan_type, l.duration,
             l.id_proof, l.income_proof, l.status
    """

    cursor.execute(query)

    loans = cursor.fetchall()

    for loan in loans:

        print(f"""
        Loan ID: {loan[0]}

        Customer Name: {loan[1]}
        Phone: {loan[2]}
        Address: {loan[3]}
        Account Balance: {loan[4]}

        Loan Amount: {loan[5]}
        Loan Type: {loan[6]}
        Duration: {loan[7]} months

        ID Proof: {loan[8]}
        Income Proof: {loan[9]}

        Status: {loan[10]}
        ----------------------------------------
        """)

    cursor.close()
    conn.close()










def view_customer_transactions(user_id):

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        t.transaction_type,
        t.amount,
        t.balance_after,
        t.transaction_date
    FROM transactions t
    JOIN accounts a
        ON t.account_number = a.account_number
    WHERE a.user_id = %s
    ORDER BY transaction_date DESC
    """

    cursor.execute(query, (user_id,))

    transactions = cursor.fetchall()

    print("\n--- Transaction History ---")

    for t in transactions:

        print(f"""
        Type: {t[0]}
        Amount: {t[1]}
        Balance After: {t[2]}
        Date: {t[3]}
        -----------------------
        """)

    cursor.close()
    conn.close()











def verify_loan(loan_id):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE loans
        SET
        status='VERIFIED_BY_STAFF',
        remarks='Documents verified. Waiting for Admin approval.'
        WHERE loan_id = %s
        """, (loan_id,))

    conn.commit()

    print("\nDocuments Verified Successfully!")
    print("Waiting for Admin Approval.")

    cursor.close()
    conn.close()






def update_loan_status():
    loan_id = input("Enter Loan ID: ")
    status = input("Approve/Reject: ").upper()

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    UPDATE loans
    SET status = %s
    WHERE loan_id = %s
    """

    cursor.execute(query, (status, loan_id))
    conn.commit()

    print("\nLoan Updated!")

    cursor.close()
    conn.close()


















def approve_loan(loan_id):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE loans
        SET
            status='APPROVED_BY_ADMIN',
            admin_status='APPROVED',
            remarks='Approved by Admin'
        WHERE loan_id=%s
    """, (loan_id,))

    conn.commit()

    print("\nLoan Approved Successfully!")

    cursor.close()
    conn.close()















def reject_loan(loan_id):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE loans
        SET
            status='REJECTED_BY_ADMIN',
            admin_status='REJECTED',
            remarks='Rejected by Admin'
        WHERE loan_id=%s
    """, (loan_id,))

    conn.commit()

    print("\nLoan Rejected!")

    cursor.close()
    conn.close()














# def reject_loan(loan_id):
#     conn = create_connection()
#     cursor = conn.cursor()

#     cursor.execute("""
#         UPDATE loans
#         SET status = 'REJECTED'
#         WHERE loan_id = %s
#     """, (loan_id,))

#     conn.commit()

#     print("\nLoan Rejected!")

#     cursor.close()
#     conn.close()









def view_my_loans(user_id):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            loan_id,
            loan_amount,
            loan_type,
            status,
            remarks
        FROM loans
        WHERE user_id=%s
    """, (user_id,))

    loans = cursor.fetchall()

    print("\n--- My Loans ---")

    for loan in loans:

        print(f"""
        Loan ID: {loan[0]}
        Amount: {loan[1]}
        Type: {loan[2]}
        Status: {loan[3]}
        Remarks: {loan[4]}
        -------------------------
        """)

    cursor.close()
    conn.close()