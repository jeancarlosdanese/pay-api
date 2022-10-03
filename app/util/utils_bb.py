from datetime import date
import re


camel_pat = re.compile(r"([A-Z])")
under_pat = re.compile(r"_([a-z])")


def get_numero_titulo_cliente(numero_convenio: int, numero_titulo_beneficiario: int) -> str:
    return f"000{numero_convenio:07d}{numero_titulo_beneficiario:010d}"


def get_date_bb_format(date: date) -> str:
    return f"{date.day:02d}.{date.month:02d}.{date.year}"


def get_date_bb(data_str: str):
    if not data_str or not isinstance(data_str, str) or len(data_str) == 0:
        return ""
    elif isinstance(data_str, str) and len(data_str) == 10 and "." in data_str:
        data_parts = data_str.split(".")
        data_iso = f"{int(data_parts[2])}-{int(data_parts[1]):02d}-{int(data_parts[0]):02d}"
        # data = date(int(data_parts[2]), int(data_parts[1]), int(data_parts[0]))
        data = date.fromisoformat(data_iso)

        assert isinstance(data, date), "Invalid date"
        return data_iso
