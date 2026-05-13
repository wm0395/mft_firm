from project.signals import hello_world


def test_hello_world_returns_literal() -> None:
    assert hello_world() == "hello world"
