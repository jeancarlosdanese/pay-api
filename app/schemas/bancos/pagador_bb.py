import re
from typing import Any, Optional
from pydantic import UUID4, constr, validator

from app.schemas.base import BaseSchema, DateTimeModelMixin, IDModelMixin
from app.schemas.enums import PersonType
from app.util.validators import (
    validate_cpf_cnpj,
    validate_phone_number,
)


class Pagador(BaseSchema):
    tipo_inscricao: PersonType  # Domínio: 1 - Pessoa física; 2 - Pessoa Jurídica.
    numero_inscricao: constr()  # noqa flake8(E501) - Define o número de inscrição do pagador; se pessoa física, CPF; se pessoa jurídica, CNPJ. Numérico, deve ser preenchido sem ponto, hífen, barra, e sem zeros à esquerda
    nome: constr(curtail_length=30)  # Identifica o nome do pagador. Pode ter até 30 caracteres
    endereco: constr(curtail_length=30)  # Identifica o endereço do pagador. Pode ter até 30 caracteres
    cep: constr(min_length=8, max_length=9)
    cidade: constr(curtail_length=30)  # Identifica a cidade do pagador. Pode ter até 30 caracteres
    bairro: constr(curtail_length=30)  # Identifica o bairro do pagador. Pode ter até 30 caracteres.
    uf: constr(
        min_length=2, max_length=2
    )  # Identifica o estado (UF) do pagador. Deve ter 2 caracteres e ser um estado válido.
    telefone: constr(curtail_length=30)  # Define o número de telefone do pagador. Pode ter até 30 caracteres.

    @validator("numero_inscricao", pre=True)
    def cpf_cnpj_is_valid(cls, cpf_cnpj: str) -> str:
        return validate_cpf_cnpj(cpf_cnpj)

    @validator("telefone", pre=True)
    def work_phone_is_valid(cls, telefone: str) -> str:
        return validate_phone_number(telefone)


class PagadorBB(BaseSchema):
    tipoInscricao: Any
    numeroInscricao: Any
    nome: constr(curtail_length=30)  # Identifica o nome do pagador. Pode ter até 30 caracteres
    endereco: constr(curtail_length=30)  # Identifica o endereço do pagador. Pode ter até 30 caracteres
    cep: Any
    cidade: constr(curtail_length=30)  # Identifica a cidade do pagador. Pode ter até 30 caracteres
    bairro: constr(curtail_length=30)  # Identifica o bairro do pagador. Pode ter até 30 caracteres.
    uf: constr(
        min_length=2, max_length=2
    )  # Identifica o estado (UF) do pagador. Deve ter 2 caracteres e ser um estado válido.
    telefone: Any

    @validator("tipoInscricao", pre=True)
    def tipo_inscricao_valid(cls, tipo_inscricao: PersonType) -> int:
        return 1 if tipo_inscricao == PersonType.fisica else 2

    @validator("numeroInscricao", pre=True)
    def numero_inscricao_is_valid(cls, cpf_cnpj: str) -> int:
        return int(re.sub("\D", "", cpf_cnpj))  # noqa flake8(W605)

    @validator("cep", pre=True)
    def cep_valid(cls, cep: str) -> int:
        return int(re.sub("\D", "", cep))  # noqa flake8(W605)

    @validator("telefone", pre=True)
    def telefone_valid(cls, telefone: str) -> int:
        return int(re.sub("\D", "", telefone))  # noqa flake8(W605)

    # class Config:
    #     alias_generator = underscore_to_camel


class PagadorWithTenantCreate(Pagador):
    tenant_id: Optional[UUID4]
    boleto_bb_id: Optional[UUID4]


class PagadorFull(Pagador, IDModelMixin):
    pass


class PagadorInDB(DateTimeModelMixin, PagadorFull):
    pass
