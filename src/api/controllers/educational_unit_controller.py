"""EducationalUnit controller"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.educational_unit_service import EducationalUnitService
from src.data.repositories.educational_unit_repository import EducationalUnitRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.educational_unit import EducationalUnit, EducationalUnitCreate, EducationalUnitUpdate
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/unit",
    tags=["EducationalUnit"],
    dependencies=[Depends(get_current_active_user)]
)

def get_educational_unit_service(db: AsyncSession = Depends(get_db)) -> EducationalUnitService:
    """Dependency injection for EducationalUnitService"""
    repository = EducationalUnitRepository(db)

    return EducationalUnitService(repository)

@router.get("/{id}", response_model=EducationalUnit)
@limiter.limit("20/minute")
async def get_educational_unit(
    request: Request,
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: EducationalUnitService = Depends(get_educational_unit_service)
):
    """
    Get an educational unit.
    - Admin can view any educational unit
    - Others: 403
    """
    # Admin (1) can view any
    if current_user.user_type_id not in [1]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.get_by_id(id)

@router.get("/", response_model=list[EducationalUnit])
@limiter.limit("20/minute")
async def get_educational_units(
    request: Request,
    active: bool = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: EducationalUnitService = Depends(get_educational_unit_service)
):
    """
    Get all educational units.
    - Admin can view any educational units
    - Others: 403
    """
    # Admin (1) can view any
    if current_user.user_type_id not in [1]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.list(active)

@router.post("/", response_model=EducationalUnit)
@limiter.limit("5/minute")
async def create_educational_unit(
    request: Request,
    body: EducationalUnitCreate,
    current_user: User = Depends(get_current_active_user),
    service: EducationalUnitService = Depends(get_educational_unit_service)
):
    """Create an educational unit"""
    # Admin (1) can create
    if current_user.user_type_id not in [1]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    try:
        return await service.create(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{id}", response_model=EducationalUnit)
@limiter.limit("5/minute")
async def update_educational_unit(
    request: Request,
    id: UUID,
    body: EducationalUnitUpdate,
    current_user: User = Depends(get_current_active_user),
    service: EducationalUnitService = Depends(get_educational_unit_service)
):
    """Update an educational unit"""
    # Admin (1) can update
    if current_user.user_type_id not in [1]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    try:
        return await service.update(id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
