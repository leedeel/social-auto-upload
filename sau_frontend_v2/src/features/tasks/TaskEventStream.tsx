import { useEffect, useState } from "react";

import { openTaskEvents, parseTaskEvent } from "./api";
import type { TaskEvent } from "@/shared/types";

/**
 * Subscribe to `/api/tasks/{id}/events` and accumulate the latest event.
 * Cleans up on unmount or when the task id changes.
 */
export function TaskEventStream({ taskId }: { taskId: string }) {
  const [event, setEvent] = useState<TaskEvent | null>(null);
  const [log, setLog] = useState<TaskEvent[]>([]);

  useEffect(() => {
    const source = openTaskEvents(taskId);
    source.onmessage = (message) => {
      const parsed = parseTaskEvent(message.data);
      if (!parsed) return;
      setEvent(parsed);
      setLog((previous) => [...previous.slice(-49), parsed]);
    };
    return () => source.close();
  }, [taskId]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-ink">最新事件</span>
        <code className="rounded bg-surface-muted px-2 py-0.5 text-xs">
          {event?.event ?? "等待中..."}
        </code>
        <span className="text-sm text-ink-muted">{event?.current_step}</span>
      </div>
      <div className="max-h-48 overflow-y-auto rounded-md border border-ink-subtle/20 bg-surface-subtle p-2 font-mono text-xs">
        {log.length === 0 ? (
          <p className="text-ink-subtle">暂无事件</p>
        ) : (
          log.map((entry, index) => (
            <div key={index} className="text-ink-muted">
              [{entry.ts ?? ""}] {entry.event}
              {entry.percent !== undefined ? ` (${entry.percent}%)` : ""}
              {entry.error ? ` — ${entry.error}` : ""}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
