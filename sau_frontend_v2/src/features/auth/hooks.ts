import { useMutation } from "@tanstack/react-query";

import { setToken } from "@/lib/api-client";
import { queryClient } from "@/lib/query-client";

import { login } from "./api";

/** Mutation that posts credentials and stores the token in localStorage. */
export function useLogin() {
  return useMutation({
    mutationFn: login,
    onSuccess: (response) => {
      setToken(response.access_token);
      // Invalidate any cached data so the next page fetch uses the new token.
      queryClient.invalidateQueries();
    },
  });
}
