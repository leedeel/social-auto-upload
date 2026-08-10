/**
 * Shared domain types for the v2 front-end.
 *
 * These mirror the Pydantic schemas in `sau_backend_v2/models/schemas.py`
 * and the `*UploadRequest` dataclasses in `sau_cli.py`. We express them as
 * Zod schemas so the API client can validate responses at runtime — a
 * back-end field rename will fail parsing here instead of silently
 * corrupting the UI.
 *
 * Bump `CONTRACT_VERSION` in `constants.ts` whenever a field is added,
 * renamed, or removed. The back-end and front-end both read the version
 * on startup; mismatched versions should refuse to boot.
 */
import { z } from "zod";

export { z };

export const PLATFORMS = ["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent", "youtube"] as const;
export type Platform = (typeof PLATFORMS)[number];

export const PlatformSchema = z.enum(PLATFORMS);

export const PUBLISH_KINDS = ["video", "note"] as const;
export type PublishKind = (typeof PUBLISH_KINDS)[number];

// --- Auth ----------------------------------------------------------------

export const LoginRequestSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});
export type LoginRequest = z.infer<typeof LoginRequestSchema>;

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
});
export type TokenResponse = z.infer<typeof TokenResponseSchema>;

// --- Accounts ------------------------------------------------------------

export const AccountSchema = z.object({
  id: z.number(),
  platform: PlatformSchema,
  type: z.number(),
  file_path: z.string(),
  user_name: z.string(),
  status: z.number(),
});
export type Account = z.infer<typeof AccountSchema>;

export const AccountCreateSchema = z.object({
  platform: PlatformSchema,
  user_name: z.string().min(1),
});
export type AccountCreate = z.infer<typeof AccountCreateSchema>;

// --- Materials -----------------------------------------------------------

export const MaterialSchema = z.object({
  id: z.number(),
  filename: z.string(),
  file_path: z.string(),
  filesize: z.number(),
  upload_time: z.string().nullable().optional(),
});
export type Material = z.infer<typeof MaterialSchema>;

// --- Publish -------------------------------------------------------------

const BasePublish = z.object({
  account_name: z.string().min(1),
  tags: z.array(z.string()).default([]),
  publish_date: z.union([z.string(), z.number()]).default(0),
  publish_strategy: z.string().default("immediate"),
});

export const DouyinVideoPublishSchema = BasePublish.extend({
  platform: z.literal("douyin"),
  kind: z.literal("video"),
  title: z.string().min(1),
  description: z.string().default(""),
  video_file: z.string().min(1),
  thumbnail_file: z.string().nullable().optional(),
  thumbnail_landscape_file: z.string().nullable().optional(),
  thumbnail_portrait_file: z.string().nullable().optional(),
  product_link: z.string().default(""),
  product_title: z.string().default(""),
  declaration: z.string().nullable().optional(),
});

export const DouyinNotePublishSchema = BasePublish.extend({
  platform: z.literal("douyin"),
  kind: z.literal("note"),
  title: z.string().min(1),
  note: z.string(),
  image_files: z.array(z.string()).min(1),
  bgm: z.string().default(""),
});

// More platform publish schemas (kuaishou/xiaohongshu/bilibili/tencent/youtube)
// follow the same pattern. See `sau_backend_v2/models/schemas.py` for the
// authoritative list.
//
// We use `z.union` rather than `z.discriminatedUnion` because the same
// platform can have both a video variant and a note variant
// (DouyinVideo + DouyinNote both carry `platform: "douyin"`), which a
// discriminated union rejects at schema construction. The back-end uses
// the (platform, kind) pair to route; the front-end does the same.

export const PublishRequestSchema = z.union([
  DouyinVideoPublishSchema,
  DouyinNotePublishSchema,
]);
export type PublishRequest = z.infer<typeof PublishRequestSchema>;

// --- Tasks ---------------------------------------------------------------

export const TaskSchema = z.object({
  id: z.string(),
  type: z.string(),
  platform: PlatformSchema,
  account_name: z.string(),
  title: z.string().nullable().optional(),
  status: z.string(),
  progress: z.number().int().min(0).max(100),
  current_step: z.string().nullable().optional(),
  error: z.string().nullable().optional(),
  request_payload: z.record(z.unknown()).nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Task = z.infer<typeof TaskSchema>;

// --- SSE event -----------------------------------------------------------

export const TaskEventSchema = z.object({
  event: z.string(),
  ts: z.string().optional(),
  percent: z.number().int().min(0).max(100).optional(),
  current_step: z.string().optional(),
  status: z.string().optional(),
  error: z.string().optional(),
});
export type TaskEvent = z.infer<typeof TaskEventSchema>;
