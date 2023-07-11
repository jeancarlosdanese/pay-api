from typing import Dict, Sequence, Union

from pydantic_i18n import BaseLoader, DictLoader

__all__ = ("TranslatorI18n",)


class TranslatorI18n:
    def __init__(
        self,
        source: Union[Dict[str, Dict[str, str]], BaseLoader],
    ):
        if isinstance(source, dict):
            source = DictLoader(source)

        self.source = source

    @property
    def locales(self) -> Sequence[str]:
        return self.source.locales

    def translate(
        self,
        msg: str,
        locale: str,
    ) -> str:
        msgs_dict = self.source.get_translations(locale=locale)

        return msgs_dict[msg] if msg in msgs_dict.keys() else msg
