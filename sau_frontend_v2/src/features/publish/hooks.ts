import { useMutation } from "@tanstack/react-query";

import { submitPublish } from "./api";
import type { PublishRequest } from "@/shared/types";

export function useSubmitPublish() {
  return useMutation({
    mutationFn: (request: PublishRequest) => submitPublish(request),
  });
}
