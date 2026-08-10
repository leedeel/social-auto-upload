import { z } from "zod";

import { getJson, openEventSource } from "@/lib/api-client";
import { TaskSchema, TaskEventSchema, type Task, type TaskEvent } from "@/shared/types";

const TaskListSchema = z.array(TaskSchema);

export function listTasks(platform?: string): Promise<Task[]> {
  const query = platform ? `?platform=${encodeURIComponent(platform)}` : "";
  return getJson(`/tasks${query}`, TaskListSchema);
}

export function getTask(id: string): Promise<Task> {
  return getJson(`/tasks/${id}`, TaskSchema);
}

export function openTaskEvents(id: string): EventSource {
  return openEventSource(`/tasks/${id}/events`);
}

export function parseTaskEvent(raw: string): TaskEvent | null {
  try {
    const data = JSON.parse(raw) as unknown;
    return TaskEventSchema.parse(data);
  } catch {
    return null;
  }
}
