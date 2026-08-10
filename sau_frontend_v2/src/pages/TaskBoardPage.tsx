import { useSearchParams } from "react-router-dom";

import { useTask, useTasks } from "@/features/tasks/hooks";
import { TaskEventStream } from "@/features/tasks/TaskEventStream";
import { cn } from "@/lib/cn";

const STATUS_COLOR: Record<string, string> = {
  queued: "bg-ink-subtle/20 text-ink-muted",
  running: "bg-blue-100 text-blue-700",
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function TaskBoardPage() {
  const [searchParams] = useSearchParams();
  const focusId = searchParams.get("id");

  const tasks = useTasks();
  const focused = useTask(focusId);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ink">任务看板</h1>

      {focusId && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-ink-muted">任务 ID</p>
              <p className="font-mono text-sm text-ink">{focusId}</p>
            </div>
            {focused.data && (
              <div>
                <p className="text-sm text-ink-muted">进度</p>
                <p className="text-2xl font-semibold text-ink">{focused.data.progress}%</p>
              </div>
            )}
          </div>
          {focused.data && (
            <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
              <div
                className="h-full bg-brand-600 transition-all"
                style={{ width: `${focused.data.progress}%` }}
              />
            </div>
          )}
          <TaskEventStream taskId={focusId} />
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-ink-subtle/20">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface-muted text-xs uppercase tracking-wider text-ink-muted">
            <tr>
              <th className="px-4 py-2.5">任务</th>
              <th className="px-4 py-2.5">平台 / 账号</th>
              <th className="px-4 py-2.5">状态</th>
              <th className="px-4 py-2.5">进度</th>
              <th className="px-4 py-2.5">创建时间</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-subtle/20">
            {tasks.data?.map((task) => (
              <tr key={task.id} className="hover:bg-surface-subtle">
                <td className="px-4 py-2.5">
                  <p className="font-medium text-ink">{task.title || "—"}</p>
                  <p className="font-mono text-xs text-ink-subtle">{task.id.slice(0, 8)}...</p>
                </td>
                <td className="px-4 py-2.5 text-ink-muted">
                  {task.platform} · {task.account_name}
                </td>
                <td className="px-4 py-2.5">
                  <span
                    className={cn(
                      "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                      STATUS_COLOR[task.status] ?? STATUS_COLOR.queued,
                    )}
                  >
                    {task.status}
                  </span>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-muted">
                      <div
                        className="h-full bg-brand-600"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-ink-muted">{task.progress}%</span>
                  </div>
                </td>
                <td className="px-4 py-2.5 text-xs text-ink-subtle">
                  {new Date(task.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {tasks.data?.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-sm text-ink-muted">
                  暂无任务
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
