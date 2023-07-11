from enum import Enum


class ContaBancariaType(str, Enum):
    checking = "Corrente"
    savings = "Poupança"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, ContaBancariaType))


class PersonType(str, Enum):
    fisica = "Física"
    juridica = "Jurídica"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, PersonType))


class UnitType(str, Enum):
    un = "Un"
    cx = "Cx"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, UnitType))


class PhoneType(str, Enum):
    celular = "Celular"
    casa = "Casa"
    trabalho = "Trabalho"
    escola = "Escola"
    iphone = "iPhone"
    apple_watch = "Apple Watch"
    fax_residencial = "Fax residencial"
    fax_comercial = "Fax comercial"
    pager = "Pager"
    outro = "Outro"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, PhoneType))


class EmailType(str, Enum):
    casa = "Casa"
    trabalho = "Trabalho"
    escola = "Escola"
    icloud = "iCloud"
    outro = "Outro"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, EmailType))


class AddressType(str, Enum):
    casa = "Casa"
    trabalho = "Trabalho"
    escola = "Escola"
    outro = "Outro"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, AddressType))


class StatesUF(str, Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"
    DF = "DF"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, StatesUF))


class TipoKeyError(str, Enum):
    email_not_verified = "email_not_verified"
    user_not_active = "user_not_active"
    auth_unsuccessful = "auth_unsuccessful"
    max_connections_by_user = "max_connections_by_user"

    @classmethod
    def values(cls):
        return list(map(lambda o: o.value, TipoKeyError))


# class Operator(str, Enum):
#     eq
#     isnull
#     notnull
#     isnotnull
#     bitwiseand
#     gt
#     gte
#     lt
#     lte
#     ne
#     glob
#     like
#     not_like
#     ilike
#     not_ilike
#     rlike
#     regex
#     regexp
#     between
#     from_to
#     as_of
#     all_
#     isin
#     notin
#     bin_regex
#     negate
#     lshift
#     rshift
