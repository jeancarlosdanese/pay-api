from typing import Any, Optional
from pydantic import UUID4, conint, constr, validator

from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin
from app.schemas.enums import StatesUF
from app.util.utils import camel_to_underscore, underscore_to_camel


class Beneficiario(BaseSchema):
    agencia: Optional[conint()]
    conta_corrente: Optional[conint()]
    tipo_endereco: Optional[conint()]
    logradouro: Optional[constr(curtail_length=30)]
    bairro: Optional[constr(curtail_length=30)]
    cidade: Optional[constr(curtail_length=30)]
    codigo_cidade: Optional[conint()]
    uf: Optional[StatesUF]
    cep: Optional[constr()]
    indicador_comprovacao: Optional[constr()]


class BeneficiarioBB(Beneficiario):
    cep: Any

    @validator("cep", pre=True)
    def cep_valid(cls, cep: int) -> str:
        if cep and isinstance(cep, int):
            cep = f"{cep:08d}"
            return f"{cep[0:5]}-{cep[5:8]}"

        return str(cep)

    class Config:
        alias_generator = underscore_to_camel


class BeneficiarioFinalBB(BaseSchema):
    tipoInscricao: int  # noqa flake8(E501) - Domínio: 1 - Pessoa física; 2 - Pessoa Jurídica
    numeroInscricao: conint()  # noqa flake8(E501) - Define o número de inscrição do beneficiário final (antigo avalista); se pessoa física, CPF; se pessoa jurídica, CNPJ. Numérico, deve ser preenchido sem ponto, hífen, barra, e sem zeros à esquerda
    nome: constr(
        curtail_length=30
    )  # Identifica o nome do beneficiário final (antigo avalista). Pode ter até 30 caracteres


class BeneficiarioWithTenantCreate(BeneficiarioBB):
    tenant_id: Optional[UUID4]
    boleto_bb_id: Optional[UUID4]

    class Config:
        alias_generator = camel_to_underscore


class BeneficiarioIdentificacao(BaseSchema):
    nome: Optional[str]
    cpf_cnpj: Optional[str]


class BeneficiarioFull(Beneficiario, BeneficiarioIdentificacao, IDModelMixin):
    pass


class BeneficiarioInDB(DateTimeModelMixin, BeneficiarioFull):
    pass
