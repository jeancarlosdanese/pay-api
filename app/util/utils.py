import re
import locale
from decimal import Decimal
from datetime import date


camel_pat = re.compile(r"([A-Z])")
under_pat = re.compile(r"_([a-z])")


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_snake_case(string: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()


def camel_to_underscore(name):
    res = camel_pat.sub(lambda x: "_" + x.group(1).lower(), name)
    # print(f"{name}: --> {res}")
    return res


def underscore_to_camel(name):
    res = under_pat.sub(lambda x: x.group(1).upper(), name)
    # print(f"{name}: --> {res}")
    return res


def get_date_print_format(date: date) -> str:
    return f"{date.day:02d}/{date.month:02d}/{date.year}"


def get_valor_real_print_format(valor: Decimal) -> str:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
    # return locale.currency(valor, grouping=True)
    return locale.format_string("%.2f", valor, True)
