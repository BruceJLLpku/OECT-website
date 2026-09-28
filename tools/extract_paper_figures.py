"""Render reviewed PDF figure+caption rectangles directly with Poppler.

Coordinates are PDF points (1/72 inch), measured from the top-left.
Inspect source pages before choosing rectangles, then inspect every output.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image
from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--pdf", type=Path, help="Override original PDF location")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    spec = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = args.pdf or Path(spec["source_pdf"])
    renderer = shutil.which("pdftoppm")
    if not renderer:
        raise SystemExit("Poppler pdftoppm is required.")
    reader = PdfReader(source)
    dpi = spec.get("dpi", 400)
    report = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "dpi": dpi, "figures": []}
    for figure in spec["figures"]:
        page_number = figure["page"]
        page = reader.pages[page_number - 1]
        left, top, right, bottom = figure["bbox_pt"]
        if not (0 <= left < right <= float(page.mediabox.width)
                and 0 <= top < bottom <= float(page.mediabox.height)):
            raise ValueError(f"Invalid rectangle: {figure['label']}")
        destination = (root / figure["output"]).resolve()
        destination.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        x, y = math.floor(left * dpi / 72), math.floor(top * dpi / 72)
        width = math.ceil(right * dpi / 72) - x
        height = math.ceil(bottom * dpi / 72) - y
        subprocess.run([renderer, "-f", str(page_number), "-l", str(page_number),
                        "-singlefile", "-r", str(dpi), "-x", str(x), "-y", str(y),
                        "-W", str(width), "-H", str(height), "-png",
                        str(source), str(destination.with_suffix(""))], check=True)
        with Image.open(destination) as image:
            image.verify()
        with Image.open(destination) as image:
            size = list(image.size)
        report["figures"].append({**figure, "pixels": size,
                                  "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
        print(f"{figure['label']}: {size[0]} x {size[1]} px -> {figure['output']}")
    args.manifest.with_name("extraction-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
