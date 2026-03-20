import React from "react";
import { Box, Text } from "ink";
import { useSpinnerFrame } from "../hooks/useSpinnerFrame.js";
import type { StreamStats } from "../hooks/useAgent.js";

interface ActivityIndicatorProps {
  isStreaming: boolean;
  streamStats: StreamStats | null;
}

function formatElapsed(ms: number): string {
  const secs = Math.floor(ms / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return `${mins}m ${rem}s`;
}

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

// Shimmer gradient palette — blue → cyan → magenta → blue cycle
const SHIMMER_COLORS = [
  "#6366f1", // indigo
  "#818cf8",
  "#a78bfa", // violet
  "#c084fc",
  "#e879f9", // fuchsia
  "#f472b6", // pink
  "#e879f9",
  "#c084fc",
  "#a78bfa",
  "#818cf8",
];

/** Render text with a shifting gradient shimmer effect. */
function ShimmerText({ text, tick }: { text: string; tick: number }) {
  const chars = text.split("");
  // Slow down: shift every 2 ticks
  const offset = Math.floor(tick / 2);
  return (
    <Text>
      {chars.map((ch, i) => {
        const colorIdx =
          (i + offset) % SHIMMER_COLORS.length;
        return (
          <Text key={i} color={SHIMMER_COLORS[colorIdx]}>
            {ch}
          </Text>
        );
      })}
    </Text>
  );
}

/** Claude Code-style activity indicator with shimmer, elapsed time, and live token stats. */
export const ActivityIndicator = React.memo(function ActivityIndicator({
  isStreaming,
  streamStats,
}: ActivityIndicatorProps) {
  const { tick } = useSpinnerFrame(isStreaming);

  if (!isStreaming) return null;

  const elapsed = streamStats
    ? formatElapsed(Date.now() - streamStats.startTime)
    : "";
  const tokenCount = streamStats
    ? `\u2191 ${formatTokens(streamStats.totalTokens)} tokens`
    : "";

  const meta = [elapsed, tokenCount].filter(Boolean).join(" \u00B7 ");
  const metaStr = meta ? ` (${meta})` : "";

  return (
    <Box marginTop={1}>
      <Text>
        <Text color="cyan">{"\u2726 "}</Text>
        <ShimmerText text="Working..." tick={tick} />
        <Text dimColor>{metaStr}</Text>
      </Text>
    </Box>
  );
});
