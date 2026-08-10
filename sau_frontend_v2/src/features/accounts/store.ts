import { create } from "zustand";

import type { Platform } from "@/shared/types";

/** UI state for the accounts page. Server data lives in TanStack Query. */
interface AccountsUiState {
  selectedPlatform: Platform | "all";
  loginDialogAccountId: number | null;
  setSelectedPlatform: (platform: Platform | "all") => void;
  openLoginDialog: (accountId: number) => void;
  closeLoginDialog: () => void;
}

export const useAccountsUiStore = create<AccountsUiState>((set) => ({
  selectedPlatform: "all",
  loginDialogAccountId: null,
  setSelectedPlatform: (platform) => set({ selectedPlatform: platform }),
  openLoginDialog: (accountId) => set({ loginDialogAccountId: accountId }),
  closeLoginDialog: () => set({ loginDialogAccountId: null }),
}));
