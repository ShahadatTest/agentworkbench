"""Write the demo data as the Markdown files people usually keep, as the baseline for the benchmark.

    python benchmark/build_fixture.py <target-dir> [extra-projects]

The files hold exactly the same information as the demo database (scripts/demo_seed.py).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import demo_seed as d  # noqa: E402
import dataset  # noqa: E402

LIVE = {"bakery-site", "dental-booking", "choir-tickets"}


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def main(target):
    root = Path(target)
    names = {p[0]: p for p in d.PROJECTS}
    lines = ["# Projects", ""]
    for slug, name, area, status, deploy, stack, summary in d.PROJECTS:
        live = ", live" if slug in LIVE else ""
        lines.append(f"- [{name}](projects/{slug}/NOTES.md): {area}, {status}{live}")
    (root).mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for slug, name, area, status, deploy, stack, summary in d.PROJECTS:
        folder = root / "projects" / slug
        (folder / "docs").mkdir(parents=True, exist_ok=True)
        notes = [f"# {name}", "", summary, "", f"Status: {status}", f"Runs on: {deploy or '-'}", f"Stack: {stack}", "",
                 "## Notes", ""]
        for s, text, author, pinned, days in d.NOTES:
            if s == slug:
                notes += [f"- ({d.ts(days)[:10]}, {author}{', pinned' if pinned else ''}) {text}", ""]
        notes += ["## Log", ""]
        for s, text, days in d.ACTIVITY:
            if s == slug:
                notes.append(f"- {d.ts(days)[:10]} {text}")
        (folder / "NOTES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")

        todo = [f"# TODO {name}", ""]
        for s, text, prio, kind, done in d.TODOS:
            if s == slug:
                todo.append(f"- [{'x' if done is not None else ' '}] (P{prio}){' idea:' if kind == 'idee' else ''} {text}")
        for s, text, prio in d.INBOX:
            if s == slug:
                todo.append(f"- [ ] (P{prio}) {text}")
        (folder / "TODO.md").write_text("\n".join(todo) + "\n", encoding="utf-8")

        for s, title, body in d.DOCS:
            if s == slug:
                (folder / "docs" / f"{slugify(title)}.md").write_text(body + "\n", encoding="utf-8")
        if not any((folder / "docs").iterdir()):
            (folder / "docs").rmdir()


if __name__ == "__main__":
    dataset.extend(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    main(sys.argv[1])
