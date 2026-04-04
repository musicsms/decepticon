import React from "react";
import { AppStateProvider } from "./state/AppState.js";
import { REPL } from "./screens/REPL.js";

interface AppProps {
  initialMessage?: string;
}

export function App({ initialMessage }: AppProps) {
  return (
    <AppStateProvider>
      <REPL initialMessage={initialMessage} />
    </AppStateProvider>
  );
}
