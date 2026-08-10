import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/cn";

const NAV_ITEMS: { to: string; label: string; end?: boolean }[] = [
  { to: "/", label: "总览", end: true },
  { to: "/accounts", label: "账号管理" },
  { to: "/materials", label: "素材库" },
  { to: "/publish", label: "发布中心" },
  { to: "/tasks", label: "任务看板" },
];

export function AppShell() {
  return (
    <div className="flex min-h-full">
      <aside className="hidden w-56 shrink-0 border-r border-ink-subtle/20 bg-white sm:block">
        <div className="px-6 py-5">
          <p className="text-lg font-semibold text-ink">sau</p>
          <p className="text-xs text-ink-muted">上传 / 分发 / 评论</p>
        </div>
        <nav className="space-y-1 px-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-ink-muted hover:bg-surface-muted hover:text-ink",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
