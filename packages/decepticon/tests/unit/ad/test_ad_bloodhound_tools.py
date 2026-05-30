"""Comprehensive tests for tools/ad/bloodhound.py and tools/ad/tools.py.

Covers:
- bloodhound.py: ImportStats, _node_kind_for_bh, _build_bh_index,
  _ingest_aces, _ingest_memberships, merge_bloodhound_json, ingest_bloodhound_zip
- tools.py: bh_ingest_zip, bh_ingest_json (JSON output shapes + error paths)

All tests are deterministic and offline — no network, Neo4j, or filesystem
services required.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from decepticon.tools.ad.bloodhound import (
    _BH_EDGE_MAP,
    ImportStats,
    _build_bh_index,
    _ingest_aces,
    _ingest_memberships,
    _node_kind_for_bh,
    _upsert_bh_object,
    ingest_bloodhound_zip,
    merge_bloodhound_json,
)
from decepticon_core.types.kg import EdgeKind, KnowledgeGraph, Node, NodeKind

# ── ImportStats ──────────────────────────────────────────────────────────────


class TestImportStats:
    def test_defaults_are_zero(self) -> None:
        s = ImportStats()
        assert s.users == 0
        assert s.computers == 0
        assert s.groups == 0
        assert s.domains == 0
        assert s.gpos == 0
        assert s.ous == 0
        assert s.edges == 0

    def test_to_dict_returns_all_fields(self) -> None:
        s = ImportStats(users=3, computers=1, groups=2, domains=1, gpos=0, ous=1, edges=10)
        d = s.to_dict()
        assert d["users"] == 3
        assert d["computers"] == 1
        assert d["groups"] == 2
        assert d["domains"] == 1
        assert d["gpos"] == 0
        assert d["ous"] == 1
        assert d["edges"] == 10

    def test_to_dict_has_exactly_seven_keys(self) -> None:
        d = ImportStats().to_dict()
        assert set(d.keys()) == {"users", "computers", "groups", "domains", "gpos", "ous", "edges"}


# ── _node_kind_for_bh ────────────────────────────────────────────────────────


class TestNodeKindForBh:
    def test_user_maps_to_user(self) -> None:
        assert _node_kind_for_bh("User") == NodeKind.USER

    def test_computer_maps_to_host(self) -> None:
        assert _node_kind_for_bh("Computer") == NodeKind.HOST

    def test_group_maps_to_group(self) -> None:
        assert _node_kind_for_bh("Group") == NodeKind.GROUP

    def test_domain_maps_to_domain(self) -> None:
        assert _node_kind_for_bh("Domain") == NodeKind.DOMAIN

    def test_gpo_maps_to_group(self) -> None:
        # GPOs are modelled as policy containers (GROUP)
        assert _node_kind_for_bh("GPO") == NodeKind.GROUP

    def test_ou_maps_to_group(self) -> None:
        # OUs are modelled as organizational containers (GROUP)
        assert _node_kind_for_bh("OU") == NodeKind.GROUP

    def test_unknown_type_falls_back_to_host(self) -> None:
        assert _node_kind_for_bh("WhateverUnknown") == NodeKind.HOST


# ── _BH_EDGE_MAP coverage ────────────────────────────────────────────────────


class TestBhEdgeMap:
    def test_dcsync_maps_to_leaks_low_weight(self) -> None:
        kind, weight = _BH_EDGE_MAP["DCSync"]
        assert kind == EdgeKind.LEAKS
        assert weight <= 0.2

    def test_admin_to_maps_to_admin_to(self) -> None:
        kind, weight = _BH_EDGE_MAP["AdminTo"]
        assert kind == EdgeKind.ADMIN_TO

    def test_member_of_maps_to_member_of(self) -> None:
        kind, weight = _BH_EDGE_MAP["MemberOf"]
        assert kind == EdgeKind.MEMBER_OF

    def test_has_session_maps_to_has_session(self) -> None:
        kind, weight = _BH_EDGE_MAP["HasSession"]
        assert kind == EdgeKind.HAS_SESSION

    def test_generic_all_maps_to_enables(self) -> None:
        kind, _ = _BH_EDGE_MAP["GenericAll"]
        assert kind == EdgeKind.ENABLES

    def test_read_laps_maps_to_leaks(self) -> None:
        kind, _ = _BH_EDGE_MAP["ReadLAPSPassword"]
        assert kind == EdgeKind.LEAKS

    def test_owns_maps_to_owns(self) -> None:
        kind, _ = _BH_EDGE_MAP["Owns"]
        assert kind == EdgeKind.OWNS

    def test_contains_maps_to_contains(self) -> None:
        kind, _ = _BH_EDGE_MAP["Contains"]
        assert kind == EdgeKind.CONTAINS

    def test_all_weights_are_positive(self) -> None:
        for name, (kind, weight) in _BH_EDGE_MAP.items():
            assert weight > 0, f"{name} has non-positive weight"


# ── _upsert_bh_object ────────────────────────────────────────────────────────


class TestUpsertBhObject:
    def test_creates_user_node_with_correct_props(self) -> None:
        g = KnowledgeGraph()
        obj = {
            "ObjectIdentifier": "S-1-5-21-1-1-1-500",
            "Properties": {
                "name": "admin@corp.local",
                "domain": "CORP.LOCAL",
                "admincount": True,
                "enabled": True,
                "hasspn": False,
            },
        }
        node = _upsert_bh_object(g, obj, "User")
        assert node.kind == NodeKind.USER
        assert node.label == "admin@corp.local"
        assert node.props["bh_id"] == "S-1-5-21-1-1-1-500"
        assert node.props["bh_type"] == "User"
        assert node.props["domain"] == "CORP.LOCAL"
        assert node.props["admincount"] is True
        assert node.props["enabled"] is True

    def test_computer_node_kind(self) -> None:
        g = KnowledgeGraph()
        obj = {
            "ObjectIdentifier": "S-1-5-21-99-1000",
            "Properties": {"name": "DC01.CORP.LOCAL"},
        }
        node = _upsert_bh_object(g, obj, "Computer")
        assert node.kind == NodeKind.HOST

    def test_fallback_label_uses_object_identifier(self) -> None:
        g = KnowledgeGraph()
        obj = {"ObjectIdentifier": "S-1-5-NOPROPS", "Properties": {}}
        node = _upsert_bh_object(g, obj, "User")
        assert node.label == "S-1-5-NOPROPS"

    def test_fallback_label_uses_unknown_when_no_id(self) -> None:
        g = KnowledgeGraph()
        obj: dict = {"Properties": {}}
        node = _upsert_bh_object(g, obj, "User")
        assert node.label == "unknown"

    def test_key_format(self) -> None:
        g = KnowledgeGraph()
        obj = {"ObjectIdentifier": "SID123", "Properties": {"name": "x"}}
        node = _upsert_bh_object(g, obj, "Group")
        assert node.props["key"] == "bh::Group::SID123"

    def test_node_is_added_to_graph(self) -> None:
        g = KnowledgeGraph()
        obj = {"ObjectIdentifier": "SID-ADD", "Properties": {"name": "tgt"}}
        _upsert_bh_object(g, obj, "User")
        assert g.stats()["nodes"] == 1


# ── _build_bh_index ──────────────────────────────────────────────────────────


class TestBuildBhIndex:
    def test_empty_graph_returns_empty_dict(self) -> None:
        g = KnowledgeGraph()
        assert _build_bh_index(g) == {}

    def test_index_contains_inserted_nodes(self) -> None:
        g = KnowledgeGraph()
        bh = {
            "meta": {"type": "users"},
            "data": [
                {"ObjectIdentifier": "S-IDX-1", "Properties": {"name": "u1"}},
                {"ObjectIdentifier": "S-IDX-2", "Properties": {"name": "u2"}},
            ],
        }
        merge_bloodhound_json(bh, g)
        idx = _build_bh_index(g)
        assert "S-IDX-1" in idx
        assert "S-IDX-2" in idx

    def test_index_maps_to_correct_node(self) -> None:
        g = KnowledgeGraph()
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-MAP-1", "Properties": {"name": "mapped"}}],
        }
        merge_bloodhound_json(bh, g)
        idx = _build_bh_index(g)
        node = idx["S-MAP-1"]
        assert node.label == "mapped"


# ── _ingest_aces ─────────────────────────────────────────────────────────────


class TestIngestAces:
    def _setup(self) -> tuple[KnowledgeGraph, Node, dict[str, Node]]:
        g = KnowledgeGraph()
        obj = {
            "ObjectIdentifier": "S-SRC-1",
            "Properties": {"name": "source"},
        }
        from decepticon.tools.ad.bloodhound import _upsert_bh_object

        src = _upsert_bh_object(g, obj, "User")
        bh_index = _build_bh_index(g)
        return g, src, bh_index

    def test_known_right_creates_edge_with_correct_kind(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"RightName": "AdminTo", "PrincipalSID": "S-PRINC-1"}]}
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 1
        # Verify at least one edge with ADMIN_TO kind
        edge_kinds = {e.kind for e in g.edges.values()}
        assert EdgeKind.ADMIN_TO in edge_kinds

    def test_unknown_right_defaults_to_enables(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"RightName": "SomeFutureRight", "PrincipalSID": "S-PRINC-X"}]}
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 1
        edge_kinds = {e.kind for e in g.edges.values()}
        assert EdgeKind.ENABLES in edge_kinds

    def test_missing_right_skips_ace(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"PrincipalSID": "S-NRIGHT"}]}  # no RightName
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 0

    def test_missing_principal_sid_skips_ace(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"RightName": "GenericAll"}]}  # no PrincipalSID
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 0

    def test_empty_aces_produces_no_edges(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        _ingest_aces(g, src, {}, stats, bh_index)
        assert stats.edges == 0

    def test_principal_not_in_index_creates_placeholder_node(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"RightName": "GenericAll", "PrincipalSID": "S-NEW-999"}]}
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert "S-NEW-999" in bh_index
        assert bh_index["S-NEW-999"].label == "S-NEW-999"

    def test_multiple_aces_count_correctly(self) -> None:
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {
            "Aces": [
                {"RightName": "GenericAll", "PrincipalSID": "S-A"},
                {"RightName": "WriteDacl", "PrincipalSID": "S-B"},
                {"RightName": "DCSync", "PrincipalSID": "S-C"},
            ]
        }
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 3

    def test_lowercase_field_names_are_accepted(self) -> None:
        # BloodHound CE uses lowercase field names in some exports
        g, src, bh_index = self._setup()
        stats = ImportStats()
        ace_obj = {"Aces": [{"rightname": "Owns", "principalid": "S-LOWER"}]}
        _ingest_aces(g, src, ace_obj, stats, bh_index)
        assert stats.edges == 1


# ── _ingest_memberships ──────────────────────────────────────────────────────


class TestIngestMemberships:
    def _setup(self) -> tuple[KnowledgeGraph, Node, dict[str, Node]]:
        g = KnowledgeGraph()
        obj = {"ObjectIdentifier": "S-MEM-SRC", "Properties": {"name": "member_user"}}
        from decepticon.tools.ad.bloodhound import _upsert_bh_object

        node = _upsert_bh_object(g, obj, "User")
        bh_index = _build_bh_index(g)
        return g, node, bh_index

    def test_membership_creates_member_of_edge(self) -> None:
        g, node, bh_index = self._setup()
        stats = ImportStats()
        mem_obj = {"MemberOf": [{"ObjectIdentifier": "S-GROUP-1"}]}
        _ingest_memberships(g, node, mem_obj, stats, bh_index)
        assert stats.edges == 1
        edge_kinds = {e.kind for e in g.edges.values()}
        assert EdgeKind.MEMBER_OF in edge_kinds

    def test_empty_memberships_produces_no_edges(self) -> None:
        g, node, bh_index = self._setup()
        stats = ImportStats()
        _ingest_memberships(g, node, {}, stats, bh_index)
        assert stats.edges == 0

    def test_group_not_in_index_creates_placeholder(self) -> None:
        g, node, bh_index = self._setup()
        stats = ImportStats()
        mem_obj = {"MemberOf": [{"ObjectIdentifier": "S-NEW-GROUP"}]}
        _ingest_memberships(g, node, mem_obj, stats, bh_index)
        assert "S-NEW-GROUP" in bh_index

    def test_dict_item_without_object_identifier_is_skipped(self) -> None:
        # A dict membership entry missing ObjectIdentifier resolves to the dict
        # itself (truthy, non-string) — isinstance check skips it.
        g, node, bh_index = self._setup()
        stats = ImportStats()
        mem_obj = {"MemberOf": [{"SomethingElse": "no-id"}]}
        _ingest_memberships(g, node, mem_obj, stats, bh_index)
        assert stats.edges == 0

    def test_multiple_memberships_count(self) -> None:
        g, node, bh_index = self._setup()
        stats = ImportStats()
        mem_obj = {
            "MemberOf": [
                {"ObjectIdentifier": "S-G1"},
                {"ObjectIdentifier": "S-G2"},
            ]
        }
        _ingest_memberships(g, node, mem_obj, stats, bh_index)
        assert stats.edges == 2


# ── merge_bloodhound_json ────────────────────────────────────────────────────


class TestMergeBloodhoundJson:
    # -- Basic type handling --

    def test_dict_input_processes_users(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-U1", "Properties": {"name": "u1"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 1

    def test_json_string_input_is_accepted(self) -> None:
        bh = json.dumps(
            {
                "meta": {"type": "computers"},
                "data": [{"ObjectIdentifier": "S-C1", "Properties": {"name": "ws1"}}],
            }
        )
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.computers == 1

    def test_groups_type_counts_correctly(self) -> None:
        bh = {
            "meta": {"type": "groups"},
            "data": [
                {"ObjectIdentifier": "S-GRP-1", "Properties": {"name": "Domain Admins"}},
                {"ObjectIdentifier": "S-GRP-2", "Properties": {"name": "Domain Users"}},
            ],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.groups == 2

    def test_domains_type_counts_correctly(self) -> None:
        bh = {
            "meta": {"type": "domains"},
            "data": [{"ObjectIdentifier": "S-DOM-1", "Properties": {"name": "CORP.LOCAL"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.domains == 1

    def test_gpos_type_counts_correctly(self) -> None:
        bh = {
            "meta": {"type": "gpos"},
            "data": [{"ObjectIdentifier": "GPO-UUID-1", "Properties": {"name": "Default GPO"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.gpos == 1

    def test_ous_type_counts_correctly(self) -> None:
        bh = {
            "meta": {"type": "ous"},
            "data": [{"ObjectIdentifier": "OU-UUID-1", "Properties": {"name": "Servers OU"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.ous == 1

    # -- type_hint override --

    def test_type_hint_overrides_meta_type(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-TH", "Properties": {"name": "override"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g, type_hint="Computers")
        assert stats.computers == 1
        assert stats.users == 0

    # -- items vs data key --

    def test_items_key_accepted(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "items": [{"ObjectIdentifier": "S-IT-1", "Properties": {"name": "ituser"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 1

    # -- List / BH-CE format --

    def test_top_level_list_is_valid(self) -> None:
        bh_list = [
            {
                "meta": {"type": "users"},
                "data": [{"ObjectIdentifier": "S-L1", "Properties": {"name": "lu1"}}],
            },
            {
                "meta": {"type": "computers"},
                "data": [{"ObjectIdentifier": "S-L2", "Properties": {"name": "lc1"}}],
            },
        ]
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(cast(Any, bh_list), g)
        assert stats.users == 1
        assert stats.computers == 1

    def test_empty_list_produces_zero_stats(self) -> None:
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(cast(Any, []), g)
        assert stats.users == 0
        assert stats.edges == 0

    # -- Error handling --

    def test_invalid_json_string_raises_value_error(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(ValueError, match="invalid JSON"):
            merge_bloodhound_json("{not json}", g)

    def test_top_level_scalar_raises_value_error(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(ValueError, match="top level"):
            merge_bloodhound_json("42", g)

    def test_non_array_data_field_raises_value_error(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(ValueError, match="'data'/'items' must be an array"):
            merge_bloodhound_json({"meta": {"type": "users"}, "data": "oops"}, g)

    def test_non_dict_items_in_data_are_skipped(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [
                "not-a-dict",
                None,
                42,
                {"ObjectIdentifier": "S-OK", "Properties": {"name": "ok"}},
            ],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 1

    # -- Edge ingestion --

    def test_aces_and_memberships_are_ingested(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [
                {
                    "ObjectIdentifier": "S-FULL-1",
                    "Properties": {"name": "target"},
                    "Aces": [{"RightName": "GenericAll", "PrincipalSID": "S-ATK"}],
                    "MemberOf": [{"ObjectIdentifier": "S-GRP-DA"}],
                }
            ],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.edges >= 2  # at least ACE + membership

    def test_incremental_merge_adds_to_existing_graph(self) -> None:
        g = KnowledgeGraph()
        bh1 = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-INC-1", "Properties": {"name": "u1"}}],
        }
        bh2 = {
            "meta": {"type": "computers"},
            "data": [{"ObjectIdentifier": "S-INC-2", "Properties": {"name": "c1"}}],
        }
        merge_bloodhound_json(bh1, g)
        merge_bloodhound_json(bh2, g)
        assert g.stats()["nodes"] == 2

    def test_missing_meta_falls_back_to_users(self) -> None:
        # meta is absent — should not raise, defaults to Users type
        bh = {"data": [{"ObjectIdentifier": "S-NOMETA", "Properties": {"name": "nometa_user"}}]}
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 1

    def test_meta_not_a_dict_is_tolerated(self) -> None:
        # BH CE can emit meta as a string or null in rare edge cases
        bh = {
            "meta": "v2",
            "data": [{"ObjectIdentifier": "S-METASTR", "Properties": {"name": "msu"}}],
        }
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 1

    def test_empty_data_array_returns_zero_nodes(self) -> None:
        bh = {"meta": {"type": "users"}, "data": []}
        g = KnowledgeGraph()
        stats = merge_bloodhound_json(bh, g)
        assert stats.users == 0
        assert g.stats()["nodes"] == 0

    def test_object_identifier_takes_precedence_over_properties_objectid(self) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [
                {
                    "ObjectIdentifier": "TOP-SID",
                    "Properties": {"name": "x", "objectid": "INNER-SID"},
                }
            ],
        }
        g = KnowledgeGraph()
        merge_bloodhound_json(bh, g)
        idx = _build_bh_index(g)
        # ObjectIdentifier wins
        assert "TOP-SID" in idx

    def test_principal_sid_lookup_reuses_existing_node(self) -> None:
        # Insert a group first, then reference it from an ACE
        g = KnowledgeGraph()
        bh_groups = {
            "meta": {"type": "groups"},
            "data": [{"ObjectIdentifier": "S-KNOWN-GRP", "Properties": {"name": "grp"}}],
        }
        merge_bloodhound_json(bh_groups, g)
        initial_nodes = g.stats()["nodes"]

        bh_users = {
            "meta": {"type": "users"},
            "data": [
                {
                    "ObjectIdentifier": "S-USER-1",
                    "Properties": {"name": "user1"},
                    "Aces": [{"RightName": "GenericAll", "PrincipalSID": "S-KNOWN-GRP"}],
                }
            ],
        }
        merge_bloodhound_json(bh_users, g)
        # S-KNOWN-GRP should NOT create a duplicate node
        assert g.stats()["nodes"] == initial_nodes + 1  # only user1 added


# ── ingest_bloodhound_zip ────────────────────────────────────────────────────


class TestIngestBloodhoundZip:
    def _make_zip(self, tmp_path: Path, files: dict[str, dict | str | bytes]) -> Path:
        """Create a zip at tmp_path/bh.zip containing the given name→content map."""
        zp = tmp_path / "bh.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            for name, content in files.items():
                if isinstance(content, bytes):
                    zf.writestr(name, content)
                elif isinstance(content, str):
                    zf.writestr(name, content.encode("utf-8"))
                else:
                    zf.writestr(name, json.dumps(content).encode("utf-8"))
        return zp

    def test_single_users_json_is_ingested(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-Z1", "Properties": {"name": "zu1"}}],
        }
        zp = self._make_zip(tmp_path, {"users.json": bh})
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.users == 1

    def test_multiple_json_files_merged(self, tmp_path: Path) -> None:
        bh_users = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-Z2", "Properties": {"name": "zu2"}}],
        }
        bh_computers = {
            "meta": {"type": "computers"},
            "data": [{"ObjectIdentifier": "S-Z3", "Properties": {"name": "zc1"}}],
        }
        zp = self._make_zip(
            tmp_path, {"20240101users.json": bh_users, "20240101computers.json": bh_computers}
        )
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.users == 1
        assert stats.computers == 1

    def test_non_json_files_are_skipped(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-Z4", "Properties": {"name": "zu4"}}],
        }
        zp = self._make_zip(
            tmp_path, {"users.json": bh, "README.txt": b"ignore me", "data.csv": b"a,b,c"}
        )
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.users == 1

    def test_invalid_json_inside_zip_is_skipped(self, tmp_path: Path) -> None:
        zp = self._make_zip(tmp_path, {"bad.json": b"{not json"})
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        # Should not raise; corrupt entry is silently skipped
        assert stats.users == 0

    def test_empty_zip_returns_zero_stats(self, tmp_path: Path) -> None:
        zp = tmp_path / "empty.zip"
        with zipfile.ZipFile(zp, "w"):
            pass
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.users == 0
        assert stats.edges == 0

    def test_type_hint_inferred_from_filename(self, tmp_path: Path) -> None:
        # File named "BloodHound_20240101_computers.json" should infer type=Computers
        bh = {"data": [{"ObjectIdentifier": "S-FN-1", "Properties": {"name": "fn_computer"}}]}
        zp = self._make_zip(tmp_path, {"BloodHound_20240101_computers.json": bh})
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.computers == 1

    def test_type_hint_inferred_from_groups_filename(self, tmp_path: Path) -> None:
        bh = {"data": [{"ObjectIdentifier": "S-GFN-1", "Properties": {"name": "gfn_group"}}]}
        zp = self._make_zip(tmp_path, {"groups.json": bh})
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.groups == 1

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-PATH-1", "Properties": {"name": "pathuser"}}],
        }
        zp = self._make_zip(tmp_path, {"users.json": bh})
        g = KnowledgeGraph()
        # Pass as Path, not str
        stats = ingest_bloodhound_zip(zp, g)
        assert stats.users == 1

    def test_totals_are_summed_across_files(self, tmp_path: Path) -> None:
        bh_u1 = {
            "meta": {"type": "users"},
            "data": [
                {"ObjectIdentifier": "S-TOT-1", "Properties": {"name": "t1"}},
                {"ObjectIdentifier": "S-TOT-2", "Properties": {"name": "t2"}},
            ],
        }
        bh_u2 = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-TOT-3", "Properties": {"name": "t3"}}],
        }
        # Two user files in zip; total users should be 3
        zp = self._make_zip(tmp_path, {"users_dc1.json": bh_u1, "users_dc2.json": bh_u2})
        g = KnowledgeGraph()
        stats = ingest_bloodhound_zip(str(zp), g)
        assert stats.users == 3


# ── tools.py: bh_ingest_zip and bh_ingest_json (JSON output + error paths) ──


class TestBhIngestZipTool:
    """Test the @tool wrapper bh_ingest_zip: JSON output shape and error paths."""

    def _invoke(self, path: str) -> dict:
        from decepticon.tools.ad.tools import bh_ingest_zip

        result = bh_ingest_zip.invoke({"path": path})
        return json.loads(result)

    def test_success_returns_import_and_stats_keys(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-TOOL-1", "Properties": {"name": "tu1"}}],
        }
        zp = tmp_path / "bh.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("users.json", json.dumps(bh))

        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(zp))

        assert "import" in result
        assert "stats" in result
        assert result["import"]["users"] == 1

    def test_missing_zip_returns_error_key(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "no_such.zip")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(missing)

        assert "error" in result

    def test_bad_zip_file_returns_error_key(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.zip"
        bad.write_bytes(b"not a zip file")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(bad))

        assert "error" in result

    def test_output_is_valid_json_string(self, tmp_path: Path) -> None:
        bh = {"meta": {"type": "users"}, "data": []}
        zp = tmp_path / "empty_users.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("users.json", json.dumps(bh))

        mock_graph = KnowledgeGraph()
        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            from decepticon.tools.ad.tools import bh_ingest_zip

            raw = bh_ingest_zip.invoke({"path": str(zp)})

        # Must be valid JSON
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)


class TestBhIngestJsonTool:
    """Test the @tool wrapper bh_ingest_json: JSON output shape and error paths."""

    def _invoke(self, path: str, type_hint: str = "") -> dict:
        from decepticon.tools.ad.tools import bh_ingest_json

        result = bh_ingest_json.invoke({"path": path, "type_hint": type_hint})
        return json.loads(result)

    def test_success_returns_import_and_stats_keys(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "users"},
            "data": [{"ObjectIdentifier": "S-JT-1", "Properties": {"name": "jtu1"}}],
        }
        f = tmp_path / "users.json"
        f.write_text(json.dumps(bh), encoding="utf-8")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(f))

        assert "import" in result
        assert "stats" in result
        assert result["import"]["users"] == 1

    def test_missing_file_returns_error(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "no.json")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(missing)

        assert "error" in result

    def test_invalid_json_file_returns_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not json}", encoding="utf-8")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(bad))

        assert "error" in result

    def test_type_hint_is_passed_through(self, tmp_path: Path) -> None:
        bh = {"data": [{"ObjectIdentifier": "S-JT-TH", "Properties": {"name": "th_computer"}}]}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(bh), encoding="utf-8")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(f), type_hint="Computers")

        assert result["import"]["computers"] == 1
        assert result["import"]["users"] == 0

    def test_empty_type_hint_uses_meta_type(self, tmp_path: Path) -> None:
        bh = {
            "meta": {"type": "groups"},
            "data": [{"ObjectIdentifier": "S-JT-GRP", "Properties": {"name": "grp"}}],
        }
        f = tmp_path / "groups.json"
        f.write_text(json.dumps(bh), encoding="utf-8")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            result = self._invoke(str(f), type_hint="")

        assert result["import"]["groups"] == 1

    def test_output_is_valid_json_string(self, tmp_path: Path) -> None:
        bh = {"meta": {"type": "domains"}, "data": []}
        f = tmp_path / "domains.json"
        f.write_text(json.dumps(bh), encoding="utf-8")
        mock_graph = KnowledgeGraph()

        with (
            patch(
                "decepticon.tools.ad.tools._load",
                return_value=(mock_graph, tmp_path / "kg.json"),
            ),
            patch("decepticon.tools.ad.tools._save"),
        ):
            from decepticon.tools.ad.tools import bh_ingest_json

            raw = bh_ingest_json.invoke({"path": str(f)})

        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
