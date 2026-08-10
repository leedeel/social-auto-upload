import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";

import { queryClient } from "@/lib/query-client";
import { AppRouter } from "@/router";

import "@/styles/globals.css";

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("#root element not found in index.html");
}

ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppRouter />
    </QueryClientProvider>
  </React.StrictMode>,
);
