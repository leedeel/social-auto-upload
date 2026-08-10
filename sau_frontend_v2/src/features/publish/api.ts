import { z } from "zod";

import { postJson } from "@/lib/api-client";
import { PublishRequestSchema, type PublishRequest } from "@/shared/types";

const PublishResponseSchema = z.object({
  task_id: z.string(),
  status: z.string(),
});

const BatchPublishResponseSchema = z.object({
  task_ids: z.array(z.string()),
  status: z.string(),
});

export function submitPublish(request: PublishRequest): Promise<{ task_id: string; status: string }> {
  return postJson("/publish", PublishRequestSchema.parse(request), PublishResponseSchema);
}

export function submitBatchPublish(requests: PublishRequest[]): Promise<{ task_ids: string[]; status: string }> {
  return postJson("/publish/batch", requests, BatchPublishResponseSchema);
}
