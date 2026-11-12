const DEFAULT_API_BASE_URL = "/api";

export function resolveApiBaseUrl(rawValue: string | undefined): string {
  const value = rawValue?.trim() || DEFAULT_API_BASE_URL;
  if (value.startsWith("/")) {
    if (value.startsWith("//") || value.includes("?") || value.includes("#")) {
      throw new Error("VITE_API_BASE_URL must be a simple root-relative path or HTTP(S) origin");
    }
    return value.length > 1 ? value.replace(/\/+$/, "") : value;
  }

  const parsed = new URL(value);
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("VITE_API_BASE_URL must be a simple root-relative path or HTTP(S) origin");
  }
  return value.replace(/\/+$/, "");
}

export const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
