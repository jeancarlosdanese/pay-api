from datetime import date
from typing import Optional
from pydantic import UUID4, BaseModel, condecimal, constr, validator
from app.schemas.bancos.pagador_bb import Pagador


class BoletoCreate(BaseModel):
    convenio_bancario_id: UUID4
    numero_titulo_beneficiario: int
    descricao_tipo_titulo: constr(min_length=2, max_length=2) = "DM"
    data_emissao: date = date.today()
    data_vencimento: date
    valor_original: condecimal()
    valor_desconto: Optional[condecimal()] = 0
    mensagem_beneficiario: Optional[constr(max_length=30)]
    pagador: Pagador

    @validator("descricao_tipo_titulo")
    def validate_descricao_tipo_titulo(cls, descricao_tipo_titulo: str):
        return descricao_tipo_titulo.upper() if descricao_tipo_titulo else descricao_tipo_titulo
