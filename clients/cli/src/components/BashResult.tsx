import React from "react";
import { Box, Text } from "ink";

interface BashResultProps {
  command: string;
  output: string;
  status?: "success" | "error";
}

const CWD_PATTERN = /\n?\[cwd: (.+?)\]\s*$/;
const MAX_OUTPUT_LINES = 50;

export const BashResult = React.memo(function BashResult({
  command,
  output,
  status,
}: BashResultProps) {
  // Extract [cwd: /path] metadata
  const cwdMatch = output.match(CWD_PATTERN);
  const cwd = cwdMatch?.[1] ?? "/workspace";
  const cleanOutput = cwdMatch
    ? output.slice(0, cwdMatch.index).trim()
    : output.trim();

  // Skip echo of command in first line
  const allLines = cleanOutput.split("\n");
  const outputLines =
    allLines[0]?.trim() === command.trim() ? allLines.slice(1) : allLines;

  // Detect error/info output
  const isError =
    status === "error" ||
    cleanOutput.startsWith("[ERROR]") ||
    cleanOutput.startsWith("[TIMEOUT]");
  const isInfo =
    cleanOutput.startsWith("[IDLE]") ||
    cleanOutput.startsWith("[RUNNING]") ||
    cleanOutput.startsWith("[BACKGROUND]");

  // Truncate very long output (60% head + 40% tail)
  const truncated = outputLines.length > MAX_OUTPUT_LINES;
  const headCount = Math.floor(MAX_OUTPUT_LINES * 0.6);
  const tailCount = MAX_OUTPUT_LINES - headCount;
  const displayLines = truncated
    ? [
        ...outputLines.slice(0, headCount),
        `... (${outputLines.length - MAX_OUTPUT_LINES} lines omitted)`,
        ...outputLines.slice(-tailCount),
      ]
    : outputLines;

  return (
    <Box flexDirection="column">
      <Text>
        <Text color="green" bold>{"┌──("}</Text>
        <Text color="red" bold>{"root㉿sandbox"}</Text>
        <Text color="green" bold>{")-["}</Text>
        <Text color="blue" bold>{cwd}</Text>
        <Text color="green" bold>{"]"}</Text>
      </Text>

      <Text>
        <Text color="green" bold>{"└─# "}</Text>
        <Text bold>{command}</Text>
      </Text>

      {displayLines
        .filter((l) => l !== "" || displayLines.length <= 3)
        .map((line, i) => (
          <Text
            key={i}
            color={isError ? "red" : isInfo ? "cyan" : undefined}
            dimColor={!isError && !isInfo}
          >
            {line}
          </Text>
        ))}
    </Box>
  );
});
