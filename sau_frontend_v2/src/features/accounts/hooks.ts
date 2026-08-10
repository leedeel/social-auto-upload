import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { checkAccount, createAccount, deleteAccount, listAccounts } from "./api";
import type { Account } from "@/shared/types";

export const ACCOUNTS_KEY = ["accounts"] as const;

/** List accounts (optionally filtered by platform). */
export function useAccounts(platform?: string) {
  return useQuery({
    queryKey: platform ? [...ACCOUNTS_KEY, platform] : ACCOUNTS_KEY,
    queryFn: () => listAccounts(platform),
  });
}

/** Create a new account row (does not generate a cookie). */
export function useCreateAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAccount,
    onSuccess: (account) => {
      queryClient.setQueryData<Account[]>(ACCOUNTS_KEY, (previous) =>
        previous ? [account, ...previous] : [account],
      );
    },
  });
}

/** Delete an account and its cookie file. */
export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAccount,
    onSuccess: (_, id) => {
      queryClient.setQueryData<Account[]>(ACCOUNTS_KEY, (previous) =>
        previous?.filter((account) => account.id !== id) ?? [],
      );
    },
  });
}

/** Re-validate the account's cookie. */
export function useCheckAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: checkAccount,
    onSuccess: (account) => {
      queryClient.setQueryData<Account[]>(ACCOUNTS_KEY, (previous) =>
        previous?.map((existing) => (existing.id === account.id ? account : existing)) ?? [account],
      );
    },
  });
}
