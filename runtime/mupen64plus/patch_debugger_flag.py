from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def patch(project: Path) -> int:
    text = project.read_text(encoding="utf-8-sig")
    root = ET.fromstring(text)
    ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    changed = 0
    for group in root.findall("m:ItemDefinitionGroup", ns):
        if group.attrib.get("Condition", "") != "'$(Configuration)|$(Platform)'=='Debug|x64'":
            continue
        defs = group.find("m:ClCompile/m:PreprocessorDefinitions", ns)
        if defs is None:
            raise SystemExit("Debug|x64 PreprocessorDefinitions missing")
        current = defs.text or ""
        if "DEBUGGER=1" not in current.split(";"):
            defs.text = "DEBUGGER=1;" + current
            changed += 1
    if changed not in (0, 1):
        raise SystemExit(f"unexpected changed count {changed}")
    ET.register_namespace("", ns["m"])
    ET.ElementTree(root).write(project, encoding="utf-8", xml_declaration=False)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vcxproj", type=Path)
    args = ap.parse_args()
    print(f"PATCHED={patch(args.vcxproj)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
