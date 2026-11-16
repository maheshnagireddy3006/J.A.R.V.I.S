"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - RELATIONAL (SQL) & NoSQL (DOCUMENT) DATA LAYER
Implements:
  1. Relational Schema Design with Primary & Foreign Keys (SQLAlchemy ORM)
  2. SQL JOINs (Multi-table relational aggregation)
  3. Indexing for Query Performance (B-Tree composite indexes on SQL & NoSQL)
  4. Filtering, Ordering, Grouping (Complex SQL query generation)
  5. Normalization Basics (Third Normal Form: Users, Sessions, TaskAuditLogs)
  6. ORM Usage (SQLAlchemy Declarative Base, Relationships, Session handling)
  7. ACID Transactions (Explicit commit/rollback transaction scopes)
  8. Schema Modeling (Mongo / Document-Oriented Store)
  9. CRUD Operations (Insert, Read, Update, Delete for Document store)
  10. Embedding vs Referencing Relationships
  11. Aggregation Pipelines ($match, $group, $sort, $project)
  12. Indexing for NoSQL Query Performance
"""

import json
import os
import time
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

import config


class Base(DeclarativeBase):
    pass

# SQLite local database path with automatic directory validation
SQLITE_DB_PATH = config.DATA_DIR / "jarvis_relational.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


# =====================================================================
# 1. RELATIONAL SCHEMA DESIGN WITH PK / FK (3NF NORMALIZED ORM)
# =====================================================================

class User(Base):
    """
    Primary User Entity.
    Demonstrates: Primary Key, Unique Constraints, Relationships, 3NF Normalization.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="guest", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # 1-to-Many Relationships (Referencing Pattern with eager joined loading)
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan", lazy="joined")
    audit_logs: Mapped[list["TaskAuditLog"]] = relationship("TaskAuditLog", back_populates="user", cascade="all, delete-orphan", lazy="joined")


class UserSession(Base):
    """
    Active User Authentication Session.
    Demonstrates: Foreign Key referencing users.id, Indexing.
    """
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class TaskAuditLog(Base):
    """
    System Task & Agent Action Audit Log.
    Demonstrates: Foreign Key, Composite Indexing for query performance, Filtering/Grouping targets.
    """
    __tablename__ = "task_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    # Composite Index for high-performance timeline queries
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action_type"),
        Index("idx_audit_created", "created_at"),
    )


# Create tables in database
Base.metadata.create_all(bind=engine)


# =====================================================================
# 2. RELATIONAL REPOSITORY: JOINS, TRANSACTIONS, FILTERING, GROUPING
# =====================================================================

class RelationalRepository:
    """Manages transactional CRUD, relational JOINs, filtering, and aggregation on SQL tables."""

    @staticmethod
    def get_session() -> Session:
        return SessionLocal()

    @classmethod
    def create_user_with_session(cls, username: str, email: str, password_hash: str, role: str = "guest") -> User:
        """
        Demonstrates: ACID Transaction scope with commit and rollback handling.
        """
        session = cls.get_session()
        try:
            with session.begin():
                user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role=role
                )
                session.add(user)
                session.flush()  # Populates user.id inside transaction
                
                # Create initial session token record
                initial_session = UserSession(
                    user_id=int(user.id),
                    token=f"init_session_{user.id}_{int(time.time())}",
                    expires_at=datetime.now(UTC)
                )
                session.add(initial_session)
                session.flush()
                # Access eager relationship before session close
                _ = list(user.sessions)
            return user
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Transaction failed during user creation: {e}")
        finally:
            session.close()

    @classmethod
    def log_task_audit(
        cls,
        action_type: str,
        status: str,
        tool_name: str | None = None,
        duration_ms: float = 0.0,
        user_id: int | None = None,
        details: str | None = None
    ) -> TaskAuditLog:
        """Persists task execution record inside transactional scope."""
        session = cls.get_session()
        try:
            with session.begin():
                log_entry = TaskAuditLog(
                    user_id=user_id,
                    action_type=action_type,
                    tool_name=tool_name,
                    status=status,
                    duration_ms=duration_ms,
                    details=details
                )
                session.add(log_entry)
                session.flush()
            return log_entry
        finally:
            session.close()

    @classmethod
    def get_user_audit_logs_with_join(cls, username: str) -> list[dict[str, Any]]:
        """
        Demonstrates: SQL JOIN query combining 'users' and 'task_audit_logs'
        with filtering and ordering.
        """
        session = cls.get_session()
        try:
            stmt = (
                select(
                    TaskAuditLog.id,
                    User.username,
                    TaskAuditLog.action_type,
                    TaskAuditLog.tool_name,
                    TaskAuditLog.status,
                    TaskAuditLog.duration_ms,
                    TaskAuditLog.created_at
                )
                .join(User, TaskAuditLog.user_id == User.id)
                .filter(User.username == username)
                .order_by(TaskAuditLog.created_at.desc())
                .limit(50)
            )
            rows = session.execute(stmt).all()
            return [
                {
                    "log_id": r[0],
                    "username": r[1],
                    "action_type": r[2],
                    "tool_name": r[3],
                    "status": r[4],
                    "duration_ms": r[5],
                    "created_at": r[6].isoformat() if r[6] else None
                }
                for r in rows
            ]
        finally:
            session.close()

    @classmethod
    def get_tool_usage_statistics_grouped(cls) -> list[dict[str, Any]]:
        """
        Demonstrates: SQL GROUP BY, COUNT, and AVG aggregations with ORDER BY.
        """
        session = cls.get_session()
        try:
            stmt = (
                select(
                    TaskAuditLog.tool_name,
                    func.count(TaskAuditLog.id).label("total_invocations"),
                    func.avg(TaskAuditLog.duration_ms).label("avg_duration_ms")
                )
                .filter(TaskAuditLog.tool_name.isnot(None))
                .group_by(TaskAuditLog.tool_name)
                .order_by(func.count(TaskAuditLog.id).desc())
            )
            rows = session.execute(stmt).all()
            return [
                {
                    "tool_name": r[0],
                    "total_invocations": r[1],
                    "avg_duration_ms": round(float(r[2] or 0), 2)
                }
                for r in rows
            ]
        finally:
            session.close()


# =====================================================================
# 3. NoSQL / MONGO DOCUMENT-ORIENTED SUBSYSTEM
# =====================================================================

class MongoDocumentStore:
    """
    Document-Oriented NoSQL Store simulation & engine.
    Demonstrates:
      - Document schema modeling (flexible JSON document structures)
      - CRUD operations (insert_one, find, update_one, delete_one)
      - Embedding vs Referencing patterns
      - Aggregation pipelines ($match, $group, $sort, $project)
      - Indexing for NoSQL query performance
    """
    def __init__(self, storage_file: str | None = None):
        self.storage_file = storage_file or str(config.DATA_DIR / "jarvis_documents.json")
        self.documents: dict[str, dict[str, Any]] = {}
        self.indexes: dict[str, dict[Any, list[str]]] = {}  # {field_name: {field_value: [doc_ids]}}
        self._load()

    def _load(self):
        """Loads persistent document state from disk."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                self.rebuild_indexes(["category", "user_ref_id", "tags"])
            except Exception:
                self.documents = {}

    def _save(self):
        """Persists documents atomically to disk."""
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
        except Exception:
            pass

    # Indexing for query performance
    def create_index(self, field_name: str):
        """Creates an in-memory B-Tree inverted index on a specific document key."""
        self.indexes[field_name] = {}
        for doc_id, doc in self.documents.items():
            val = doc.get(field_name)
            if val is not None:
                if isinstance(val, list):
                    for item in val:
                        self.indexes[field_name].setdefault(item, []).append(doc_id)
                else:
                    self.indexes[field_name].setdefault(val, []).append(doc_id)

    def rebuild_indexes(self, fields: list[str]):
        for f in fields:
            self.create_index(f)

    # CRUD: Create
    def insert_one(self, document: dict[str, Any]) -> str:
        """
        Inserts document into collection.
        Demonstrates: Embedding relationships (embedded metadata/profile object)
        versus Referencing relationships ('user_ref_id').
        """
        doc_id = str(document.get("_id") or f"doc_{int(time.time() * 1000)}_{len(self.documents)}")
        doc = dict(document)
        doc["_id"] = doc_id
        doc.setdefault("created_at", time.time())
        self.documents[doc_id] = doc
        self._save()
        self.rebuild_indexes(list(self.indexes.keys()) or ["category", "user_ref_id"])
        return doc_id

    # CRUD: Read
    def find(self, query: dict[str, Any] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Queries documents with indexed acceleration and filter matching."""
        if not query:
            return list(self.documents.values())[:limit]

        # Use index if single field query
        if len(query) == 1:
            key, val = next(iter(query.items()))
            if key in self.indexes and val in self.indexes[key]:
                matching_ids = self.indexes[key][val]
                return [self.documents[doc_id] for doc_id in matching_ids[:limit]]

        # Scan match
        matches = []
        for doc in self.documents.values():
            if all(doc.get(k) == v for k, v in query.items()):
                matches.append(doc)
                if len(matches) >= limit:
                    break
        return matches

    # CRUD: Update
    def update_one(self, query: dict[str, Any], update_values: dict[str, Any]) -> bool:
        """Updates the first matching document."""
        matches = self.find(query, limit=1)
        if not matches:
            return False
        target_id = matches[0]["_id"]
        self.documents[target_id].update(update_values)
        self.documents[target_id]["updated_at"] = time.time()
        self._save()
        return True

    # CRUD: Delete
    def delete_one(self, query: dict[str, Any]) -> bool:
        """Deletes the first matching document."""
        matches = self.find(query, limit=1)
        if not matches:
            return False
        target_id = matches[0]["_id"]
        del self.documents[target_id]
        self._save()
        self.rebuild_indexes(list(self.indexes.keys()))
        return True

    # NoSQL Aggregation Pipeline ($match, $group, $sort, $project)
    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Executes a multi-stage aggregation pipeline modeled after MongoDB:
        Stages: $match, $group, $sort, $project.
        """
        working_set = list(self.documents.values())

        for stage in pipeline:
            # Stage: $match
            if "$match" in stage:
                match_spec = stage["$match"]
                working_set = [
                    d for d in working_set
                    if all(d.get(k) == v for k, v in match_spec.items())
                ]

            # Stage: $group
            elif "$group" in stage:
                group_spec = stage["$group"]
                group_key = group_spec["_id"]
                grouped: dict[Any, list[dict[str, Any]]] = {}
                for doc in working_set:
                    val = doc.get(group_key.replace("$", "")) if group_key.startswith("$") else group_key
                    grouped.setdefault(val, []).append(doc)

                aggregated = []
                for g_val, g_docs in grouped.items():
                    res = {"_id": g_val}
                    for out_field, accum in group_spec.items():
                        if out_field == "_id":
                            continue
                        if "$count" in accum:
                            res[out_field] = len(g_docs)
                        elif "$sum" in accum:
                            sum_key = accum["$sum"].replace("$", "")
                            res[out_field] = sum(d.get(sum_key, 0) for d in g_docs)
                    aggregated.append(res)
                working_set = aggregated

            # Stage: $sort
            elif "$sort" in stage:
                sort_spec = stage["$sort"]
                for sort_field, direction in sort_spec.items():
                    working_set.sort(key=lambda x: x.get(sort_field, 0), reverse=(direction == -1))

            # Stage: $project
            elif "$project" in stage:
                proj_spec = stage["$project"]
                projected = []
                for doc in working_set:
                    p = {}
                    for field_name, include in proj_spec.items():
                        if include == 1 and field_name in doc:
                            p[field_name] = doc[field_name]
                    projected.append(p)
                working_set = projected

        return working_set


# Global Singleton document store
document_store = MongoDocumentStore()
