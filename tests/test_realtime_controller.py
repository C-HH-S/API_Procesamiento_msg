import pytest
from unittest.mock import patch

def test_broadcast_new_message_calls_emit():
    """Prueba que broadcast_new_message emite un evento con los datos correctos."""
    from app.controllers import realtime_controller

    fake_data = {"message_id": "123", "content": "Hola mundo"}

    with patch.object(realtime_controller, "socketio") as mock_socketio:
        realtime_controller.broadcast_new_message(fake_data)
        mock_socketio.emit.assert_called_once_with("new_message", fake_data)


def test_handle_connect_prints_sid(monkeypatch, capsys):
    """Prueba que handle_connect imprime el SID al conectarse."""
    from app.controllers import realtime_controller

    class FakeRequest:
        sid = "fake-sid-123"

    monkeypatch.setattr(realtime_controller, "request", FakeRequest)

    realtime_controller.handle_connect()
    captured = capsys.readouterr()
    assert "Cliente SocketIO conectado: fake-sid-123" in captured.out


def test_handle_disconnect_prints_sid(monkeypatch, capsys):
    """Prueba que handle_disconnect imprime el SID al desconectarse."""
    from app.controllers import realtime_controller

    class FakeRequest:
        sid = "fake-sid-999"

    monkeypatch.setattr(realtime_controller, "request", FakeRequest)

    realtime_controller.handle_disconnect()
    captured = capsys.readouterr()
    assert "Cliente SocketIO desconectado: fake-sid-999" in captured.out
