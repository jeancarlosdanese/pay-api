from datetime import date
import re


camel_pat = re.compile(r"([A-Z])")
under_pat = re.compile(r"_([a-z])")


def get_numero_titulo_cliente(numero_convenio: int, numero_titulo_beneficiario: int) -> str:
    return f"000{numero_convenio:07d}{numero_titulo_beneficiario:010d}"


def get_date_bb_format(date: date) -> str:
    return f"{date.day:02d}.{date.month:02d}.{date.year}"
