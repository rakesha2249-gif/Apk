from pathlib import Path
import re

path = Path("decoded/res/values/strings.xml")

names = (
    "system_error_manufacturer",
    "system_error_wipe_data",
)

text = path.read_text(encoding="utf-8")

for name in names:
    pattern = (
        rf'(<string\b[^>]*\bname="{name}"[^>]*>)'
        rf'(.*?)'
        rf'(</string>)'
    )

    text, count = re.subn(
        pattern,
        lambda m: m.group(1) + m.group(3),
        text,
        count=1,
        flags=re.DOTALL,
    )

    if count != 1:
        raise RuntimeError(
            f"String not found: {name}"
        )

path.write_text(text, encoding="utf-8")

print("English target strings cleared")
