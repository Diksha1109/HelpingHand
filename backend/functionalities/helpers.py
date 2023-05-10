import re
from typing import List
import string
from werkzeug.datastructures import ImmutableMultiDict

email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
phone_regex = r'[0-9]{10,12}'
pass_regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'


def check_form_key_exist(form: ImmutableMultiDict, must_contain: List[str]):
    """
    It is used to validate form data keys
    """
    keys = form.keys()

    invalid = False
    for form_key in must_contain:
        if form_key not in keys:
            invalid = True
            break

    return not invalid


def validate_username(username: str):
    match = string.ascii_letters + string.digits
    if not all([x in match for x in username]):
        return False
    if not (len(username) >= 4 and len(username) <= 25):
        return False
    if not username[0].isalpha():
        return False
    return True


def validate_email(email: str):
    if (re.fullmatch(email_regex, email)):
        return True
    else:
        return False


def validate_phone(phone_number: str):
    if re.fullmatch(phone_regex, phone_number):
        return True
    else:
        return False


def validate_password_form(password: str):
    if re.match(pass_regex, password):
        return True
    else:
        return False
