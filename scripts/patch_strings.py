
from pathlib import Path
import xml.etree.ElementTree as ET

path = Path("decoded/res/values/strings.xml")

names = {
    "system_error_manufacturer",
    "system_error_wipe_data",
}

tree = ET.parse(path)
root = tree.getroot()

found = set()

for element in root.findall("string"):
    name = element.get("name")

    if name in names:
        element.text = ""
        found.add(name)

missing = names - found

if missing:
    raise RuntimeError(
        f"Missing strings: {sorted(missing)}"
    )

tree.write(
    path,
    encoding="utf-8",
    xml_declaration=True
)

print("English target strings cleared")
