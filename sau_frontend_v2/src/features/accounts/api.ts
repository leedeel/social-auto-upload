import { deleteJson, getJson, postJson } from "@/lib/api-client";
import { AccountSchema, type Account, z } from "@/shared/types";

const AccountListSchema = z.array(AccountSchema);

export function listAccounts(platform?: string): Promise<Account[]> {
  const query = platform ? `?platform=${encodeURIComponent(platform)}` : "";
  return getJson(`/accounts${query}`, AccountListSchema);
}

export function createAccount(input: { platform: Account["platform"]; user_name: string }): Promise<Account> {
  return postJson("/accounts", input, AccountSchema);
}

export function deleteAccount(id: number): Promise<void> {
  return deleteJson(`/accounts/${id}`);
}

export function checkAccount(id: number): Promise<Account> {
  return postJson(`/accounts/${id}/check`, undefined, AccountSchema);
}
