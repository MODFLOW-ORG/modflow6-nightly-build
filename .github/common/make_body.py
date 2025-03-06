# This script converts the release notes TOML file
# to markdown, which is added to the release page.
import argparse
import datetime
import sys
from pathlib import Path
from warnings import warn

DATE = datetime.date.today().strftime("%b %d, %Y")
TEMPLATE_PATH = Path(__file__).parent / "body.md.jinja"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("toml_path")
    parser.add_argument("md_path")
    args = parser.parse_args()
    toml_path = Path(args.toml_path).expanduser().absolute()
    md_path = Path(args.md_path).expanduser().absolute()
    if not toml_path.is_file():
        warn(f"Release notes TOML file not found: {toml_path}")
        sys.exit(0)

    md_path.unlink(missing_ok=True)

    import tomli
    from jinja2 import Environment, FileSystemLoader

    loader = FileSystemLoader(Path(__file__).parent)
    env = Environment(
        loader=loader,
        trim_blocks=True,
        lstrip_blocks=True,
        line_statement_prefix="_",
        keep_trailing_newline=True,
    )
    template = env.get_template(TEMPLATE_PATH.name)
    with open(md_path, "w") as md_file:
        with open(toml_path, "rb") as toml_file:
            content = tomli.load(toml_file)
            sections = content.get("sections", [])
            subsections = content.get("subsections", [])
            items = content.get("items", [])
            # make sure each item has a subsection entry even if empty
            for item in items:
                if not item.get("subsection"):
                    item["subsection"] = ""
            if not any(items):
                warn("No release notes found, aborting")
                sys.exit(0)
            md_file.write(
                template.render(
                    sections=sections,
                    subsections=subsections,
                    items=items,
                    date=DATE,
                )
            )
