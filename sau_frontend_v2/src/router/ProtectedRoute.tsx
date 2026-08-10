import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore, selectIsAuthenticated } from "@/features/auth/store";

/**
 * Gate that redirects unauthenticated users to /login. Reads from the
 * auth store (which hydrates from localStorage on mount) so a hard refresh
 * doesn't bounce the user out.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthed = useAuthStore(selectIsAuthenticated);
  const location = useLocation();
  if (!isAuthed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}
