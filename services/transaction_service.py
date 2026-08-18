# services/transaction_service.py

from database.connection import create_connection
from decimal import Decimal


def deposit(account_number, amount):

    conn = create_connection()
    cursor = conn.cursor()

    #step 1: Get current balance

    cursor.execute("""
        SELECT balance, account_status FROM accounts 
        WHERE account_number = %s""", (account_number,))
    result = cursor.fetchone()


    if not result:
        print("\nAccount not found.")
        cursor.close()
        conn.close()
        return
    
    if result[1] != 'ACTIVE':
        print(f"\nTransaction Failed! Account is {result[1]}.")
        print("Please contact staff for Assistance.")
        cursor.close()
        conn.close()
    
    current_balance = result[0]
    amount = Decimal(str(amount))
    new_balance = current_balance + amount

    #step 2: Update balance in accounts table

    cursor.execute(
        "UPDATE accounts SET balance = %s WHERE account_number = %s",
        (new_balance, account_number)
    )

    #step 3: Insert transaction record

    cursor.execute("""
        INSERT INTO transactions(
        account_number, transaction_type, amount, balance_after, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (account_number, "DEPOSIT", amount, new_balance, "Money Deposited"))

    conn.commit()
    print(f"\nDeposit Successful! New Balance: {new_balance}")

    cursor.close()
    conn.close()






DAILY_WITHDRAWAL_LIMIT = Decimal("50000.00")


def withdraw(account_number, amount):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT balance, account_status
        FROM accounts
        WHERE account_number = %s
    """, (account_number,))
    result = cursor.fetchone()

    if not result:
        print("\nAccount not found.")
        cursor.close()
        conn.close()
        return

    if result[1] != 'ACTIVE':
        print(f"\nTransaction failed! Account is {result[1]}.")
        print("Please contact staff for assistance.")
        cursor.close()
        conn.close()
        return

    current_balance = result[0]
    amount = Decimal(str(amount))

    if amount > current_balance:
        print("\nInsufficient funds.")
        cursor.close()
        conn.close()
        return

    # Check today's total withdrawals
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE account_number = %s
        AND transaction_type = 'WITHDRAW'
        AND DATE(transaction_time) = CURDATE()
    """, (account_number,))

    todays_total = cursor.fetchone()[0]
    todays_total = Decimal(str(todays_total))

    if todays_total + amount > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - todays_total
        if remaining < 0:
            remaining = Decimal("0.00")
        print(f"\nDaily withdrawal limit exceeded!")
        print(f"Limit: ₹{DAILY_WITHDRAWAL_LIMIT} | Already withdrawn today: ₹{todays_total}")
        print(f"You can withdraw up to ₹{remaining} more today.")
        cursor.close()
        conn.close()
        return
    
    new_balance = current_balance - amount

    cursor.execute(
        "UPDATE accounts SET balance = %s WHERE account_number = %s",
        (new_balance, account_number)
    )


    cursor.execute("""
        INSERT INTO transactions(
        account_number, transaction_type, amount, balance_after, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (account_number, "WITHDRAW", amount, new_balance, "Money Withdrawn"))


    conn.commit()
    print(f"\nWithdrawal Successful! New Balance: {new_balance}")

    cursor.close()
    conn.close()






def transfer(from_account, to_account, amount):

    conn = create_connection()
    cursor = conn.cursor()

    #Get Sender Account Balance

    cursor.execute("""
        SELECT balance, account_status FROM accounts 
        WHERE account_number = %s
        """, (from_account,))


    sender = cursor.fetchone()


    #Get Receiver Account Balance

    cursor.execute(""" 
    SELECT balance FROM accounts 
    WHERE account_number = %s""", (to_account,))


    reciever = cursor.fetchone()

    if not sender:
        print("\nSender account not found.")
        cursor.close()
        conn.close()
        return

    if not reciever:
        print("\nReceiver account not found.")
        cursor.close()
        conn.close()
        return

    if sender[1] != 'ACTIVE':
        print(f"\nTransaction failed! Your account is {sender[1]}.")
        print("Please contact staff for assistance.")
        cursor.close()
        conn.close()
        return

    if reciever[1] != 'ACTIVE':
        print(f"\nTransaction failed! Receiver account is {reciever[1]}.")
        print("Please contact staff for assistance.")
        cursor.close()
        conn.close()
        return

    
    sender_balance = sender[0]
    reciever_balance = reciever[0]

    amount = Decimal(str(amount))

    if amount > sender_balance:
        print("Insufficient balance")
        cursor.close()
        conn.close()
        return

    # Check today's total outgoing (withdraw + transfer out)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE account_number = %s
        AND transaction_type IN ('WITHDRAW', 'TRANSFER_OUT')
        AND DATE(transaction_time) = CURDATE()
    """, (from_account,))

    todays_total = cursor.fetchone()[0]
    todays_total = Decimal(str(todays_total))

    if todays_total + amount > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - todays_total
        if remaining < 0:
            remaining = Decimal("0.00")
        print(f"\nDaily transaction limit exceeded!")
        print(f"Limit: ₹{DAILY_WITHDRAWAL_LIMIT} | Already used today: ₹{todays_total}")
        print(f"You can send up to ₹{remaining} more today.")
        cursor.close()
        conn.close()
        return
    

    #Update Balance

    new_sender = sender_balance - amount
    new_reciever = reciever_balance + amount

    cursor.execute("" \
    "UPDATE accounts SET balance = %s " \
    "WHERE account_number = %s", (new_sender, from_account))


    cursor.execute("" \
    "UPDATE accounts SET balance = %s " \
    "WHERE account_number = %s",(new_reciever, to_account))
    

    # Transaction Logs

    cursor.execute("""
        INSERT INTO transactions
        (account_number, transaction_type, amount, balance_after, description)
        VALUES (%s, %s, %s, %s, %s)
    """,(from_account, "TRANSFER_OUT", amount, new_sender, "Send Money"))


    cursor.execute("""
        INSERT INTO transactions
        (account_number, transaction_type, amount, balance_after, description)
        VALUES (%s, %s, %s, %s, %s)
    """,(to_account, "TRANSFER_IN", amount, new_reciever, "Recieved Money"))
    

    conn.commit()

    print("\nTransfer Successful!")
    print(f"Transfered ₹{amount}/-")

    cursor.close()
    conn.close()



def view_transaction_history(account_number):

    conn = create_connection()

    cursor = conn.cursor()


    query = """
    SELECT transaction_type, amount, balance_after, transaction_time
    FROM transactions
    WHERE account_number = %s
    ORDER BY transaction_time DESC
    """

    cursor.execute(query, (account_number,))

    transactions = cursor.fetchall()


    if not transactions:
        
        print("\nNo Transactions Found")
        return
    

    print("\n--- Transaction History ---")
    print("-"* 70)


    for transaction in transactions:
        t_type = transaction[0]
        amount = transaction[1]
        balance = transaction[2]
        time = transaction[3]


        print(
            f"{t_type} |"
            f"{amount} |"
            f"Balance : ₹{balance} |"
            f"{time}"
        )


    cursor.close()
    conn.close()