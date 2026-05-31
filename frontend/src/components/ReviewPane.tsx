import { useEffect, useState } from "react";
import type { Item, Section } from "../types";
import { getItem, parseRaw, saveRaw, saveSections } from "../api";
import { ImagePreview } from "./ImagePreview";
import { SectionManager } from "./SectionManager";
import { RawMode } from "./RawMode";

interface Props {
  item: Item;
  onSaved: (mtime: number) => void;
}

function sectionsToRaw(sections: Section[]): string {
  return sections
    .map((s) => {
      const head = s.label !== null ? `=== ${s.label} ===\n` : "";
      const body = s.kind === "tags" ? (s.tags ?? []).join(", ") : (s.text ?? "");
      return head + body;
    })
    .join("\n\n");
}

export function ReviewPane({ item, onSaved }: Props) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [baseMtime, setBaseMtime] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);
  const [raw, setRaw] = useState<string | null>(null); // non-null => raw mode
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    const detail = await getItem(item.id);
    setImageUrl(detail.image_url);
    setSections(detail.sections);
    setBaseMtime(detail.caption_mtime);
    setDirty(false);
    setRaw(null);
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [item.id]);

  function editSections(next: Section[]) {
    setSections(next);
    setDirty(true);
  }

  function enterRaw() {
    setRaw(sectionsToRaw(sections));
  }

  async function exitRaw() {
    if (raw === null) {
      return;
    }
    try {
      const parsed = await parseRaw(raw);
      setSections(parsed.sections);
      setDirty(true);
      setRaw(null);
    } catch (e: any) {
      setError(String(e.detail ?? e));
      // stay in raw mode so the user can fix the text or retry
    }
  }

  async function save() {
    setError(null);
    try {
      const result = raw !== null
        ? await saveRaw(item.id, raw, baseMtime)
        : await saveSections(item.id, sections, baseMtime);
      setSections(result.sections);
      setBaseMtime(result.caption_mtime);
      setDirty(false);
      setRaw(null);
      onSaved(result.caption_mtime);
    } catch (e: any) {
      if (e.status === 409) {
        setError("File changed on disk. Reload to get the latest (discards your edits)?");
      } else {
        setError(String(e.detail ?? e));
      }
    }
  }

  return (
    <div className="review-pane" style={{ display: "flex", gap: "1rem" }}>
      <div style={{ flex: 1 }}>
        <ImagePreview url={imageUrl} />
      </div>
      <div style={{ flex: 1 }}>
        <div className="toolbar">
          <button onClick={save} disabled={!dirty && raw === null}>Save{dirty ? " *" : ""}</button>
          {raw === null
            ? <button onClick={enterRaw}>Edit raw</button>
            : <button onClick={exitRaw}>Structured</button>}
        </div>
        {error && (
          <div className="error" role="alert">
            {error} <button onClick={load}>Reload</button>
          </div>
        )}
        {raw === null
          ? <SectionManager sections={sections} onChange={editSections} />
          : <RawMode raw={raw} onChange={(r) => { setRaw(r); setDirty(true); }} />}
      </div>
    </div>
  );
}
