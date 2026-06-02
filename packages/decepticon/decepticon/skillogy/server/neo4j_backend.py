"""Neo4j-backed storage for the skillogy service.

Replaces the in-memory ``SkillRegistry`` (kept in ``registry.py`` for
the migration window). The server now opens a Bolt session to the same
Neo4j instance that ``skillogy.builder`` populates via ``skills.cypher``.

The wire protocol stays the same — the same ``SkillEnvelope`` /
``SkillMeta`` proto types are returned — but every read now answers from
the live graph instead of an in-memory dict.

Read-only enforcement
---------------------
Server-driven Cypher (``run_cypher_read`` RPC, Phase 1b-onwards
``recall``) is the obvious attack surface. The backend enforces three
defenses, layered: ``default_access_mode=READ`` on the Bolt session
(server-side), AST-style keyword denylist applied to the inbound
``query`` string (belt-and-suspenders), and a per-query parameter cap
+ row-count cap so a malformed query can't exhaust the agent context.
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# Write-mode Cypher keywords we refuse to forward, even though the
# Neo4j driver session is also opened in READ mode. The check is
# whole-word, case-insensitive, after stripping line comments + string
# literals so a benign body like "// MERGE example" cannot be flagged.
_WRITE_KEYWORDS = (
    "CREATE",
    "MERGE",
    "SET",
    "DELETE",
    "DETACH",
    "REMOVE",
    "DROP",
    "LOAD",
    "USING PERIODIC COMMIT",
    "FOREACH",
)


class CypherWriteRejected(ValueError):
    """Raised when a client query trips the write-keyword denylist."""


_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_STRING_RE = re.compile(r"'([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\"")
_WORD_BOUNDARY = r"(?<![A-Za-z_])({kw})(?![A-Za-z_])"


def _strip_noise(query: str) -> str:
    """Drop line comments + string literals before keyword scanning."""
    no_comments = _LINE_COMMENT_RE.sub("", query)
    return _STRING_RE.sub("''", no_comments)


def assert_read_only(query: str) -> None:
    """Raise ``CypherWriteRejected`` if ``query`` contains a write keyword."""
    cleaned = _strip_noise(query)
    for kw in _WRITE_KEYWORDS:
        pattern = _WORD_BOUNDARY.format(kw=re.escape(kw))
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            raise CypherWriteRejected(
                f"Cypher write keyword {kw!r} is not allowed in read-only RPC"
            )


class Neo4jBackend:
    """Thin Bolt wrapper used by the FastAPI / grpcio server.

    Created once at server boot, shared across requests. Holds a single
    driver instance; sessions are short-lived (request-scoped). The
    driver is closed in ``close()`` so unit tests with testcontainers
    can tear it down deterministically.
    """

    def __init__(
        self,
        *,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        max_rows: int = 200,
    ) -> None:
        try:
            from neo4j import GraphDatabase  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "Skillogy server requires the neo4j driver. "
                "Install with: pip install neo4j>=5.24"
            ) from exc
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database
        self._max_rows = max_rows

    def close(self) -> None:
        self._driver.close()

    # ---- skill ops ----

    def load_skill(self, path: str) -> dict[str, Any] | None:
        """Fetch one ``:Skill`` node by canonical path. Returns its full
        property dict, or ``None`` if no such skill exists."""
        query = "MATCH (s:Skill {path: $path}) RETURN properties(s) AS props"
        with self._driver.session(database=self._database, default_access_mode="READ") as session:
            result = session.run(query, path=path).single()
        return None if result is None else dict(result["props"])

    def health(self) -> dict[str, Any]:
        """Return service liveness + a count of :Skill nodes in the graph."""
        query = "MATCH (s:Skill) RETURN count(s) AS skill_count"
        with self._driver.session(database=self._database, default_access_mode="READ") as session:
            result = session.run(query).single()
        skill_count = 0 if result is None else int(result["skill_count"])
        return {"status": "ok", "skill_count": skill_count}

    # ---- read-only cypher escape hatch (used by run_cypher_read RPC, Phase 1a) ----

    def run_cypher_read(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute an agent-supplied read-only Cypher query.

        ``assert_read_only`` is the syntactic guard; the Bolt session's
        ``default_access_mode='READ'`` is the server-side guard. Results
        are capped at ``self._max_rows`` so a runaway query cannot exhaust
        the agent context window or wire bandwidth.
        """
        assert_read_only(query)
        with self._driver.session(database=self._database, default_access_mode="READ") as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result.fetch(self._max_rows)]
