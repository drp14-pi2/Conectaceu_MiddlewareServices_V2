"""User repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.data.models.user_model import UserModel
from src.data.repositories.base.base_repository import BaseRepository

class UserRepository(BaseRepository[UserModel]):
    """Repository for User entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)
    
    async def get_by_document(self, document: str) -> Optional[UserModel]:
        """Get user by document"""
        stmt = select(UserModel).where(UserModel.document == document)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        if not email:
            return None
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_cellphone(self, cellphone: str) -> Optional[UserModel]:
        """Get user by cellphone number"""
        if not cellphone:
            return None
        stmt = select(UserModel).where(UserModel.cellphone_number == cellphone)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_filters(
        self,
        name: Optional[str] = None,
        document: Optional[str] = None,
        email: Optional[str] = None,
        phoneNumber: Optional[str] = None,
        user_type_id: Optional[int] = None,
        sex_id: Optional[int] = None,
        gender_id: Optional[int] = None,
        active: Optional[bool] = None,
        email_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserModel]:
        """Find users with multiple filters"""
        conditions = [UserModel.user_type_id != 1] # Never include administrators
        
        if name:
            conditions.append(UserModel.name.contains(name))
        if document:
            conditions.append(UserModel.document == document)
        if email:
            conditions.append(UserModel.email == email)
        if phoneNumber:
            conditions.append(UserModel.cellphone_number == phoneNumber)
        if user_type_id:
            conditions.append(UserModel.user_type_id == user_type_id)
        if sex_id:
            conditions.append(UserModel.sex_id == sex_id)
        if gender_id:
            conditions.append(UserModel.gender_id == gender_id)
        if active is not None:
            conditions.append(UserModel.active == active)
        if email_verified is not None:
            conditions.append(UserModel.email_verified == email_verified)
        
        stmt = select(UserModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def deactivate(self, user_id: UUID) -> bool:
        """Soft delete - deactivate user"""
        user = await self.get_by_id(user_id)
        if user:
            user.active = False
            await self.session.flush()
            return True
        return False
    
    async def activate(self, user_id: UUID) -> bool:
        """Activate user"""
        user = await self.get_by_id(user_id)
        if user:
            user.active = True
            await self.session.flush()
            return True
        return False
    
    async def update_password(self, user_id: UUID, hashed_password: str) -> bool:
        """Update user password"""
        user = await self.get_by_id(user_id)
        if user:
            user.password = hashed_password
            await self.session.flush()
            return True
        return False
    
    async def get_educators(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Get all educators (user_type_id = 4)"""
        return await self.find_by_filters(user_type_id=4, active=True, skip=skip, limit=limit)
    
    async def get_students(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Get all students (user_type_id = 5)"""
        return await self.find_by_filters(user_type_id=5, active=True, skip=skip, limit=limit)
    
    async def find_by_password_reset_token(self, token: str) -> Optional[UserModel]:
        """Find user by password reset token"""
        stmt = select(UserModel).where(UserModel.password_reset_token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_password_reset_token(self, user_id: UUID) -> bool:
        """Clear password reset token"""
        user = await self.get_by_id(user_id)
        if user:
            user.password_reset_token = None
            user.password_reset_expires = None
            await self.session.flush()
            return True
        return False
    
    async def get_last_student_sequential(self) -> int:
        stmt = (
            select(UserModel.student_sequential)
            .where(
                and_(
                    UserModel.user_type_id == 5,
                    UserModel.student_sequential != None
                )
            )
            .order_by(UserModel.student_sequential.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        last = result.scalar_one_or_none()
        return last or 0