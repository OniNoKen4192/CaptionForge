import type { Item } from "../types";

interface Props {
  items: Item[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ItemList({ items, selectedId, onSelect }: Props) {
  return (
    <ul className="item-list" style={{ listStyle: "none", margin: 0, padding: 0, overflowY: "auto" }}>
      {items.map((it) => (
        <li key={it.id}>
          <button
            onClick={() => onSelect(it.id)}
            style={{ fontWeight: it.id === selectedId ? "bold" : "normal", width: "100%", textAlign: "left" }}
          >
            {it.has_caption ? "📝" : "◻"} {it.id}
          </button>
        </li>
      ))}
    </ul>
  );
}
