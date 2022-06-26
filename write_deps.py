import toml
import markdown

with open("./pyproject.toml", "r") as f:
    tomlfile = toml.load(f)
with open("./docs/dependencies.md", "w") as f:
    f.write("## Dependencies\n")
    for depname, depvers in tomlfile["tool"]["poetry"].get("dependencies").items():
        if depname not in ["markdown", "Markdown", "toml"]:
            line = f"- ```{depname}``` == {depvers}\n"
            f.write(line)