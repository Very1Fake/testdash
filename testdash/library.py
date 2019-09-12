from Crypto.Hash import SHA512


def encrypt_password(password: str) -> str:  # Return SHA512 hash of password
    return SHA512.new(bytes(password, 'utf8')).digest().hex()


def check_password(password: str, password_right: str):  # Checking SHA512 hash of password with original
    if SHA512.new(bytes(password, 'utf8')).digest().hex() == password_right:
        return True
    else:
        return False
