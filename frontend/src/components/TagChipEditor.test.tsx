import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, it, expect } from "vitest";
import { TagChipEditor } from "./TagChipEditor";

function Harness({ initial }: { initial: string[] }) {
  const [tags, setTags] = useState(initial);
  return <TagChipEditor tags={tags} onChange={setTags} />;
}

describe("TagChipEditor", () => {
  it("adds a tag via the input on Enter", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a"]} />);
    await user.type(screen.getByPlaceholderText("add tag"), "blue eyes{Enter}");
    expect(screen.getByText("blue eyes")).toBeInTheDocument();
  });

  it("removes a tag via its ✕ button", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b"]} />);
    await user.click(screen.getByRole("button", { name: "remove a" }));
    expect(screen.queryByText("a")).not.toBeInTheDocument();
    expect(screen.getByText("b")).toBeInTheDocument();
  });

  it("dedupes preserving first-seen order", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b", "a", "c", "b"]} />);
    await user.click(screen.getByRole("button", { name: "dedupe" }));
    const chips = screen.getAllByTestId("chip").map((c) =>
      c.textContent?.replace(/[✕↑↓]/g, "").trim()
    );
    expect(chips).toEqual(["a", "b", "c"]);
  });

  it("moves a tag up via its ↑ button", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b", "c"]} />);
    await user.click(screen.getByRole("button", { name: "move b up" }));
    const chips = screen.getAllByTestId("chip").map((c) =>
      c.textContent?.replace(/[✕↑↓]/g, "").trim()
    );
    expect(chips).toEqual(["b", "a", "c"]);
  });

  it("move up is a no-op at the top", async () => {
    const user = userEvent.setup();
    render(<Harness initial={["a", "b"]} />);
    await user.click(screen.getByRole("button", { name: "move a up" }));
    const chips = screen.getAllByTestId("chip").map((c) =>
      c.textContent?.replace(/[✕↑↓]/g, "").trim()
    );
    expect(chips).toEqual(["a", "b"]);
  });
});
