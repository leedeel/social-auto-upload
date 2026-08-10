import { z } from "zod";

import { apiClient, deleteJson, getJson } from "@/lib/api-client";
import { MaterialSchema, type Material } from "@/shared/types";

const MaterialListSchema = z.array(MaterialSchema);

export function listMaterials(): Promise<Material[]> {
  return getJson("/materials", MaterialListSchema);
}

export async function uploadMaterial(file: File, onProgress?: (percent: number) => void): Promise<Material> {
  const form = new FormData();
  form.append("file", file);
  const response = await apiClient.post("/materials", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return MaterialSchema.parse(response.data);
}

export function deleteMaterial(id: number): Promise<void> {
  return deleteJson(`/materials/${id}`);
}

export function previewUrl(id: number): string {
  return `/api/materials/${id}/preview`;
}
