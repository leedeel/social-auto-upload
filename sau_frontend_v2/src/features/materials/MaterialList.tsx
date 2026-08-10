import { useDeleteMaterial, useMaterials } from "./hooks";
import { previewUrl } from "./api";

function formatSize(mb: number): string {
  if (mb < 1) return `${Math.round(mb * 1024)} KB`;
  return `${mb.toFixed(1)} MB`;
}

export function MaterialList() {
  const { data, isLoading, isError, error } = useMaterials();
  const remove = useDeleteMaterial();

  if (isLoading) return <p className="text-sm text-ink-muted">加载中...</p>;
  if (isError) return <p className="text-sm text-red-600">加载失败: {(error as Error).message}</p>;
  if (!data || data.length === 0) {
    return <p className="text-sm text-ink-muted">素材库为空,先上传一个文件吧。</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((material) => {
        const isVideo = /\.(mp4|mov|avi|mkv|webm|flv|wmv|m4v)$/i.test(material.filename);
        return (
          <div key={material.id} className="card overflow-hidden p-0">
            <div className="aspect-video bg-ink/5">
              {isVideo ? (
                <video src={previewUrl(material.id)} controls className="h-full w-full object-contain" />
              ) : (
                <img src={previewUrl(material.id)} alt={material.filename} className="h-full w-full object-contain" />
              )}
            </div>
            <div className="p-4">
              <p className="truncate text-sm font-medium text-ink" title={material.filename}>
                {material.filename}
              </p>
              <p className="mt-1 text-xs text-ink-muted">{formatSize(material.filesize)}</p>
              <div className="mt-3 flex justify-end">
                <button
                  className="btn-ghost text-xs text-red-600 hover:bg-red-50"
                  onClick={() => {
                    if (confirm(`确认删除「${material.filename}」?`)) {
                      remove.mutate(material.id);
                    }
                  }}
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
