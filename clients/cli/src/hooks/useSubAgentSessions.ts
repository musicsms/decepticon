import { useMemo } from "react";
import type { AgentEvent, SubAgentSession } from "../types.js";

/**
 * Derive structured sub-agent sessions from the flat event stream.
 *
 * Sessions are built by scanning for subagent_start/subagent_end events
 * and collecting all events with a matching `subagent` field between them.
 * This is a pure derivation (useMemo) — no separate state to synchronize.
 */
export function useSubAgentSessions(events: AgentEvent[]): SubAgentSession[] {
  return useMemo(() => {
    const sessions: SubAgentSession[] = [];
    // Map from agent name → currently open session (only one per agent at a time)
    const openSessions = new Map<string, SubAgentSession>();

    for (const event of events) {
      if (event.type === "subagent_start" && event.subagent) {
        const session: SubAgentSession = {
          id: event.id,
          agent: event.subagent,
          description: event.content || `Starting ${event.subagent}`,
          startEventId: event.id,
          eventIds: [event.id],
          toolCount: 0,
          startTime: event.timestamp,
          status: "running",
        };
        openSessions.set(event.subagent, session);
        sessions.push(session);
      } else if (event.type === "subagent_end" && event.subagent) {
        const session = openSessions.get(event.subagent);
        if (session) {
          session.endEventId = event.id;
          session.endTime = event.timestamp;
          session.status = event.status === "error" ? "error" : "completed";
          session.eventIds.push(event.id);
          openSessions.delete(event.subagent);
        }
      } else if (event.subagent) {
        // Tool results, bash results, AI messages from sub-agents
        const session = openSessions.get(event.subagent);
        if (session) {
          session.eventIds.push(event.id);
          if (event.type === "tool_result" || event.type === "bash_result") {
            session.toolCount++;
          }
        }
      }
    }

    return sessions;
  }, [events]);
}
