# services/notification_service.py

from database.connection import create_connection


def send_notification(user_id, message):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO notifications (user_id, message)
            VALUES (%s, %s)
        """, (user_id, message))

        conn.commit()

    except Exception as e:
        print("\nNotification Error:", e)

    finally:
        cursor.close()
        conn.close()


def view_notifications(user_id):
    print("\n--- Notifications ---")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT notification_id, message, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    notifications = cursor.fetchall()

    if not notifications:
        print("\nNo Notifications Found.")
        cursor.close()
        conn.close()
        return

    unread_ids = []

    for n in notifications:
        status = "🔴 NEW" if not n[2] else "✅ READ"
        print(f"""
        [{status}]
        ID      : {n[0]}
        Message : {n[1]}
        Time    : {n[3]}
        ----------------------""")

        if not n[2]:
            unread_ids.append(n[0])

    # Mark all unread as read
    if unread_ids:
        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE notification_id IN ({})
        """.format(','.join(['%s'] * len(unread_ids))), unread_ids)

        conn.commit()
        print(f"\n{len(unread_ids)} notification(s) marked as read.")

    cursor.close()
    conn.close()


def unread_count(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM notifications
        WHERE user_id = %s AND is_read = FALSE
    """, (user_id,))

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count