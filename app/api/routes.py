from fastapi import APIRouter

from .api_v1.enums import router as enums_router
from .api_v1.tenants import router as tenants_router
from .api_v1.roles import router as roles_router
from .api_v1.permissions import router as permissions_router
from .api_v1.auth import router as auth_router
from .api_v1.users import router as users_router
from .api_v1.profile import router as profile_router
from .api_v1.boletos_bb import router as boleto_bb_router
from .api_v1.contas_bancarias import router as contas_bancarias_router
from .api_v1.convenios_bancarios import router as convenios_bancarios_router


router = APIRouter()


router.include_router(enums_router, prefix="/enums", tags=["enums"])
router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
router.include_router(roles_router, prefix="/roles", tags=["roles"])
router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(profile_router, prefix="/profile", tags=["profile"])
router.include_router(contas_bancarias_router, prefix="/contas-bancarias", tags=["contas-bancarias"])
router.include_router(convenios_bancarios_router, prefix="/convenios-bancarios", tags=["convenios-bancarios"])
router.include_router(boleto_bb_router, prefix="/boletos-bb", tags=["boletos-bb"])
