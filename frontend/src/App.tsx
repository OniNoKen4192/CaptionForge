import { useCallback, useEffect, useState } from "react";
import type { Item } from "./types";
import { openDataset } from "./api";
import { DatasetOpen } from "./components/DatasetOpen";
import { ItemList } from "./components/ItemList";
import { ReviewPane } from "./components/ReviewPane";

export default function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function open(path: string) {
    setError(null);
    try {
      const { items } = await openDataset(path);
      setItems(items);
      setSelectedId(items.length ? items[0].id : null);
    } catch (e: any) {
      setError(String(e.detail ?? e));
    }
  }

  const step = useCallback((delta: number) => {
    setSelectedId((cur) => {
      const idx = items.findIndex((it) => it.id === cur);
      if (idx === -1) return cur;
      const next = Math.min(Math.max(idx + delta, 0), items.length - 1);
      return items[next].id;
    });
  }, [items]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "TEXTAREA" || tag === "INPUT";
      if (e.key === "ArrowLeft" && !typing) step(-1);
      if (e.key === "ArrowRight" && !typing) step(1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step]);

  function markSaved(id: string, mtime: number) {
    setItems((its) => its.map((it) => (it.id === id ? { ...it, has_caption: true, caption_mtime: mtime } : it)));
  }

  const selected = items.find((it) => it.id === selectedId) ?? null;

  return (
    <div className="app">
      <aside className="sidebar">
        <DatasetOpen onOpen={open} />
        {error && <div className="error" role="alert">{error}</div>}
        <ItemList items={items} selectedId={selectedId} onSelect={setSelectedId} />
      </aside>
      <main className="main-pane">
        {selected
          ? <ReviewPane key={selected.id} item={selected} onSaved={(m) => markSaved(selected.id, m)} />
          : <p>Open a dataset to begin.</p>}
      </main>
    </div>
  );
}
