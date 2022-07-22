from datetime import date, timedelta
from typing import Optional

from pydantic import condecimal, conint, validator

from app.schemas.base import BaseSchema
from app.util.utils import get_date_print_format, get_valor_real_print_format


class EnderecoBoleto(BaseSchema):
    cep: Optional[str]
    logradouro: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]

    @property
    def endereco(self) -> str:
        endereco = ""
        if self.cep:
            endereco = f"CEP: {self.cep}"

        if not endereco and self.logradouro:
            endereco = f"{self.logradouro}"
        else:
            endereco += f"; {self.logradouro}"

        if not endereco and self.bairro:
            endereco = f"BAIRRO: {self.bairro}"
        else:
            endereco += f", {self.bairro}"

        if not endereco and self.cidade:
            endereco = f"CIDADE: {self.cidade}"
        else:
            endereco += f" - {self.cidade}"

        if not endereco and self.uf:
            endereco = f"UF: {self.uf}"
        else:
            endereco += f"-{self.uf}"

        return endereco


class BeneficiarioBoleto(EnderecoBoleto):
    agencia: str
    conta: str
    nome: str
    cpf_cnpj: str


class PagadorBoleto(EnderecoBoleto):
    nome: str
    cpf_cnpj: str


class DadosBoleto(BaseSchema):
    aceite: str = "N"
    carteira: str
    data_documento: date
    data_processamento: date
    data_vencimento: date
    numero_documento: str
    nosso_numero: str
    valor_original: condecimal()
    valor_desconto: condecimal()
    linha_digitavel: str
    codigo_barras: str

    local_pagamento: Optional[str] = "Pagável em qualquer banco até o vencimento"
    quantidade: Optional[str] = None
    especie: Optional[str] = "R$"
    especie_documento: Optional[str] = "DM"
    moeda: Optional[str] = "9"
    qr_code: Optional[str] = None
    numero_dias_limite_recebimento: Optional[conint()] = 30
    taxa_juros_mes: Optional[condecimal()] = None
    taxa_multa: Optional[condecimal()] = None
    mensagem_beneficiario: Optional[str]

    beneficiario: BeneficiarioBoleto
    pagador: PagadorBoleto

    @validator("linha_digitavel")
    def validate_linha_digitavel(cls, linha_digitavel: str):
        if len(linha_digitavel) == 47:
            ld = str(linha_digitavel)
            return f"{ld[0:5]}.{ld[5:10]} {ld[10:15]}.{ld[15:21]} {ld[21:26]}.{ld[26:32]} {ld[32:33]} {ld[33:47]}"

        return linha_digitavel

    @property
    def data_vencimento_format(cls) -> str:
        return get_date_print_format(cls.data_vencimento)

    @property
    def data_processamento_format(cls) -> str:
        return get_date_print_format(cls.data_documento)

    @property
    def data_documento_format(cls) -> str:
        return get_date_print_format(cls.data_processamento)

    @property
    def valor_original_format(cls):
        return get_valor_real_print_format(cls.valor_original)

    @property
    def valor_desconto_format(cls):
        return get_valor_real_print_format(cls.valor_desconto)

    @property
    def mensagem_dias_recebimento(cls) -> str:
        data_limite = cls.data_vencimento + timedelta(days=cls.numero_dias_limite_recebimento)
        return f"Não receber após {cls.numero_dias_limite_recebimento} dias do vencimento \
            ({get_date_print_format(data_limite)})"

    @property
    def mensagem_desconto(cls) -> str:
        if cls.valor_desconto > 0:
            return f"DESC: R$ {cls.valor_desconto_format} até {cls.data_vencimento_format}"

        return ""

    @property
    def mensagem_juros(cls) -> str:
        if cls.taxa_juros_mes > 0:
            return f"JUROS: Taxa mensal {get_valor_real_print_format(cls.taxa_juros_mes)}% APÓS \
                {cls.data_vencimento_format}"

        return ""

    @property
    def mensagem_multa(cls) -> str:
        if cls.taxa_multa > 0:
            data_multa = cls.data_vencimento + timedelta(days=1)
            return f"MULTA DE: {get_valor_real_print_format(cls.taxa_multa)}% A PARTIR DE \
                {get_date_print_format(data_multa)}"

        return ""


class DadosBoletoBB(DadosBoleto):
    banco_id: str = "001"
    logo_banco: Optional[str] = "static/logos/banco_do_brasil.png"
    local_pagamento: Optional[str] = "Pagável preferencialmente nos canais de autoatendimento do Banco do Brasil"
