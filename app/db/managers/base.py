from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.db.models.base import File, GuestUser

ModelType = TypeVar("ModelType", bound=Base)


class BaseManager(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get_all(self, db: AsyncSession) -> Optional[List[ModelType]]:
        result = (await db.execute(select(self.model))).scalars().all()
        return result

    async def get_all_ids(self, db: AsyncSession) -> Optional[List[ModelType]]:
        result = (await db.execute(select(self.model.id))).scalars().all()
        # ids = [item[0] for item in items]
        return result

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        return (
            await db.execute(select(self.model).where(self.model.id == id))
        ).scalar_one_or_none()

    async def create(
        self, db: AsyncSession, obj_in: Optional[ModelType] = {}
    ) -> Optional[ModelType]:
        obj_in["created_at"] = datetime.utcnow()
        obj_in["updated_at"] = obj_in["created_at"]
        obj = self.model(**obj_in)

        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def bulk_create(self, db: AsyncSession, obj_in: list) -> Optional[bool]:
        items = await db.execute(
            insert(self.model)
            .values(obj_in)
            .on_conflict_do_nothing()
            .returning(self.model.id)
        )
        await db.commit()
        ids = [item[0] for item in items]
        return ids

    async def update(
        self, db: AsyncSession, db_obj: Optional[ModelType], obj_in: Optional[ModelType]
    ) -> Optional[ModelType]:
        if not db_obj:
            return None
        for attr, value in obj_in.items():
            setattr(db_obj, attr, value)
        db_obj.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, db_obj: Optional[ModelType]):
        if db_obj:
            await db.delete(db_obj)
            await db.commit()

    async def delete_by_id(self, db: AsyncSession, id: UUID):
        to_delete = (
            await db.execute(select(self.model).where(self.model.id == id))
        ).scalar_one_or_none()
        await db.delete(to_delete)
        await db.commit()

    async def delete_all(self, db: AsyncSession):
        to_delete = await db.delete(self.model)
        await db.execute(to_delete)
        await db.commit()


class FileManager(BaseManager[File]):
    pass


class GuestUserManager(BaseManager[File]):
    pass


file_manager = FileManager(File)
guestuser_manager = GuestUserManager(GuestUser)
