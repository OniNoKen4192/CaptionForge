import type { Section } from "../types";
import { TagChipEditor } from "./TagChipEditor";
import { NLSectionEditor } from "./NLSectionEditor";

interface Props {
  sections: Section[];
  onChange: (sections: Section[]) => void;
}

function toTags(text: string): string[] {
  return text.split(",").map((t) => t.trim()).filter(Boolean);
}

export function SectionManager({ sections, onChange }: Props) {
  function update(i: number, patch: Partial<Section>) {
    onChange(sections.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));
  }

  function toggleKind(i: number) {
    const s = sections[i];
    if (s.kind === "tags") {
      update(i, { kind: "natural_language", text: (s.tags ?? []).join(", "), tags: [] });
    } else {
      update(i, { kind: "tags", tags: toTags(s.text ?? ""), text: "" });
    }
  }

  function move(i: number, delta: number) {
    const j = i + delta;
    if (j < 0 || j >= sections.length) return;
    const next = [...sections];
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }

  function remove(i: number) {
    onChange(sections.filter((_, idx) => idx !== i));
  }

  function add() {
    onChange([...sections, { label: "New Section", kind: "natural_language", text: "" }]);
  }

  return (
    <div className="section-manager">
      {sections.map((s, i) => (
        <div className="section" key={i}>
          <div className="section-head">
            <input
              value={s.label ?? ""}
              placeholder="(no label)"
              onChange={(e) => update(i, { label: e.target.value || null })}
            />
            <button onClick={() => toggleKind(i)}>
              {s.kind === "tags" ? "tags → NL" : "NL → tags"}
            </button>
            <button aria-label="move up" onClick={() => move(i, -1)}>↑</button>
            <button aria-label="move down" onClick={() => move(i, 1)}>↓</button>
            <button aria-label="remove section" onClick={() => remove(i)}>🗑</button>
          </div>
          {s.kind === "tags" ? (
            <TagChipEditor tags={s.tags ?? []} onChange={(tags) => update(i, { tags })} />
          ) : (
            <NLSectionEditor text={s.text ?? ""} onChange={(text) => update(i, { text })} />
          )}
        </div>
      ))}
      <button className="add-section" onClick={add}>+ Add section</button>
    </div>
  );
}
