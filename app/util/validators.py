from datetime import datetime
import string
import re
import dateutil
import phonenumbers

from validate_docbr import CPF, CNPJ


# simple check for valid username
def validate_cpf_cnpj(cpf_cnpj: str) -> str:
    if cpf_cnpj is None:
        return cpf_cnpj
    cpf_cnpj = re.sub("[-/.]", "", cpf_cnpj)
    assert all(char in string.digits for char in cpf_cnpj), "Invalid characters in cpf_cnpj."
    assert len(cpf_cnpj) == 11 or len(cpf_cnpj) == 14, "Number invalid of characters in cpf_cnpj."
    if len(cpf_cnpj) == 11:
        cpf = CPF()
        assert cpf.validate(cpf_cnpj), "Invalid CPF number"
        return cpf.mask(cpf_cnpj)
    if len(cpf_cnpj) == 14:
        cnpj = CNPJ()
        assert cnpj.validate(cpf_cnpj), "Invalid CNPJ number"
        return cnpj.mask(cpf_cnpj)


def validate_phone_number(phone_number: str) -> str:
    if not phone_number or phone_number == "":
        return phone_number

    if phone_number[0] == "+":
        number = phonenumbers.parse(f"{phone_number}", None)
        assert phonenumbers.is_valid_number(number)
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    number = phonenumbers.parse(f"{phone_number}", "BR")
    assert phonenumbers.is_valid_number(number)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL)


def clear_string_to_validate(string: str):
    return re.sub(" +", " ", string).strip()


def datetime_format(value):
    date_format = value or datetime.now()
    if isinstance(date_format, str):
        date_format = dateutil.parser.parse(date_format)

    return date_format.astimezone()
