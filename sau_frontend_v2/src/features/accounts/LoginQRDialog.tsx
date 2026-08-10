import { useEffect, useRef, useState } from "react";

import { openEventSource } from "@/lib/api-client";
import { useAccountsUiStore } from "./store";

/**
 * SSE login dialog. Subscribes to `/api/accounts/{id}/login`, parses
 * `event: qrcode` payloads (with `image_data_url` / `image_path`) and
 * shows the latest QR alongside status text. Closes itself when the
 * server emits a `result` event with success.
 */
export function LoginQRDialog() {
  const accountId = useAccountsUiStore((s) => s.loginDialogAccountId);
  const close = useAccountsUiStore((s) => s.closeLoginDialog);

  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("等待扫码...");
  const [done, setDone] = useState<"success" | "failed" | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (accountId === null) return;
    setQrSrc(null);
    setStatus("正在打开登录页...");
    setDone(null);

    const source = openEventSource(`/accounts/${accountId}/login`);
    sourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Record<string, unknown>;
        const eventName = String(data.event ?? "event");
        if (eventName === "qrcode") {
          const dataUrl = typeof data.image_data_url === "string" ? data.image_data_url : null;
          if (dataUrl) {
            setQrSrc(dataUrl);
            setStatus("请用对应 App 扫描二维码");
          }
        } else if (eventName === "info") {
          setStatus(typeof data.message === "string" ? data.message : status);
        } else if (eventName === "result") {
          if (data.success === true) {
            setDone("success");
            setStatus("登录成功");
          } else {
            setDone("failed");
            setStatus(typeof data.message === "string" ? data.message : "登录失败");
          }
        } else if (eventName === "failed" || eventName === "error") {
          setDone("failed");
          setStatus(typeof data.message === "string" ? data.message : "登录失败");
        }
      } catch {
        // Malformed events are ignored; SSE comments (`: keepalive`) are not
        // delivered to onmessage so we don't need to handle them here.
      }
    };

    source.onerror = () => {
      setDone("failed");
      setStatus("连接中断,请重试");
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
    // We intentionally don't depend on `status` — it's only used inside the
    // handler as a fallback string and we don't want the effect to re-fire.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId]);

  if (accountId === null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-ink">扫码登录</h2>
        <p className="mt-1 text-sm text-ink-muted">{status}</p>

        <div className="mt-4 flex aspect-square w-full items-center justify-center rounded-md border border-ink-subtle/20 bg-surface-subtle">
          {qrSrc ? (
            <img src={qrSrc} alt="login QR" className="h-full w-full object-contain" />
          ) : (
            <span className="text-sm text-ink-subtle">等待二维码...</span>
          )}
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <button className="btn-ghost" onClick={close}>
            {done ? "关闭" : "取消"}
          </button>
        </div>
      </div>
    </div>
  );
}
