interface Props {
  raw: string;
  onChange: (raw: string) => void;
}

export function RawMode({ raw, onChange }: Props) {
  return (
    <textarea
      className="raw-mode"
      style={{ width: "100%", minHeight: "24rem", fontFamily: "monospace", whiteSpace: "pre" }}
      value={raw}
      onChange={(e) => onChange(e.target.value)}
      spellCheck={false}
    />
  );
}
