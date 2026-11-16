"""
UNIT & INTEGRATION TESTS: RELATIONAL SQL (JOINS, TRANSACTIONS, ORM) & NoSQL DOCUMENT STORE
"""

import pytest
import time
from database import RelationalRepository, MongoDocumentStore, User, TaskAuditLog


def test_relational_transaction_and_user_creation():
    username = f"tester_{int(time.time() * 1000)}"
    email = f"{username}@jarvis.local"

    user = RelationalRepository.create_user_with_session(
        username=username,
        email=email,
        password_hash="fake_hash_123",
        role="operator"
    )

    assert user.id is not None
    assert user.username == username
    assert len(user.sessions) >= 1


def test_relational_sql_joins_and_audit():
    username = f"audit_user_{int(time.time() * 1000)}"
    user = RelationalRepository.create_user_with_session(
        username=username,
        email=f"{username}@jarvis.local",
        password_hash="pwd_hash_456"
    )

    RelationalRepository.log_task_audit(
        action_type="tool_execution",
        tool_name="get_system_health",
        status="SUCCESS",
        duration_ms=45.2,
        user_id=user.id,
        details="Diagnostic completed"
    )

    logs = RelationalRepository.get_user_audit_logs_with_join(username)
    assert len(logs) >= 1
    assert logs[0]["username"] == username
    assert logs[0]["tool_name"] == "get_system_health"
    assert logs[0]["status"] == "SUCCESS"


def test_nosql_document_crud_and_aggregation():
    store = MongoDocumentStore()
    doc_id = store.insert_one({
        "title": "System Note",
        "category": "performance",
        "latency_ms": 25,
        "tags": ["core", "benchmark"],
        "embedded_profile": {"theme": "holographic"}
    })

    # Read / Find
    found = store.find({"category": "performance"})
    assert len(found) >= 1

    # Update
    assert store.update_one({"_id": doc_id}, {"latency_ms": 30}) is True
    updated = store.find({"_id": doc_id})
    assert updated[0]["latency_ms"] == 30

    # Aggregation Pipeline
    pipeline = [
        {"$match": {"category": "performance"}},
        {"$group": {"_id": "$category", "total_count": {"$count": 1}}},
        {"$sort": {"total_count": -1}}
    ]
    agg_res = store.aggregate(pipeline)
    assert len(agg_res) >= 1
    assert agg_res[0]["total_count"] >= 1

    # Delete
    assert store.delete_one({"_id": doc_id}) is True
