from langchain_core.messages import HumanMessage, AIMessage

from agent.memory import ConversationMemory


def test_save_and_restore_conversation(tmp_path):

    memory = ConversationMemory(
        tmp_path / "test_memory.db"
    )

    messages = [
        HumanMessage(content="Hello SmartTools"),
        AIMessage(content="Hello! How can I help you?")
    ]

    memory.save(messages, "session_1")

    restored = memory.load("session_1")

    assert len(restored) == 2
    assert restored[0].content == "Hello SmartTools"
    assert restored[1].content == "Hello! How can I help you?"


def test_conversation_count(tmp_path):

    memory = ConversationMemory(
        tmp_path / "test_memory.db"
    )

    memory.save([
        HumanMessage(content="Hello"),
        AIMessage(content="Hi")
    ], "session_1")

    assert memory.count("session_1") == 2


def test_clear_conversation(tmp_path):

    memory = ConversationMemory(
        tmp_path / "test_memory.db"
    )

    memory.save([
        HumanMessage(content="Hello")
    ], "session_1")

    memory.clear("session_1")

    assert memory.load("session_1") == []
    assert memory.count("session_1") == 0


def test_sessions_are_isolated(tmp_path):

    memory = ConversationMemory(
        tmp_path / "test_memory.db"
    )

    memory.save([
        HumanMessage(content="Session one")
    ], "session_1")

    memory.save([
        HumanMessage(content="Session two")
    ], "session_2")

    assert memory.load("session_1")[0].content == "Session one"
    assert memory.load("session_2")[0].content == "Session two"