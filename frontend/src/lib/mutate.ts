import { toast } from "sonner";

/**
 * Wraps an async mutation (create/update/delete) with:
 * - toast on success
 * - toast on error (parsed from ApiError)
 * - never silently swallows exceptions
 *
 * Usage:
 *   await mutate(() => apiPost("/v1/foo", data), "Créé avec succès");
 *   await mutate(() => apiDelete("/v1/foo/1"), "Supprimé");
 */
export async function mutate<T>(
  fn: () => Promise<T>,
  successMessage?: string,
): Promise<T | undefined> {
  try {
    const result = await fn();
    if (successMessage) {
      toast.success(successMessage);
    }
    return result;
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Une erreur est survenue";
    toast.error(message);
    return undefined;
  }
}
