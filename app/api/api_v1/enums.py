from typing import List

from fastapi.param_functions import Depends
from app.api.dependencies.auth import get_auth_token
from app.api.dependencies.security import tenant_authentication_header
from app.schemas.enums import (
    AddressType,
    ContaBancariaType,
    EmailType,
    PersonType,
    PhoneType,
    StatesUF,
    TipoKeyError,
    UnitType,
)
from fastapi.routing import APIRouter


router = APIRouter()


@router.get(
    "/conta-bancaria-types",
    response_model=List[ContaBancariaType],
    name="enums:get-conta-bancaria-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_conta_bancaria_types() -> List[ContaBancariaType]:
    types = [p.value for p in ContaBancariaType]
    return types


@router.get(
    "/person-types",
    response_model=List[PersonType],
    name="enums:get-person-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_person_types() -> List[PersonType]:
    types = [p.value for p in PersonType]
    return types


@router.get(
    "/unit-types",
    response_model=List[UnitType],
    name="enums:get-unit-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_unit_types() -> List[UnitType]:
    types = [p.value for p in UnitType]
    return types


@router.get(
    "/phone-types",
    response_model=List[PhoneType],
    name="enums:get-phone-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_phone_types() -> List[PhoneType]:
    types = [p.value for p in PhoneType]
    return types


@router.get(
    "/email-types",
    response_model=List[EmailType],
    name="enums:get-email-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_email_types() -> List[EmailType]:
    types = [p.value for p in EmailType]
    return types


@router.get(
    "/address-types",
    response_model=List[AddressType],
    name="enums:get-address-types",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_address_types() -> List[AddressType]:
    types = [p.value for p in AddressType]
    return types


@router.get(
    "/state-ufs",
    response_model=List[StatesUF],
    name="enums:get-state-ufs",
    dependencies=[Depends(tenant_authentication_header)],
)
async def get_enums_of_state_ufs() -> List[StatesUF]:
    ufs = [p.value for p in StatesUF]
    return ufs


@router.get(
    "/key-errors",
    response_model=List[TipoKeyError],
    name="enums:get-key-errors",
    dependencies=[Depends(get_auth_token)],
)
async def get_enums_of_key_errors() -> List[TipoKeyError]:
    return TipoKeyError.values()
