import type { Item } from "../types";

interface Props {
  items: Item[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ItemList({ items, selectedId, onSelect }: Props) {
  return (
    <ul className="item-list">
      {items.map((it) => (
        <li key={it.id}>
          <button
            className="item-row"
            aria-current={it.id === selectedId ? "true" : undefined}
            onClick={() => onSelect(it.id)}
          >
            {it.has_caption ? "📝" : "◻"} {it.id}
          </button>
        </li>
      ))}
    </ul>
  );
}
