import { useEffect } from "react";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";

import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AccountManagementPage } from "@/pages/AccountManagementPage";
import { MaterialLibraryPage } from "@/pages/MaterialLibraryPage";
import { PublishCenterPage } from "@/pages/PublishCenterPage";
import { TaskBoardPage } from "@/pages/TaskBoardPage";
import { useAuthStore } from "@/features/auth/store";
import { AppShell } from "./AppShell";
import { ProtectedRoute } from "./ProtectedRoute";

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "accounts", element: <AccountManagementPage /> },
      { path: "materials", element: <MaterialLibraryPage /> },
      { path: "publish", element: <PublishCenterPage /> },
      { path: "tasks", element: <TaskBoardPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);

export function AppRouter() {
  // Hydrate the auth store from localStorage on first mount so a refresh
  // doesn't log the user out.
  const hydrate = useAuthStore((s) => s.hydrate);
  useEffect(() => {
    hydrate();
  }, [hydrate]);
  return <RouterProvider router={router} />;
}
