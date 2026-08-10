import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "./store";
import { useLogin } from "./hooks";
import { DEFAULT_PASSWORD, DEFAULT_USERNAME } from "@/shared/constants";

/**
 * Lightweight login form. The dev credentials are pre-filled to keep the
 * `pnpm dev` → `uvicorn sau_backend_v2.main:app` flow friction-free; ship
 * a real user store before any non-local deployment.
 */
export function LoginForm() {
  const [username, setUsername] = useState(DEFAULT_USERNAME);
  const [password, setPassword] = useState(DEFAULT_PASSWORD);
  const navigate = useNavigate();
  const signIn = useAuthStore((s) => s.signIn);
  const login = useLogin();

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate(
      { username, password },
      {
        onSuccess: (response) => {
          signIn(response.access_token, username);
          navigate("/", { replace: true });
        },
      },
    );
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-ink">用户名</label>
        <input
          className="input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-ink">密码</label>
        <input
          className="input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </div>
      {login.isError && (
        <p className="text-sm text-red-600">
          {(login.error as { message?: string })?.message ?? "登录失败"}
        </p>
      )}
      <button type="submit" className="btn-primary w-full" disabled={login.isPending}>
        {login.isPending ? "登录中..." : "登录"}
      </button>
    </form>
  );
}
