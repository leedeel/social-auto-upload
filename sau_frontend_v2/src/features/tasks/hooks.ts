import { useQuery } from "@tanstack/react-query";

import { listTasks, getTask } from "./api";
import type { Task } from "@/shared/types";

export const TASKS_KEY = ["tasks"] as const;

export function useTasks(platform?: string) {
  return useQuery({
    queryKey: platform ? [...TASKS_KEY, platform] : TASKS_KEY,
    queryFn: () => listTasks(platform),
    refetchInterval: 5_000,
  });
}

export function useTask(id: string | null) {
  return useQuery({
    queryKey: ["task", id],
    queryFn: () => getTask(id!),
    enabled: id !== null,
    refetchInterval: 3_000,
  });
}
