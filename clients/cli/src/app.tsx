import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { Box, Text, Static, useApp, useInput } from "ink";
import { useAgent } from "./hooks/useAgent.js";
import { Banner } from "./components/Banner.js";
import { EventItem } from "./components/EventItem.js";
import { ActivityIndicator } from "./components/ActivityIndicator.js";
import { Prompt } from "./components/Prompt.js";
import type { AgentEvent } from "./types.js";

const HELP_TEXT = [
  "Commands:",
  "  /help   - Show this help",
  "  /clear  - Clear conversation",
  "  /quit   - Exit",
  "  /exit   - Exit",
].join("\n");

interface AppProps {
  initialMessage?: string;
}

export function App({ initialMessage }: AppProps) {
  const { exit } = useApp();
  const agent = useAgent();

  // Auto-submit initial message (e.g. demo mode)
  const autoStarted = useRef(false);
  useEffect(() => {
    if (!initialMessage || autoStarted.current) return;
    autoStarted.current = true;
    // Delay to ensure LangGraph server is fully ready
    const timer = setTimeout(() => agent.submit(initialMessage), 3000);
    return () => clearTimeout(timer);
  }, []);

  // Ctrl+C — cancel stream if running, otherwise exit
  useInput((_input, key) => {
    if (key.ctrl && _input === "c") {
      if (agent.isStreaming) {
        agent.cancel();
      } else {
        exit();
      }
    }
  });

  const handleSubmit = useCallback(
    (input: string) => {
      const trimmed = input.trim();
      if (!trimmed) return;

      if (trimmed === "/quit" || trimmed === "/exit") {
        exit();
        return;
      }

      if (trimmed === "/clear") {
        agent.clearEvents();
        return;
      }

      if (trimmed === "/help") {
        agent.addSystemEvent(HELP_TEXT);
        return;
      }

      agent.submit(trimmed);
    },
    [agent, exit],
  );

  // Prepend a sentinel banner item so it renders once at the top of <Static>
  const staticItems = useMemo(
    () =>
      [{ id: "__banner__" } as const, ...agent.events] as Array<
        { id: "__banner__" } | AgentEvent
      >,
    [agent.events],
  );

  return (
    <Box flexDirection="column">
      {/* Static region: banner (once) + completed events — permanent output */}
      <Static items={staticItems}>
        {(item) => (
          <Box key={item.id}>
            {item.id === "__banner__" ? (
              <Banner />
            ) : (
              <EventItem event={item as AgentEvent} />
            )}
          </Box>
        )}
      </Static>

      {/* Dynamic region: activity spinner + error + prompt */}
      <ActivityIndicator
        isStreaming={agent.isStreaming}
        streamStats={agent.streamStats}
      />

      {agent.error && (
        <Box>
          <Text color="red" bold>
            {"error> "}
          </Text>
          <Text color="red">{agent.error}</Text>
        </Box>
      )}

      <Prompt
        isDisabled={agent.isStreaming}
        onSubmit={handleSubmit}
        activeAgent={agent.activeAgent}
      />
    </Box>
  );
}
