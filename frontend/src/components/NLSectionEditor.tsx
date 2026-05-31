interface Props {
  text: string;
  onChange: (text: string) => void;
}

export function NLSectionEditor({ text, onChange }: Props) {
  return (
    <textarea
      className="nl-editor"
      style={{ width: "100%", minHeight: "8rem", whiteSpace: "pre-wrap" }}
      value={text}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
