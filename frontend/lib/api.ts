export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  init?: RequestInit & { accessToken?: string | null },
): Promise<T> {
  const { accessToken, ...rest } = init || {};
  const headers = new Headers(rest.headers);
  headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers, cache: "no-store" });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}
