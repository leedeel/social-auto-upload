import { z } from "zod";

import { postJson } from "@/lib/api-client";
import { LoginRequestSchema, TokenResponseSchema } from "@/shared/types";

export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type LoginResponse = z.infer<typeof TokenResponseSchema>;

/** POST /api/auth/login → returns the bearer token. */
export function login(payload: LoginRequest) {
  return postJson("/auth/login", LoginRequestSchema.parse(payload), TokenResponseSchema);
}
