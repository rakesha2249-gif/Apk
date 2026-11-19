
from pathlib import Path
import re

path = Path("decoded/res/values/strings.xml")

original = path.read_text(encoding="utf-8")
modified = original

names = (
    "system_error_manufacturer",
    "system_error_wipe_data",
)

for name in names:
    pattern = (
        r'(<string\b[^>]*\bname=["\']'
        + re.escape(name)
        + r'["\'][^>]*>)'
        + r'(.*?)'
        + r'(</string>)'
    )

    matches = list(
        re.finditer(pattern, modified, re.DOTALL)
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one string: {name}, "
            f"found {len(matches)}"
        )

    modified = re.sub(
        pattern,
        lambda m: m.group(1) + m.group(3),
        modified,
        count=1,
        flags=re.DOTALL,
    )

if modified == original:
    raise RuntimeError("No changes made")

path.write_text(modified, encoding="utf-8")

print("Target strings cleared without XML rewrite")
