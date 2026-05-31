export type Kind = "tags" | "natural_language";

export interface Section {
  label: string | null;
  kind: Kind;
  tags?: string[];
  text?: string;
}

export interface Item {
  id: string;
  image: string;
  has_caption: boolean;
  caption_mtime: number | null;
}

export interface ItemDetail {
  image_url: string;
  sections: Section[];
  caption_mtime: number | null;
}

export interface SaveResult {
  sections: Section[];
  caption_mtime: number;
}
