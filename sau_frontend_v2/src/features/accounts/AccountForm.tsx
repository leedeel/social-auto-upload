import { useState } from "react";

import { useCreateAccount } from "./hooks";
import { PLATFORMS, type Platform } from "@/shared/types";

/** Small inline form: pick a platform, type an account name, submit. */
export function AccountForm() {
  const [platform, setPlatform] = useState<Platform>("douyin");
  const [userName, setUserName] = useState("");
  const create = useCreateAccount();

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!userName.trim()) return;
    create.mutate(
      { platform, user_name: userName.trim() },
      { onSuccess: () => setUserName("") },
    );
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-ink-muted">平台</label>
        <select
          className="input w-32"
          value={platform}
          onChange={(e) => setPlatform(e.target.value as Platform)}
        >
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1 min-w-[12rem]">
        <label className="mb-1 block text-xs font-medium text-ink-muted">账号名</label>
        <input
          className="input"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          placeholder="如 creator, demo, ..."
        />
      </div>
      <button type="submit" className="btn-primary" disabled={create.isPending}>
        {create.isPending ? "添加中..." : "添加账号"}
      </button>
      {create.isError && (
        <p className="basis-full text-sm text-red-600">{(create.error as Error).message}</p>
      )}
    </form>
  );
}
