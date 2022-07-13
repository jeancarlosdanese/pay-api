from typing import Any
import httpx
from app.api.dependencies.database import get_repository
from fastapi import Body, Depends, HTTPException, status
from app.api.dependencies.redis_database import get_redis_repository
from app.db.repositories.boletos_bb import BoletosBBRepository
from app.db.repositories.convenios_bancarios import ConveniosBancariosRepository
from app.db.repositories.contas_bancarias import ContasBancariasRepository
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.bancos.boleto import BoletoCreate

from app.schemas.tenant import TenantInDB
from fastapi.routing import APIRouter
from app.api.dependencies.auth import get_tenant_by_api_key


router = APIRouter()
client = httpx.AsyncClient()


@router.post("", response_model=Any, name="boletos-bb:register-new-boleto-bb", status_code=status.HTTP_201_CREATED)
async def register_new_boleto_bb(
    new_boleto: BoletoCreate = Body(..., embed=False),
    convenios_bancarios_repo: ConveniosBancariosRepository = Depends(get_repository(ConveniosBancariosRepository)),
    contas_bancarias_repo: ContasBancariasRepository = Depends(get_repository(ContasBancariasRepository)),
    token_bb_redis_repo: TokenBBRedisRepository = Depends(get_redis_repository(TokenBBRedisRepository)),
    boletos_bb_repo: BoletosBBRepository = Depends(get_repository(BoletosBBRepository)),
    tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
) -> Any:
    convenio_bancario = await convenios_bancarios_repo.get_convenio_bancario_by_id(
        tenant_id=tenant_origin.id, id=new_boleto.convenio_bancario_id
    )
    if not convenio_bancario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That convenio_bancario_id is not found. Please try another one.",
        )

    conta_bancaria = await contas_bancarias_repo.get_conta_bancaria_by_id(
        tenant_id=tenant_origin.id,
        id=convenio_bancario.conta_bancaria_id,
    )

    if not conta_bancaria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That conta_bancaria_id is not found. Please try another one.",
        )

    bobelo_bb_in_db = await boletos_bb_repo.register_new_boleto_bb(
        tenant=tenant_origin,
        convenio_bancario=convenio_bancario,
        conta_bancaria=conta_bancaria,
        new_boleto=new_boleto,
        token_bb_redis_repo=token_bb_redis_repo,
    )

    return bobelo_bb_in_db
