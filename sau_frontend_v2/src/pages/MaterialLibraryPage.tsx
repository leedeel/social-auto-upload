import { MaterialUploader } from "@/features/materials/MaterialUploader";
import { MaterialList } from "@/features/materials/MaterialList";

export function MaterialLibraryPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ink">素材库</h1>
      <div className="card">
        <MaterialUploader />
      </div>
      <MaterialList />
    </div>
  );
}
