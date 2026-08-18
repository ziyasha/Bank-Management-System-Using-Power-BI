# utils/validators.py

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


# ---------- Pure checks (no input, just True/False) ----------

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_amount(amount_str):
    try:
        amount = Decimal(amount_str)
        return amount > 0
    except (InvalidOperation, ValueError):
        return False


def is_valid_pin(pin):
    return pin.isdigit() and len(pin) == 4


# ---------- Re-prompting input helpers ----------
# Each of these keeps asking until the user gives something valid,
# instead of crashing or silently falling through with bad data.

def get_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def get_valid_email(prompt="E-mail: "):
    while True:
        email = input(prompt).strip()
        if is_valid_email(email):
            return email
        print("Invalid email format. Example: name@example.com")


def get_valid_phone(prompt="Phone: "):
    while True:
        phone = input(prompt).strip()
        if is_valid_phone(phone):
            return phone
        print("Phone number must be exactly 10 digits.")


def get_valid_date(prompt="Date of Birth (YYYY-MM-DD): "):
    while True:
        date_str = input(prompt).strip()
        if is_valid_date(date_str):
            return date_str
        print("Invalid date. Please use YYYY-MM-DD format (e.g. 1998-05-21).")


def get_valid_password(prompt="Password: ", min_length=6):
    while True:
        password = input(prompt)
        if len(password) >= min_length:
            return password
        print(f"Password must be at least {min_length} characters.")


def get_valid_amount(prompt="Amount: "):
    while True:
        amount_str = input(prompt).strip()
        if is_valid_amount(amount_str):
            return Decimal(amount_str)
        print("Please enter a valid positive amount (e.g. 500 or 500.50).")


def get_valid_pin(prompt="Enter 4-digit PIN: "):
    while True:
        pin = input(prompt).strip()
        if is_valid_pin(pin):
            return pin
        print("PIN must be exactly 4 digits.")


def get_valid_choice(prompt, valid_choices):
    """valid_choices: iterable of uppercase strings, e.g. ['A', 'R']"""
    while True:
        choice = input(prompt).strip().upper()
        if choice in valid_choices:
            return choice
        print(f"Invalid option. Please choose one of: {', '.join(valid_choices)}")


def get_valid_int(prompt, min_value=None, max_value=None):
    while True:
        raw = input(prompt).strip()
        if not raw.lstrip("-").isdigit():
            print("Please enter a whole number.")
            continue
        value = int(raw)
        if min_value is not None and value < min_value:
            print(f"Value must be at least {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Value must be at most {max_value}.")
            continue
        return value