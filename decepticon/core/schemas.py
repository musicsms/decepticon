"""Red team engagement document schemas.

Defines the machine-readable document set for planning and executing
red team engagements. These map to the military-style planning hierarchy:

  RoE     → legal scope & boundaries       (guard rail, checked every iteration)
  CONOPS  → operational concept & threat    (strategic context)
  OPPLAN  → tactical objectives & status    (ralph loop task tracker)

The OPPLAN is the direct analogue of ralph's prd.json — it drives the
autonomous loop, with each objective checked off as it passes validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────────


class EngagementType(StrEnum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    HYBRID = "hybrid"
    ASSUMED_BREACH = "assumed-breach"
    PHYSICAL = "physical"


class ObjectivePhase(StrEnum):
    """Kill chain phases for objective ordering.

    Practical 5-phase model aligned with sub-agent routing:
      recon          → recon agent       (TA0043 Reconnaissance)
      initial-access → exploit agent     (TA0001 Initial Access + TA0002 Execution)
      post-exploit   → postexploit agent (TA0003-TA0009: Persistence thru Collection)
      c2             → postexploit agent (TA0011 Command and Control)
      exfiltration   → postexploit agent (TA0010 Exfiltration + Actions on Objectives)
    """

    RECON = "recon"
    INITIAL_ACCESS = "initial-access"
    POST_EXPLOIT = "post-exploit"
    C2 = "c2"
    EXFILTRATION = "exfiltration"


class OpsecLevel(StrEnum):
    """OPSEC posture for an objective.

    Determines C2 tier selection, tool choices, and detection avoidance rigor.
    Based on Red Team Maturity Model levels and C2 tier mapping.
    See docs/red-team/opplan-domain-knowledge.md for details.
    """

    LOUD = "loud"           # No evasion; testing detection capability
    STANDARD = "standard"   # Basic OPSEC; modify default signatures
    CAREFUL = "careful"     # Active evasion; avoid known signatures
    QUIET = "quiet"         # Minimal footprint; blend with normal traffic
    SILENT = "silent"       # Zero detection tolerance; abort if burned


class C2Tier(StrEnum):
    """C2 infrastructure tier for objective execution."""

    INTERACTIVE = "interactive"  # Direct operator control, seconds callback
    SHORT_HAUL = "short-haul"   # Reliable access, minutes-hours callback
    LONG_HAUL = "long-haul"     # Persistent fallback, hours-days callback


class ObjectiveStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


# ── RoE (Rules of Engagement) ────────────────────────────────────────


class ScopeEntry(BaseModel):
    """A single in-scope or out-of-scope target."""

    target: str = Field(description="Domain, IP range (CIDR), or asset identifier")
    type: str = Field(description="domain, ip-range, cloud-resource, physical, etc.")
    notes: str = ""


class EscalationContact(BaseModel):
    """Emergency or escalation contact."""

    name: str
    role: str
    channel: str = Field(description="Phone, email, Slack, etc.")
    available: str = Field(default="24/7", description="Availability window")


class RoE(BaseModel):
    """Rules of Engagement — legally binding scope and boundaries.

    Checked at the start of every ralph loop iteration as a guard rail.
    """

    engagement_name: str
    client: str
    start_date: str
    end_date: str
    engagement_type: EngagementType
    testing_window: str = Field(
        description="Authorized testing hours, e.g. 'Mon-Fri 09:00-18:00 KST'"
    )

    # Scope
    in_scope: list[ScopeEntry] = Field(default_factory=list)
    out_of_scope: list[ScopeEntry] = Field(default_factory=list)

    # Boundaries
    prohibited_actions: list[str] = Field(
        default_factory=lambda: [
            "Denial of Service (DoS/DDoS)",
            "Social engineering of employees (unless authorized)",
            "Physical access attempts (unless authorized)",
            "Data exfiltration of real customer data",
            "Modification or deletion of production data",
        ]
    )
    permitted_actions: list[str] = Field(default_factory=list)

    # Escalation
    escalation_contacts: list[EscalationContact] = Field(default_factory=list)
    incident_procedure: str = Field(
        default="Stop immediately, document the incident, notify engagement lead within 15 minutes."
    )

    # Legal
    authorization_reference: str = Field(
        default="", description="Reference to signed authorization letter or contract"
    )

    # Operational limits
    data_handling: str = Field(
        default="",
        description="How discovered PII, credentials, and client data must be handled",
    )
    cleanup_required: bool = Field(
        default=True,
        description="Whether red team must remove tools/artifacts after engagement",
    )

    # Metadata
    version: str = "1.0"
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


# ── CONOPS (Concept of Operations) ───────────────────────────────────


class ThreatActor(BaseModel):
    """Threat actor profile to emulate."""

    name: str = Field(description="Actor name or archetype, e.g. 'APT29', 'Opportunistic External'")
    sophistication: str = Field(description="low, medium, high, nation-state")
    motivation: str = Field(description="financial, espionage, disruption, hacktivism")
    initial_access: list[str] = Field(
        default_factory=list, description="Expected initial access techniques (MITRE IDs)"
    )
    ttps: list[str] = Field(
        default_factory=list, description="Key MITRE ATT&CK technique IDs this actor uses"
    )


class KillChainPhase(BaseModel):
    """A phase in the engagement kill chain."""

    phase: ObjectivePhase
    description: str
    success_criteria: str = ""
    tools: list[str] = Field(default_factory=list)


class CONOPS(BaseModel):
    """Concept of Operations — strategic engagement overview.

    Readable by both technical operators and non-technical stakeholders.
    """

    engagement_name: str
    executive_summary: str = Field(description="2-3 sentence overview a CEO could understand")

    # Threat model
    threat_actors: list[ThreatActor] = Field(default_factory=list)
    attack_narrative: str = Field(
        default="", description="Story-form description of the simulated attack scenario"
    )

    # Kill chain
    kill_chain: list[KillChainPhase] = Field(default_factory=list)

    # Operational
    methodology: str = Field(default="PTES + MITRE ATT&CK framework")
    communication_plan: str = Field(
        default="", description="How red cell communicates with client and internally"
    )

    # Timeline
    phases_timeline: dict[str, str] = Field(
        default_factory=dict, description="Phase name → date range mapping"
    )

    # Success criteria
    success_criteria: list[str] = Field(default_factory=list)


# ── Deconfliction Plan ───────────────────────────────────────────────


class DeconflictionEntry(BaseModel):
    """A deconfliction identifier for red team activity."""

    type: str = Field(description="source-ip, user-agent, tool-hash, time-window, etc.")
    value: str
    description: str = ""


class DeconflictionPlan(BaseModel):
    """Deconfliction plan — separating red team activity from real threats."""

    engagement_name: str
    identifiers: list[DeconflictionEntry] = Field(default_factory=list)
    notification_procedure: str = Field(
        default="Red team lead notifies SOC 30 minutes before active scanning begins."
    )
    soc_contact: str = ""
    deconfliction_code: str = Field(
        default="", description="Shared secret code for real-time deconfliction calls"
    )


# ── OPPLAN (Operations Plan) — the ralph loop driver ─────────────────


class Objective(BaseModel):
    """A single engagement objective — analogous to ralph's user story.

    Each objective must be completable in ONE agent context window.
    The ralph loop picks the highest-priority objective where status != 'passed'.
    """

    id: str = Field(description="Unique ID, e.g. OBJ-001")
    phase: ObjectivePhase
    title: str
    description: str
    acceptance_criteria: list[str] = Field(
        description="Verifiable criteria — each must be checkable"
    )
    priority: int = Field(
        description="Execution order (1 = first). Respects kill chain dependencies."
    )
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    """pending → in-progress → completed/blocked. blocked → in-progress (retry) or completed (abandon)."""
    mitre: list[str] = Field(
        default_factory=list,
        description="MITRE ATT&CK technique IDs (e.g. ['T1190', 'T1059.004'])",
    )

    # Red team-specific fields (not found in pentest planning)
    opsec: OpsecLevel = Field(
        default=OpsecLevel.STANDARD,
        description="OPSEC posture — drives tool selection and detection avoidance rigor",
    )
    opsec_notes: str = Field(
        default="", description="Specific OPSEC constraints for this objective"
    )
    c2_tier: C2Tier = Field(
        default=C2Tier.INTERACTIVE,
        description="C2 tier: interactive (seconds), short-haul (minutes), long-haul (hours)",
    )
    concessions: list[str] = Field(
        default_factory=list,
        description="Pre-authorized assists if objective is blocked (TIBER/CORIE concept)",
    )

    notes: str = ""
    blocked_by: list[str] = Field(
        default_factory=list, description="Objective IDs that must complete first"
    )
    owner: str = Field(
        default="", description="Sub-agent currently executing this objective"
    )


class OPPLAN(BaseModel):
    """Operations Plan — the tactical task tracker for the ralph loop.

    Direct analogue of ralph's prd.json. The autonomous loop reads this
    file each iteration, picks the next objective, executes it, and
    updates the status.
    """

    engagement_name: str
    threat_profile: str = Field(
        description="Short threat actor summary for context injection each iteration"
    )
    objectives: list[Objective] = Field(default_factory=list)


# ── Engagement Bundle ─────────────────────────────────────────────────


class EngagementBundle(BaseModel):
    """Complete engagement document set.

    The planning agent generates all four documents as a unit.
    The ralph loop reads roe + opplan each iteration.
    """

    roe: RoE
    conops: CONOPS
    opplan: OPPLAN
    deconfliction: DeconflictionPlan

    def save(self, engagement_dir: str) -> dict[str, str]:
        """Save all documents to an engagement workspace directory.

        Layout:
          <engagement_dir>/plan/roe.json, conops.json, opplan.json, deconfliction.json
          <engagement_dir>/findings.md
          <engagement_dir>/recon/  (created empty)
          <engagement_dir>/exploit/  (created empty)
          <engagement_dir>/post-exploit/  (created empty)

        Returns a mapping of document type → file path.
        """
        import json
        from pathlib import Path

        root = Path(engagement_dir)
        plan_dir = root / "plan"
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Create execution subdirectories
        for subdir in ("recon", "exploit", "post-exploit"):
            (root / subdir).mkdir(parents=True, exist_ok=True)

        files = {}
        for name, doc in [
            ("roe", self.roe),
            ("conops", self.conops),
            ("opplan", self.opplan),
            ("deconfliction", self.deconfliction),
        ]:
            path = plan_dir / f"{name}.json"
            path.write_text(
                json.dumps(doc.model_dump(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            files[name] = str(path)

        # Initialize empty findings.md
        findings_path = root / "findings.md"
        if not findings_path.exists():
            findings_path.write_text(
                f"# Findings Log — {self.roe.engagement_name}\n\n"
                f"Started: {datetime.now().isoformat()}\n\n"
                "---\n\n",
                encoding="utf-8",
            )
            files["findings"] = str(findings_path)

        return files
