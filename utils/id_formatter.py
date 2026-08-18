#utils/id_formatter.py


def format_user_id(user_id, role_id):
    if role_id == 1:
        return f"AD{user_id}"
    elif role_id == 2:
        return f"ST{user_id}"
    elif role_id == 3:
        return f"CU{user_id}"
    elif role_id == 4:
        return f"MG{user_id}"
    else:
        return f"US{user_id}"