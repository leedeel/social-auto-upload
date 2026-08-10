import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteMaterial, listMaterials, uploadMaterial } from "./api";
import type { Material } from "@/shared/types";

export const MATERIALS_KEY = ["materials"] as const;

export function useMaterials() {
  return useQuery({ queryKey: MATERIALS_KEY, queryFn: listMaterials });
}

export function useUploadMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { file: File; onProgress?: (percent: number) => void }) =>
      uploadMaterial(input.file, input.onProgress),
    onSuccess: (material) => {
      queryClient.setQueryData<Material[]>(MATERIALS_KEY, (previous) =>
        previous ? [material, ...previous] : [material],
      );
    },
  });
}

export function useDeleteMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteMaterial,
    onSuccess: (_, id) => {
      queryClient.setQueryData<Material[]>(MATERIALS_KEY, (previous) =>
        previous?.filter((material) => material.id !== id) ?? [],
      );
    },
  });
}
