"""
How a node's outputs reach the next node.

The engine merges every source node's outputs into the target's inputs using rules keyed
by the source node's type. Nodes whose answer is not called "output" need a rule, or their
result only survives under a prefixed key and never reaches the next node.
"""

import pytest

from backend.core.engine.data_collector import DataCollector
from backend.core.models import Edge, Node, Position, Workflow


def workflow_with(source_type: str, target_type: str = "email") -> Workflow:
    return Workflow(
        name="flow",
        nodes=[
            Node(id="src", type=source_type, position=Position(x=0, y=0), data={}),
            Node(id="dst", type=target_type, position=Position(x=200, y=0), data={}),
        ],
        edges=[Edge(id="e1", source="src", target="dst")],
    )


def merge(source_type: str, outputs: dict, target_type: str = "email") -> dict:
    workflow = workflow_with(source_type, target_type)
    source_data = DataCollector.collect_source_data(workflow, "dst", {"src": outputs})
    return DataCollector.smart_merge_sources(source_data, target_type, workflow, "dst")


@pytest.mark.unit
class TestOutputsReachTheNextNode:
    def test_text_input_sets_text(self):
        assert merge("text_input", {"text": "hello"})["text"] == "hello"

    def test_mcp_tool_result_reaches_next_node(self):
        inputs = merge("mcp_tool", {"text": "found 2 records", "result": {"content": []},
                                    "server": "acme", "tool": "search"})
        assert inputs["text"] == "found 2 records"
        assert inputs["content"] == "found 2 records"

    def test_chat_answer_reaches_next_node(self):
        inputs = merge("chat", {"response": "the answer", "model": "claude-sonnet-5", "cost": 0.01})
        assert inputs["text"] == "the answer"

    def test_raw_outputs_still_available_under_prefixed_keys(self):
        inputs = merge("mcp_tool", {"text": "t", "server": "acme", "tool": "search"})
        assert inputs["src_server"] == "acme" and inputs["src_tool"] == "search"

    def test_mcp_tool_feeds_a_chat_node(self):
        inputs = merge("mcp_tool", {"text": "records: 2"}, target_type="chat")
        assert inputs["text"] == "records: 2"


@pytest.mark.unit
class TestMCPToolNodeReceivesUpstreamValue:
    """The node fills {input} in its arguments from whatever the previous node produced."""

    @pytest.mark.parametrize("inputs,expected", [
        ({"input": "direct"}, "direct"),
        ({"text": "from text"}, "from text"),
        ({"content": "from content"}, "from content"),
        ({"response": "from chat"}, "from chat"),
        ({"query": "from query"}, "from query"),
    ])
    def test_placeholder_sources(self, inputs, expected):
        from backend.nodes.tools.mcp_tool_node import MCPToolNode

        arguments = MCPToolNode()._build_arguments({"arguments": {"q": "{input}"}}, inputs)
        assert arguments == {"q": expected}

    def test_other_input_keys_are_addressable(self):
        from backend.nodes.tools.mcp_tool_node import MCPToolNode

        arguments = MCPToolNode()._build_arguments(
            {"arguments": {"channel": "{channel}", "body": "{input}"}},
            {"channel": "#general", "text": "hi"},
        )
        assert arguments == {"channel": "#general", "body": "hi"}
