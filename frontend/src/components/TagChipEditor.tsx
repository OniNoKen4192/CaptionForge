import { useState } from "react";

interface Props {
  tags: string[];
  onChange: (tags: string[]) => void;
}

export function TagChipEditor({ tags, onChange }: Props) {
  const [draft, setDraft] = useState("");

  function addDraft() {
    const t = draft.trim();
    if (t) onChange([...tags, t]);
    setDraft("");
  }

  function removeAt(i: number) {
    onChange(tags.filter((_, idx) => idx !== i));
  }

  function moveAt(i: number, delta: number) {
    const j = i + delta;
    if (j < 0 || j >= tags.length) return;
    const next = [...tags];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }

  function dedupe() {
    const seen = new Set<string>();
    onChange(
      tags.filter((t) => {
        if (seen.has(t)) return false;
        seen.add(t);
        return true;
      })
    );
  }

  return (
    <div className="tag-chip-editor">
      <div className="chips">
        {tags.map((t, i) => (
          <span className="chip" data-testid="chip" key={`${t}-${i}`}>
            {t}
            <button aria-label={`move ${t} up`} onClick={() => moveAt(i, -1)}>↑</button>
            <button aria-label={`move ${t} down`} onClick={() => moveAt(i, 1)}>↓</button>
            <button aria-label={`remove ${t}`} onClick={() => removeAt(i)}>✕</button>
          </span>
        ))}
      </div>
      <div className="chip-controls">
        <input
          placeholder="add tag"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addDraft();
            }
          }}
        />
        <button onClick={dedupe}>dedupe</button>
      </div>
    </div>
  );
}
