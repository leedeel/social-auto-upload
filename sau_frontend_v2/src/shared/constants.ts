/**
 * Cross-cutting constants for the v2 front-end. Bump `CONTRACT_VERSION`
 * whenever the API contract in `shared/types.ts` changes shape (add, remove,
 * or rename a field). The back-end reads the same version on startup.
 */
export const CONTRACT_VERSION = "0.1.0";

/** Bearer token used to authenticate against the FastAPI backend. */
export const API_TOKEN: string =
  (import.meta.env.VITE_API_TOKEN as string | undefined) ?? "sau-dev-token-change-me";

/** Default username/password (only used by the dev login form). */
export const DEFAULT_USERNAME = "admin";
export const DEFAULT_PASSWORD = "admin";

/** Vite proxy points `/api` to this URL. */
export const API_BASE_URL = "/api";

/** localStorage key for the bearer token. */
export const TOKEN_STORAGE_KEY = "sau_v2_token";
