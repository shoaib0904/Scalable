from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Hashes the given password using a secure hash algorithm.
    """
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """
    Verifies if the provided password matches the given hashed password.
    """
    return check_password_hash(hashed_password, password)
