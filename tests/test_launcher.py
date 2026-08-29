import socket

import app as launcher


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_port_in_use(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", lambda *_args, **_kwargs: FakeConnection())
    assert launcher.port_is_in_use("127.0.0.1", 8000) is True


def test_port_available(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise ConnectionRefusedError

    monkeypatch.setattr(socket, "create_connection", unavailable)
    assert launcher.port_is_in_use("127.0.0.1", 8000) is False
