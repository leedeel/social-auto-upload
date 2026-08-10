import { LoginForm } from "@/features/auth/LoginForm";

export function LoginPage() {
  return (
    <div className="flex min-h-full items-center justify-center bg-surface-subtle p-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold text-ink">sau</h1>
          <p className="mt-1 text-sm text-ink-muted">视频上传 / 分发 / 自动评论</p>
        </div>
        <div className="card">
          <LoginForm />
        </div>
      </div>
    </div>
  );
}
