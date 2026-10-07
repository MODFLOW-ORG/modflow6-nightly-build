# This script converts the release notes TOML files
# to markdown, which is added to the release page.
# Release notes are one TOML file per item in the
# items/ subdirectory of the release notes directory,
# with section and subsection names in schema.toml.
import argparse
import datetime
from pathlib import Path
from warnings import warn

DATE = datetime.date.today().strftime("%b %d, %Y")
TEMPLATE_PATH = Path(__file__).parent / "body.md.jinja"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notes_path", help="Release notes directory")
    parser.add_argument("md_path")
    args = parser.parse_args()
    notes_path = Path(args.notes_path).expanduser().absolute()
    schema_path = notes_path / "schema.toml"
    items_path = notes_path / "items"
    md_path = Path(args.md_path).expanduser().absolute()

    md_path.unlink(missing_ok=True)

    import tomli
    from jinja2 import Environment, FileSystemLoader

    sections = {}
    subsections = {}
    items = []
    if schema_path.is_file():
        with open(schema_path, "rb") as schema_file:
            schema = tomli.load(schema_file)
            sections = schema.get("sections", {})
            subsections = schema.get("subsections", {})
        for item_path in sorted(items_path.glob("*.toml")):
            with open(item_path, "rb") as item_file:
                item = tomli.load(item_file)
            if item.get("section") not in sections:
                warn(f"Skipping {item_path.name}, invalid section: {item.get('section')}")
                continue
            # make sure each item has a subsection entry even if empty
            if not item.get("subsection"):
                item["subsection"] = ""
            items.append(item)
    else:
        warn(f"Release notes schema file not found: {schema_path}")

    if not any(items):
        warn("No release notes found")

    # items without a subsection come first in their section, with no header
    subsections = {"": "", **subsections}

    loader = FileSystemLoader(Path(__file__).parent)
    env = Environment(
        loader=loader,
        trim_blocks=True,
        lstrip_blocks=True,
        line_statement_prefix="_",
        keep_trailing_newline=True,
    )
    template = env.get_template(TEMPLATE_PATH.name)
    md_path.write_text(
        template.render(
            sections=sections,
            subsections=subsections,
            items=items,
            date=DATE,
        )
    )
