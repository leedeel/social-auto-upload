import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAccounts } from "@/features/accounts/hooks";
import { useMaterials } from "@/features/materials/hooks";
import { useSubmitPublish } from "./hooks";
import { PLATFORMS, type Platform } from "@/shared/types";

/**
 * Minimal publish form. Selects platform → account → material, fills
 * title/description/tags, and submits a single publish task. The back-end
 * response contains the task id; we navigate to the task board so the
 * user can watch progress.
 */
export function PublishForm() {
  const [platform, setPlatform] = useState<Platform>("douyin");
  const [accountId, setAccountId] = useState<number | null>(null);
  const [materialId, setMaterialId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");

  const accounts = useAccounts(platform);
  const materials = useMaterials();
  const submit = useSubmitPublish();
  const navigate = useNavigate();

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (accountId === null || materialId === null || !title.trim()) return;
    const account = accounts.data?.find((a) => a.id === accountId);
    const material = materials.data?.find((m) => m.id === materialId);
    if (!account || !material) return;
    submit.mutate(
      {
        // The discriminated union in `shared/types.ts` only models douyin so
        // far; back-end accepts any platform payload. Cast keeps the form
        // type-safe where it can be, and lets the back-end schema be the
        // authority for the rest.
        platform: platform as "douyin",
        kind: "video",
        account_name: account.user_name,
        title: title.trim(),
        description,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        video_file: material.file_path,
        publish_date: 0,
        publish_strategy: "immediate",
      } as Parameters<typeof submit.mutate>[0],
      {
        onSuccess: (response) => navigate(`/tasks?id=${response.task_id}`),
      },
    );
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-ink">平台</label>
          <select
            className="input"
            value={platform}
            onChange={(e) => {
              setPlatform(e.target.value as Platform);
              setAccountId(null);
            }}
          >
            {PLATFORMS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-ink">账号</label>
          <select
            className="input"
            value={accountId ?? ""}
            onChange={(e) => setAccountId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">选择一个账号</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.user_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-ink">素材</label>
        <select
          className="input"
          value={materialId ?? ""}
          onChange={(e) => setMaterialId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">选择一个素材</option>
          {materials.data?.map((m) => (
            <option key={m.id} value={m.id}>
              {m.filename}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-ink">标题</label>
        <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-ink">描述</label>
        <textarea
          className="input min-h-[6rem]"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-ink">标签</label>
        <input
          className="input"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="用逗号分隔,例如 美食,探店"
        />
      </div>

      {submit.isError && (
        <p className="text-sm text-red-600">发布失败: {(submit.error as Error).message}</p>
      )}

      <button
        type="submit"
        className="btn-primary"
        disabled={submit.isPending || accountId === null || materialId === null || !title.trim()}
      >
        {submit.isPending ? "提交中..." : "提交发布任务"}
      </button>
    </form>
  );
}
