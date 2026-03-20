import React from "react";
import { Box, Text } from "ink";
import type { AgentEvent } from "../types.js";
import { BashResult } from "./BashResult.js";
import { renderMarkdown } from "../utils/markdown.js";

interface EventItemProps {
  event: AgentEvent;
}

const MAX_RESULT_LINES = 20;

/** Extract skill name from a /skills/... path. Returns null if not a skill path. */
function extractSkillName(args: Record<string, unknown>): string | null {
  const filePath = args.file_path as string | undefined;
  if (!filePath || !filePath.includes("/skills/")) return null;
  const parts = filePath.split("/");
  const skillsIdx = parts.indexOf("skills");
  const skillDir = parts[parts.length - 2];
  if (skillDir && skillDir !== "skills" && skillsIdx >= 0) return skillDir;
  return parts[skillsIdx + 1] ?? null;
}

/** Format tool args as key=value string. */
function formatArgs(args: Record<string, unknown>): string {
  return Object.entries(args)
    .filter(([, v]) => v != null && v !== "")
    .map(([k, v]) => {
      const val = typeof v === "string" ? `"${v}"` : String(v);
      return `${k}=${val}`;
    })
    .join(", ");
}

/** Status dot: green for success, red for error. */
function StatusDot({ status }: { status?: "success" | "error" }) {
  const color = status === "error" ? "red" : "green";
  return <Text color={color}>{"● "}</Text>;
}

/** Truncate and format result lines for display. */
function truncateLines(content: string): string[] {
  const lines = content.split("\n");
  if (lines.length <= MAX_RESULT_LINES) return lines;
  return [
    ...lines.slice(0, MAX_RESULT_LINES),
    `... (${lines.length - MAX_RESULT_LINES} more lines)`,
  ];
}

/** Routes an AgentEvent to the appropriate visual renderer. */
export const EventItem = React.memo(function EventItem({
  event,
}: EventItemProps) {
  switch (event.type) {
    case "user":
      return (
        <Box marginTop={1} marginBottom={1}>
          <Text backgroundColor="#333333" color="white" bold>
            {` \u276F ${event.content} `}
          </Text>
        </Box>
      );

    case "bash_result":
      return (
        <Box marginTop={1}>
          <BashResult
            command={(event.toolArgs?.command as string) ?? ""}
            output={event.content}
            status={event.status}
          />
        </Box>
      );

    case "tool_result": {
      const skillName = extractSkillName(event.toolArgs ?? {});
      if (skillName) {
        return (
          <Box flexDirection="column" marginTop={1}>
            <Text>
              <StatusDot status={event.status} />
              <Text bold>{`Skill(${skillName})`}</Text>
            </Text>
            <Text dimColor>{"  \u23BF  Successfully loaded skill"}</Text>
          </Box>
        );
      }

      const toolName = event.toolName ?? "";
      const argsStr = formatArgs(event.toolArgs ?? {});
      const display = truncateLines(event.content);
      return (
        <Box flexDirection="column" marginTop={1}>
          <Text>
            <StatusDot status={event.status} />
            <Text bold>{`${toolName}(${argsStr})`}</Text>
          </Text>
          {display.map((line, i) => (
            <Text key={i} dimColor wrap="wrap">
              {"  \u23BF  "}{line}
            </Text>
          ))}
        </Box>
      );
    }

    case "ai_message":
      return (
        <Box flexDirection="column" marginTop={1}>
          <Text>
            <Text color="white">{"● "}</Text>
            <Text>{renderMarkdown(event.content)}</Text>
          </Text>
        </Box>
      );

    case "system":
      return (
        <Box marginTop={1}>
          <Text dimColor wrap="wrap">
            {event.content}
          </Text>
        </Box>
      );

    default:
      return null;
  }
});
