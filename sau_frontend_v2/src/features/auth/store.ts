import { create } from "zustand";

import { getToken, setToken } from "@/lib/api-client";

/**
 * Auth state slice. Only owns UI state (logged-in flag, current username);
 * the actual token lives in localStorage and is attached by the axios
 * interceptor. Don't put server data here — that's TanStack Query's job.
 */
interface AuthState {
  token: string | null;
  username: string | null;
  hydrate: () => void;
  signIn: (token: string, username: string) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  username: null,
  hydrate: () => {
    const token = getToken();
    if (token !== null) {
      set({ token, username: null });
    }
  },
  signIn: (token, username) => {
    setToken(token);
    set({ token, username });
  },
  signOut: () => {
    setToken(null);
    set({ token: null, username: null });
  },
}));

export const selectIsAuthenticated = (s: AuthState) => s.token !== null;
