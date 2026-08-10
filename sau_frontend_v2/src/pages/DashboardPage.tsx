import { useQuery } from "@tanstack/react-query";

import { getJson } from "@/lib/api-client";
import { AccountSchema, MaterialSchema, TaskSchema, z } from "@/shared/types";
import { useAuthStore } from "@/features/auth/store";

/**
 * Dashboard with three counter cards. The numbers come straight from the
 * FastAPI backend (no client-side aggregation), so they reflect the
 * canonical SQLite state.
 */
export function DashboardPage() {
  const signOut = useAuthStore((s) => s.signOut);

  const accounts = useQuery({
    queryKey: ["accounts"],
    queryFn: () => getJson("/accounts", z.array(AccountSchema)),
  });
  const materials = useQuery({
    queryKey: ["materials"],
    queryFn: () => getJson("/materials", z.array(MaterialSchema)),
  });
  const tasks = useQuery({
    queryKey: ["tasks"],
    queryFn: () => getJson("/tasks", z.array(TaskSchema)),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink">总览</h1>
        <button onClick={signOut} className="btn-ghost">
          退出登录
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="账号"
          value={accounts.data?.length}
          loading={accounts.isLoading}
          error={!!accounts.error}
        />
        <StatCard
          title="素材"
          value={materials.data?.length}
          loading={materials.isLoading}
          error={!!materials.error}
        />
        <StatCard
          title="任务"
          value={tasks.data?.length}
          loading={tasks.isLoading}
          error={!!tasks.error}
        />
      </div>

      <div className="card">
        <h2 className="text-lg font-medium text-ink">快速入口</h2>
        <p className="mt-1 text-sm text-ink-muted">
          各业务页(账号管理 / 素材库 / 发布中心 / 任务看板)正在接入,本页面用于 sanity check 后端连通性。
        </p>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  loading,
  error,
}: {
  title: string;
  value: number | undefined;
  loading: boolean;
  error: boolean;
}) {
  return (
    <div className="card">
      <p className="text-sm text-ink-muted">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-ink">
        {loading ? "..." : error ? "—" : value ?? 0}
      </p>
    </div>
  );
}
