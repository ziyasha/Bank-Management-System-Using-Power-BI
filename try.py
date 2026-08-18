# use if you forgot password and not able to see in MySQL workbench, you can use this code to generate hashed password and pin for your new password and PIN. Then you can update your password and PIN in MySQL workbench
# use this query in MySQL to update your password and PIN in MySQL workbench - "UPDATE USERS SET PASSWORD = 'paste_the_new_hash_here' WHERE EMAIL = 'vimu@gmail.com';""


# import bcrypt

# new_password = "shazi1234"
# hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

# print(hashed.decode())