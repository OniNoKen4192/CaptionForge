interface Props {
  url: string | null;
}

export function ImagePreview({ url }: Props) {
  if (!url) return <div className="image-preview empty">No image</div>;
  return (
    <div className="image-preview">
      <img src={url} alt="" style={{ maxWidth: "100%", maxHeight: "80vh" }} />
    </div>
  );
}
