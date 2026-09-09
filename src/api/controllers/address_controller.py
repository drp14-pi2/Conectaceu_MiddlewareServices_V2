"""Address controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.services.address_service import AddressService
from src.data.repositories.address_repository import AddressRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.address import Address, AddressUpdate
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/address",
    tags=["Address"],
    dependencies=[Depends(get_current_active_user)]
)

def get_address_service(db: Session = Depends(get_db)) -> AddressService:
    """Dependency injection for AddressService"""
    repository = AddressRepository(db)

    return AddressService(repository)

@router.get("/user/{user_id}", response_model=List[Address])
async def get_user_addresses(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service)
):
    """
    Get all addresses for a user.
    - Users can view their own addresses
    - Admin/Secretary can view any user's addresses
    - Others: 403
    """
    # Admin (1) and Secretary (2) can view any. Users can only view their own
    if current_user.user_type_id in [1, 2] or current_user.id == user_id:
        return await service.get_user_addresses(user_id)
    
    raise HTTPException(status_code=403, detail="Can only view your own addresses")

@router.put("/{address_id}", response_model=Address)
async def update_address(
    address_id: UUID,
    dto: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service)
):
    """Update an address"""
    try:
        existing: Address | None = await service.get_by_id(address_id)

        if not existing:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Admin/Secretary can update any. Users can only update their own
        if current_user.user_type_id in [1, 2] or existing.user_id == current_user.id:
            return await service.update_address(address_id, dto)
        
        raise HTTPException(status_code=403, detail="Can only update your own addresses")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
