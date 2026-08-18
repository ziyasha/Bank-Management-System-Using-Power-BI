#main.py

from services.auth_services import (register_user, login_user, forgot_password)
from database.connection import DatabaseConnectionError


def welcome_menu():
    while True:
        print("\n"+"-"*40)
        print("\n--- Welcome to the Authentication System ---")
        print("1. Register")
        print("2. Login")
        print("3. Forgot Password")
        print("4. Exit")

        choice = input("Please select an option: ")

        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            forgot_password()
        elif choice == '4':
            print("\nThank you for using the Authentication System. Goodbye!")
            break
        else:
            print("\nInvalid option. Please try again.")


if __name__ == "__main__":
    try:
        welcome_menu()
    except DatabaseConnectionError as e:
        print(f"\n{e}")
        print("Please make sure MySQL is running and your db_config.py settings are correct.")