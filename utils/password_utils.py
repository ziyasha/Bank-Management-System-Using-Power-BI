# utils/password_utils.py

import bcrypt


def hash_password(plain_password):
    password_bytes = plain_password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(plain_password, hashed_password):
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def hash_pin(plain_pin):
    pin_bytes = plain_pin.encode('utf-8')
    hashed = bcrypt.hashpw(pin_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_pin(plain_pin, hashed_pin):
    pin_bytes = plain_pin.encode('utf-8')
    hashed_bytes = hashed_pin.encode('utf-8')
    return bcrypt.checkpw(pin_bytes, hashed_bytes)