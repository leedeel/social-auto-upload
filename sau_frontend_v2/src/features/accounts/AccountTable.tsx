import { useDeleteAccount, useCheckAccount } from "./hooks";
import { useAccountsUiStore } from "./store";
import { cn } from "@/lib/cn";
import type { Account } from "@/shared/types";

const STATUS_LABEL: Record<number, { text: string; color: string }> = {
  0: { text: "未登录", color: "bg-ink-subtle/20 text-ink-muted" },
  1: { text: "已登录", color: "bg-green-100 text-green-700" },
};

export function AccountTable({ accounts }: { accounts: Account[] }) {
  const openLoginDialog = useAccountsUiStore((s) => s.openLoginDialog);
  const remove = useDeleteAccount();
  const check = useCheckAccount();

  if (accounts.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-ink-subtle/30 bg-surface-subtle p-8 text-center text-sm text-ink-muted">
        还没有账号,先用上方表单添加一个。
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-ink-subtle/20">
      <table className="w-full text-left text-sm">
        <thead className="bg-surface-muted text-xs uppercase tracking-wider text-ink-muted">
          <tr>
            <th className="px-4 py-2.5">账号名</th>
            <th className="px-4 py-2.5">平台</th>
            <th className="px-4 py-2.5">状态</th>
            <th className="px-4 py-2.5">Cookie</th>
            <th className="px-4 py-2.5 text-right">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-subtle/20">
          {accounts.map((account) => {
            const status = STATUS_LABEL[account.status] ?? STATUS_LABEL[0];
            return (
              <tr key={account.id} className="hover:bg-surface-subtle">
                <td className="px-4 py-2.5 font-medium text-ink">{account.user_name}</td>
                <td className="px-4 py-2.5 text-ink-muted">{account.platform}</td>
                <td className="px-4 py-2.5">
                  <span
                    className={cn(
                      "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                      status.color,
                    )}
                  >
                    {status.text}
                  </span>
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink-subtle">
                  {account.file_path.split("/").pop()}
                </td>
                <td className="space-x-2 px-4 py-2.5 text-right">
                  <button
                    className="btn-ghost text-xs"
                    onClick={() => openLoginDialog(account.id)}
                  >
                    登录
                  </button>
                  <button
                    className="btn-ghost text-xs"
                    onClick={() => check.mutate(account.id)}
                    disabled={check.isPending}
                  >
                    校验
                  </button>
                  <button
                    className="btn-ghost text-xs text-red-600 hover:bg-red-50"
                    onClick={() => {
                      if (confirm(`确认删除账号「${account.user_name}」?`)) {
                        remove.mutate(account.id);
                      }
                    }}
                  >
                    删除
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
