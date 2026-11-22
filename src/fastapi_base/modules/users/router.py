from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from fastapi_base.api.deps import CurrentPrincipal, require
from fastapi_base.modules.users.dependencies import UserServiceDep
from fastapi_base.modules.users.permissions import UserPermission
from fastapi_base.modules.users.schemas import (
    MeDTO,
    UserFilterDTO,
    UserReadDTO,
    UserUpdateDTO,
)
from fastapi_base.shared.schemas import PageDTO

router = APIRouter(prefix="/users", tags=["users"])
UserId = Annotated[int, Path(ge=1)]


@router.get(
    "/me",
    response_model=MeDTO,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require(UserPermission.READ))],
)
async def me(principal: CurrentPrincipal, service: UserServiceDep) -> MeDTO:
    return await service.get_me(principal)


@router.patch(
    "/me",
    response_model=MeDTO,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require(UserPermission.WRITE))],
)
async def update_me(
    userUpdateDTO: UserUpdateDTO, principal: CurrentPrincipal, service: UserServiceDep
) -> MeDTO:
    return await service.update_me(principal, userUpdateDTO)


@router.get(
    "/search",
    response_model=PageDTO[UserReadDTO],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require(UserPermission.READ))],
)
async def seach(
    filterDTO: Annotated[UserFilterDTO, Query()], service: UserServiceDep
) -> PageDTO[UserReadDTO]:
    return await service.search(filterDTO)


@router.delete(
    "/{user_id}/roles/{role}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require(UserPermission.WRITE))],
)
async def remove_role(user_id: UserId, role: str, service: UserServiceDep) -> None:
    await service.remove_role(user_id, role)


@router.post(
    "/deactivate/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require(UserPermission.WRITE))],
)
async def deactivate_user(user_id: UserId, service: UserServiceDep) -> None:
    await service.deactivate_user(user_id)
