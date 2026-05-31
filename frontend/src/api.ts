import type { Item, ItemDetail, Section, SaveResult } from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw { status: res.status, detail: (detail as any).detail ?? res.statusText };
  }
  return res.json() as Promise<T>;
}

export async function openDataset(path: string): Promise<{ root: string; items: Item[] }> {
  return json(await fetch("/api/dataset/open", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  }));
}

export async function getItem(id: string): Promise<ItemDetail> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`));
}

export async function parseRaw(raw: string): Promise<{ sections: Section[] }> {
  return json(await fetch("/api/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw }),
  }));
}

export async function saveSections(
  id: string, sections: Section[], baseMtime: number | null,
): Promise<SaveResult> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections, base_mtime: baseMtime }),
  }));
}

export async function saveRaw(
  id: string, raw: string, baseMtime: number | null,
): Promise<SaveResult> {
  return json(await fetch(`/api/item/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw, base_mtime: baseMtime }),
  }));
}
