import re

def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+(\+[A-Za-z0-9._%+-]+)?@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.fullmatch(pattern, email) is not None