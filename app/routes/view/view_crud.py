import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import joinedload

from app.database.base import Base
from app.database.db import CurrentAsyncSession

ModelType = TypeVar("ModelType", bound=Base)


class SQLAlchemyCRUD(Generic[ModelType]):
    def __init__(
        self,
        db_model: Type[ModelType],
        related_models: Optional[Dict[Type[Base], str]] = None,
    ):
        self.db_model = db_model
        self.related_models = related_models if related_models is not None else {}

    async def create(self, data: dict[str, Any], db: CurrentAsyncSession) -> ModelType:
        new_record = self.db_model(**data)
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        return new_record

    async def read_all(
        self,
        db: CurrentAsyncSession,
        skip: int = 0,
        limit: int = 0,
        join_relationships: bool = False,
    ) -> List[ModelType]:

        stmt = select(self.db_model)
        if join_relationships:
            for related_model, join_column in self.related_models.items():
                relationship = getattr(self.db_model, join_column, None)

                if relationship is not None:
                    stmt = stmt.options(joinedload(relationship))

                else:
                    # Handle error or invalid relationship specification
                    raise ValueError(f"No relationship found for {join_column}")
        stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        query = await db.execute(stmt)
        return list(query.unique().scalars().all())

    async def read_by_primary_key(
        self,
        db: CurrentAsyncSession,
        id: uuid.UUID,
        join_relationships: bool = False,
    ) -> ModelType:

        stmt = select(self.db_model)
        if join_relationships:
            for related_model, join_column in self.related_models.items():
                relationship = getattr(self.db_model, join_column, None)
                # print(relationship)
                if relationship is not None:
                    stmt = stmt.options(joinedload(relationship))
                else:
                    # Handle error or invalid relationship specification
                    raise ValueError(f"No relationship found for {join_column}")
        stmt = stmt.where(self.db_model.id == id)
        query = await db.execute(stmt)
        record = query.scalar()
        if not record:
            raise HTTPException(status_code=404, detail=f"Record with {id} not found")
        return record

    async def read_by_column(
        self,
        db: CurrentAsyncSession,
        column_name: str,
        column_value: Any,
        skip: int = 0,
        limit: int = 0,
    ) -> Union[Optional[ModelType], List[ModelType]]:

        column = getattr(self.db_model, column_name)

        if isinstance(column_value, str):
            stmt = select(self.db_model).where(
                func.lower(column) == column_value.lower()
            )
        else:
            stmt = select(self.db_model).where(column == column_value)
        if skip > 0:
            stmt = stmt.offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        query = await db.execute(stmt)
        # unique(): to avoid duplicate rows in case of join operations.
        records = list(query.unique().scalars().all())
        if not records:
            return None
        elif len(records) == 1:
            return records[0]
        else:
            return records

    async def update(
        self, db: CurrentAsyncSession, id: uuid.UUID, data: dict[str, Any]
    ) -> ModelType | None:

        stmt = select(self.db_model).where(self.db_model.id == id)
        query = await db.execute(stmt)
        if not query:
            raise HTTPException(status_code=404, detail=f"Record with {id} not found")
        db_item = query.scalar_one()
        if db_item:
            for key, value in data.items():
                setattr(db_item, key, value)
            await db.commit()
            await db.refresh(db_item)
            return db_item

    async def delete(
        self,
        db: CurrentAsyncSession,
        id: uuid.UUID,
    ) -> bool:

        stmt = select(self.db_model).where(self.db_model.id == id)
        query = await db.execute(stmt)
        if not query:
            raise HTTPException(status_code=404, detail=f"Record with {id} not found")
        db_item = query.scalar_one()
        if db_item:
            await db.delete(db_item)
            await db.commit()
            return True
        return False

    async def check_associated_records(
        self,
        db: CurrentAsyncSession,
        associated_model: Type[Base],
        primary_attribute: uuid.UUID,
        secondary_attribute: uuid.UUID,
    ) -> List[ModelType | None]:

        column_names = [column.key for column in inspect(associated_model).columns]

        result = await db.execute(
            select(associated_model).filter(
                getattr(associated_model, column_names[0]) == primary_attribute,
                getattr(associated_model, column_names[1]) == secondary_attribute,
            )
        )
        existing_record = result.scalar_one_or_none()
        return existing_record
