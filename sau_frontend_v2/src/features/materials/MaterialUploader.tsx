import { useState } from "react";

import { useUploadMaterial } from "./hooks";

/** Drop-zone + file picker. Shows per-file progress while uploading. */
export function MaterialUploader() {
  const upload = useUploadMaterial();
  const [progress, setProgress] = useState<number | null>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    for (const file of Array.from(files)) {
      setProgress(0);
      try {
        await upload.mutateAsync({ file, onProgress: setProgress });
      } finally {
        setProgress(null);
      }
    }
  };

  return (
    <div>
      <label
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-ink-subtle/40 bg-surface-subtle px-6 py-8 text-sm text-ink-muted hover:bg-surface-muted"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          void handleFiles(e.dataTransfer.files);
        }}
      >
        <span className="font-medium text-ink">拖拽文件到此处,或点击选择</span>
        <span className="mt-1 text-xs">支持 mp4 / mov / jpg / png / webp</span>
        <input
          type="file"
          className="hidden"
          multiple
          accept="video/*,image/*"
          onChange={(e) => void handleFiles(e.target.files)}
        />
      </label>
      {progress !== null && (
        <div className="mt-3">
          <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
            <div className="h-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-1 text-xs text-ink-muted">上传中... {progress}%</p>
        </div>
      )}
    </div>
  );
}
