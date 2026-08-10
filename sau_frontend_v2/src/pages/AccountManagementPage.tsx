import { AccountForm } from "@/features/accounts/AccountForm";
import { AccountTable } from "@/features/accounts/AccountTable";
import { LoginQRDialog } from "@/features/accounts/LoginQRDialog";
import { useAccounts } from "@/features/accounts/hooks";
import { useAccountsUiStore } from "@/features/accounts/store";
import { PLATFORMS, type Platform } from "@/shared/types";
import { cn } from "@/lib/cn";

const TABS: { value: Platform | "all"; label: string }[] = [
  { value: "all", label: "全部" },
  ...PLATFORMS.map((p) => ({ value: p, label: p })),
];

export function AccountManagementPage() {
  const selected = useAccountsUiStore((s) => s.selectedPlatform);
  const setSelected = useAccountsUiStore((s) => s.setSelectedPlatform);
  const accounts = useAccounts(selected === "all" ? undefined : selected);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink">账号管理</h1>
      </div>

      <div className="card">
        <AccountForm />
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setSelected(tab.value)}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              selected === tab.value
                ? "bg-brand-50 text-brand-700"
                : "text-ink-muted hover:bg-surface-muted",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {accounts.isLoading ? (
        <p className="text-sm text-ink-muted">加载中...</p>
      ) : accounts.isError ? (
        <p className="text-sm text-red-600">加载失败: {(accounts.error as Error).message}</p>
      ) : (
        <AccountTable accounts={accounts.data ?? []} />
      )}

      <LoginQRDialog />
    </div>
  );
}
