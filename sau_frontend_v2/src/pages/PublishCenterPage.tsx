import { PublishForm } from "@/features/publish/PublishForm";

export function PublishCenterPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ink">发布中心</h1>
      <p className="text-sm text-ink-muted">
        填写一次发布任务,后端会异步执行并把进度推到任务看板。多账号 × 多平台的批量分发属于 M1 延伸范围,后续接入。
      </p>
      <div className="card max-w-2xl">
        <PublishForm />
      </div>
    </div>
  );
}
