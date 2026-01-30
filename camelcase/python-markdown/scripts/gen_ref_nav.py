"""Generate the code reference pages and navigation."""

import textwrap
import yaml
from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

perModuleOptions = {
    "markdown": {"summary": {"attributes": True, "functions": True, "classes": True}}
}

basePath = Path(__file__).resolve().parent.parent

modules = [
    basePath.joinpath("markdown", "__init__.py"),
    basePath.joinpath("markdown", "preprocessors.py"),
    basePath.joinpath("markdown", "blockparser.py"),
    basePath.joinpath("markdown", "blockprocessors.py"),
    basePath.joinpath("markdown", "treeprocessors.py"),
    basePath.joinpath("markdown", "inlinepatterns.py"),
    basePath.joinpath("markdown", "postprocessors.py"),
    basePath.joinpath("markdown", "serializers.py"),
    basePath.joinpath("markdown", "util.py"),
    basePath.joinpath("markdown", "htmlparser.py"),
    basePath.joinpath("markdown", "test_tools.py"),
    *sorted(basePath.joinpath("markdown", "extensions").rglob("*.py")),
]

for srcPath in modules:
    path = srcPath.relative_to(basePath)
    modulePath = path.with_suffix("")
    docPath = path.with_suffix(".md")
    fullDocPath = Path("reference", docPath)

    parts = tuple(modulePath.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        docPath = docPath.with_name("index.md")
        fullDocPath = fullDocPath.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue

    navParts = [f"<code>{part}</code>" for part in parts]
    nav[navParts] = docPath.as_posix()

    with mkdocs_gen_files.open(fullDocPath, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")
        if ident in perModuleOptions:
            yamlOptions = yaml.dump({"options": perModuleOptions[ident]})
            fd.write(f"\n{textwrap.indent(yamlOptions, prefix='    ')}")
        elif ident.startswith("markdown.extensions."):
            yamlOptions = yaml.dump({"options": {"inherited_members": False}})
            fd.write(f"\n{textwrap.indent(yamlOptions, prefix='    ')}")

    mkdocs_gen_files.set_edit_path(fullDocPath, ".." / path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as navFile:
    navFile.writelines(nav.build_literate_nav())
