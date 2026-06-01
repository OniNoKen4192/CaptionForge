import { useState } from "react";

interface Props {
  onOpen: (path: string) => void;
}

export function DatasetOpen({ onOpen }: Props) {
  const [path, setPath] = useState("");
  return (
    <form
      className="dataset-open"
      onSubmit={(e) => { e.preventDefault(); if (path.trim()) onOpen(path.trim()); }}
    >
      <input
        placeholder="dataset directory path"
        value={path}
        onChange={(e) => setPath(e.target.value)}
      />
      <button type="submit">Open</button>
    </form>
  );
}
