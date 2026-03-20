import React from "react";
import { Text } from "ink";

interface ToolCallLineProps {
  name: string;
  args: Record<string, unknown>;
}

/** Renders tool call in legacy CLI style: ● tool_name(key="value", ...) */
export const ToolCallLine = React.memo(function ToolCallLine({
  name,
  args,
}: ToolCallLineProps) {
  const argsStr = Object.entries(args)
    .filter(([, v]) => v != null && v !== "")
    .map(([k, v]) => {
      const val = typeof v === "string" ? `"${v}"` : String(v);
      return `${k}=${val}`;
    })
    .join(", ");

  return (
    <Text>
      <Text color="magenta" bold>
        {"● "}
      </Text>
      <Text color="magenta" bold>
        {name}
      </Text>
      <Text dimColor>{`(${argsStr})`}</Text>
    </Text>
  );
});
