"""
UNIT TESTS: MULTI-STEP AGENT, INTENT ROUTING, TOOLS & SELF-CORRECTION
"""

import pytest
from unittest.mock import patch, MagicMock
from brain import JarvisBrain, LocalTools


def test_local_tools_system_health():
    health = LocalTools.get_system_health()
    assert health["status"] == "success"
    assert "cpu" in health
    assert "ram" in health
    assert "disks" in health


def test_local_tools_forbidden_command_guard():
    with pytest.raises(PermissionError):
        LocalTools.execute_shell_command("format C: /q")


@patch("brain.MemorySubsystem")
def test_agent_graph_initialization(mock_memory):
    mock_memory.return_value = MagicMock()
    brain = JarvisBrain()
    assert brain.workflow is not None
    assert brain.tools is not None


@patch("brain.MemorySubsystem")
def test_agent_self_correction_routing(mock_memory):
    mock_memory.return_value = MagicMock()
    brain = JarvisBrain()
    # Simulating error state to test route_after_tool
    error_state = {
        "user_input": "Run test",
        "tool_name": "execute_shell_command",
        "error_trace": "Simulated error",
        "retry_count": 0
    }
    next_node = brain._route_after_tool(error_state)
    assert next_node == "error_recover"

    # Exhausted retries routes to fatal error
    exhausted_state = {
        "user_input": "Run test",
        "tool_name": "execute_shell_command",
        "error_trace": "Simulated error",
        "retry_count": 2
    }
    fatal_node = brain._route_after_tool(exhausted_state)
    assert fatal_node == "fatal_error"
