#services/complaint_services.py

from database.connection import create_connection

from services.notification_service import send_notification




def submit_complaint(user_id):
    print("\n--- Submit Complaint ---")

    subject = input("Subject: ")
    description = input("Description: ")

    conn = create_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO complaints (user_id, subject, description, status)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (user_id, subject, description, "OPEN"))
    conn.commit()

    print("\nComplaint Submitted!")

    cursor.close()
    conn.close()







def view_complaints():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT complaint_id, user_id, subject,
               description, status, created_at, resolved_on
        FROM complaints
    """)

    complaints = cursor.fetchall()

    if not complaints:
        print("\nNo Complaints Found.")
    else:
        for c in complaints:
            resolved = c[6] if c[6] else "Not Resolved Yet"
            print(f"""
            Complaint ID : {c[0]}
            User ID      : CU{c[1]}
            Subject      : {c[2]}
            Description  : {c[3]}
            Status       : {c[4]}
            Submitted On : {c[5]}
            Resolved On  : {resolved}
            ----------------------""")

    cursor.close()
    conn.close()










def resolve_complaint():
    complaint_id = input("Enter Complaint ID: ")

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE complaints
            SET status = 'RESOLVED',
                resolved_on = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
        """, (complaint_id,))

        conn.commit()

        if cursor.rowcount == 0:
            print("\nComplaint ID not found.")
        else:
            # Get user_id for notification
            cursor.execute("""
                SELECT user_id FROM complaints
                WHERE complaint_id = %s
            """, (complaint_id,))
            result = cursor.fetchone()

            if result:
                send_notification(
                    result[0],
                    f"Your complaint (ID: {complaint_id}) has been resolved!"
                )

            print("\nComplaint Resolved Successfully!")

    except Exception as e:
        print("\nError:", e)

    finally:
        cursor.close()
        conn.close()