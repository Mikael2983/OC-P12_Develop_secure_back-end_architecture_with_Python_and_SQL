import logging
from typing import Any, Dict, List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.inspection import inspect

logger = logging.getLogger(__name__)


class Entity:
    """
    Base class for ORM models providing reusable filtering,
    sorting, saving, updating, and soft deleting features,
    with support for joined relationships and dotted path resolution.
    """

    @staticmethod
    def _resolve(obj: Any, attr_path: str) -> Any:
        """
        Resolves a dotted attribute path (e.g., "user.name") on an object.

        Args:
            obj: Base object to resolve from.
            attr_path: Dotted attribute path.

        """
        current = obj
        for attr in attr_path.split("."):
            if current is None:
                return ""
            current = getattr(current, attr, None)
            if current is None:
                return ""
        return current

    @classmethod
    def _is_valid_path(cls, attr_path: str) -> bool:
        """
        Validates if a path exists on the model using double underscores for relations.

        Args:
            attr_path: Path like "relation__field".

        Returns:
            True if valid, False otherwise.
        """
        try:
            model = cls
            for part in attr_path.split("__"):
                mapper = inspect(model)
                if part not in mapper.relationships and part not in mapper.columns:
                    return False
                if part in mapper.relationships:
                    model = mapper.relationships[part].mapper.class_
            return True
        except SQLAlchemyError as e:
            logger.exception(e)
            return False

    @classmethod
    def filter_by_fields(cls,
                         db: Session,
                         archived: bool = False,
                         **filters: Dict[str, Any]
                         ) -> List[Any]:
        """
        Filter instances based on field-value pairs, supporting nested relationships.

        Args:
            db: SQLAlchemy session.
            archived: Include archived objects if True.
            **filters: Key-value pairs where keys may include relations via '__'.

        Returns:
            List of filtered ORM instances.

        raise : AttributeError if wrong field in filters
                SQLAlchemyError : If a database error occurs during the query.
        """
        try:
            query = db.query(cls)
            relations = set()

            if hasattr(cls, "archived") and not archived:
                query = query.filter(cls.archived.is_(False))

            for field_path, value in filters.items():
                path_parts = field_path.split("__")
                current_model = cls
                relation_chain = []

                for part in path_parts[:-1]:
                    attr = getattr(current_model, part)
                    relation_chain.append(attr)
                    current_model = attr.property.mapper.class_

                final_attr = getattr(current_model, path_parts[-1])

                for rel in relation_chain:
                    query = query.join(rel)

                query = query.filter(final_attr == value)
                relations.update(path_parts[:-1])

            for rel in relations:
                if hasattr(cls, rel):
                    query = query.options(joinedload(getattr(cls, rel)))

            return query.all()

        except (AttributeError, SQLAlchemyError) as e:
            logger.exception(e)
            raise

    @classmethod
    def order_by_fields(cls,
                        db: Session,
                        field_path: str,
                        descending: bool = False,
                        archived: bool = False
                        ) -> List[Any]:
        """
        Return all objects ordered by a specified field, including nested fields.

        Args:
            db: SQLAlchemy session.
            field_path: Dot-separated field path (e.g. "user.name").
            descending: Sort in descending order if True.
            archived: Include archived records if True.

        Returns:
            Sorted list of ORM instances.

        Raises:
            SQLAlchemyError : If a database error occurs during the query.
        """
        try:
            query = db.query(cls)

            if hasattr(cls, "archived") and not archived:
                with db.no_autoflush:
                    query = query.filter(cls.archived.is_(False))

            if "." in field_path:
                relation = field_path.split(".")[0]
                if hasattr(cls, relation):
                    with db.no_autoflush:
                        query = query.options(
                            joinedload(getattr(cls, relation))
                        )

            results = query.all()

        except SQLAlchemyError as e:
            logger.exception(e)
            raise

        return sorted(results,
                      key=lambda obj: cls._resolve(obj, field_path),
                      reverse=descending
                      )

    def save(self, db: Session) -> None:
        """
        Validate and persist the instance to the database.

        Args:
            db: SQLAlchemy session.

        Raises:
            SQLAlchemyError : If a database error occurs during the commit.
        """
        try:
            db.add(self)
            db.commit()
        except SQLAlchemyError as e:
            logger.exception(f"database error occurs during save: {e}")
            db.rollback()
            raise

    def update(self, db: Session, data: dict) -> None:
        """
        Update the instance with given attributes and persist changes.

        Args:
            db: SQLAlchemy session.
            data: Field-value pairs to update.

        Raises:
            AttributeError : if an attribute is protected or non-existent.
            ValueError, TypeError: invalid data during validation.
            SQLAlchemyError : If a database error occurs during the commit.
        """
        try:
            for attr, value in data.items():

                if attr == "signed":
                    value = 'True' == value

                if hasattr(self, attr):
                    setattr(self, attr, value)

            self.validate_all(db)
            db.commit()

        except (AttributeError, ValueError, TypeError, SQLAlchemyError) as e:
            db.rollback()
            logger.exception(e)
            raise

    @classmethod
    def soft_delete(cls, db: Session, item_id: int) -> None:
        """
        Soft delete an instance by setting 'archived' field to True.

        Args:
            db: SQLAlchemy session.
            item_id: ID of the object to archive.

        Raises:
            ValueError: If object is not found or lacks an 'archived' field.
            SQLAlchemyError: If a database error occurs during the commit.
        """
        try:
            obj = db.query(cls).filter_by(id=item_id).first()

            if not obj or not hasattr(obj, "archived"):
                error = f"{cls.__name__} with ID={item_id} not found"
                logger.exception(error)
                raise ValueError(error)

            obj.archived = True
            db.commit()

        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            logger.exception(e)
            raise
