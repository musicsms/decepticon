"""``build_grpc_server`` must fail loud until the gRPC transport is wired.

The hand-rolled ``skillogy.proto`` has no protoc-generated bindings, so a
``grpc.Server`` built from it would bind a port but answer every RPC with
``UNIMPLEMENTED`` — a silent dead port. ``build_grpc_server`` therefore raises
``RuntimeError``, and ``__main__._start_grpc`` degrades gracefully to REST.
"""

from __future__ import annotations

import pytest

from decepticon.skillogy.server import SkillRegistry, build_grpc_server


def test_build_grpc_server_raises_until_wired() -> None:
    with pytest.raises(RuntimeError) as exc:
        build_grpc_server(SkillRegistry(), port=50051)
    msg = str(exc.value)
    assert "gRPC" in msg
    # The message must point operators at the supported transport.
    assert "REST" in msg


def test_start_grpc_degrades_to_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    """The boot path swallows the RuntimeError and returns None (no thread),
    so the REST server still comes up."""
    from decepticon.skillogy import __main__ as skillogy_main

    thread = skillogy_main._start_grpc(SkillRegistry(), 50051)
    assert thread is None
