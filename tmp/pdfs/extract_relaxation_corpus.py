from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


FILES = [
    r"D:\Work in Zheng Group\Dynamic Network-光\2012 AM  Matyjaszewski NCSS- 光.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2014 Macromolecule Bowman 光碱释放 Michael不可逆交联.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2017 AM Bowman 烯丙硫醚+自由基前体小分子 光降解水凝胶.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2017 AM Bowman 液晶+烯丙硫醚.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2019 NJP 烯丙基硫+LAP 光控交换.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2020 AM Anseth 硫醇结构调控烯丙硫醚光降解与类器官传代.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2020 AM Lewis 3D打印液晶+烯丙硫醚.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2020 Ann Biomed Eng Anseth 光封端巯基关闭硫酯水凝胶应力松弛.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2023 Sci Adv Anseth 光诱导黏弹性调控类器官曲率与隐窝形成.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2024 AM Campos 光二硫酯 动态弛豫时间.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2025 JACS Kalow DASA光热催化 烯胺.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2025 JACS Schlogl MP光控酸催化 酯交换.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2025 NatCom Yijun Zheng 光控二硫酯+Schiff碱 多样化弛豫时间水凝胶.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\Advanced Materials - 2021 - Zhu - Reconstructable Gradient Structures and Reprogrammable 3D Deformations of Hydrogels with (1).pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\nihms-715282.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\zhao-et-al-2023-light-controlled-chemical-reaction-pathways-in-disulfide-based-nonequilibrium-systems.pdf",
    r"D:\Work in Zheng Group\Dynamic Network-光\2005 Science 烯丙硫醚.pdf",
    r"D:\Work in Zheng Group\Dynamic Network\2020 Poly Chem Kalow Vitrimer硫代米氏酸酯.pdf",
    r"D:\Work in Zheng Group\Dynamic Network\2023 Chem Kalow 硫代米氏酸酯.pdf",
]

OUT = Path(__file__).resolve().parent / "text"
OUT.mkdir(parents=True, exist_ok=True)

term_re = re.compile(
    r"relax|Maxwell|time constant|characteristic time|half[- ]?life|t_?1/2|tau|"
    r"creep|frequency sweep|cross[- ]?over|terminal flow|viscoelastic|stress decay",
    re.I,
)
doi_re = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

records = []
for index, raw_path in enumerate(FILES, 1):
    path = Path(raw_path)
    reader = PdfReader(path)
    pages = []
    hits = []
    for pageno, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "")
        pages.append(f"\n\n===== PDF PAGE {pageno} =====\n{text}")
        lines = text.splitlines()
        for lineno, line in enumerate(lines):
            if term_re.search(line):
                lo = max(0, lineno - 2)
                hi = min(len(lines), lineno + 3)
                hits.append({
                    "page": pageno,
                    "context": "\n".join(lines[lo:hi]),
                })
    stem = f"{index:02d}_{re.sub(r'[^0-9A-Za-z._-]+', '_', path.stem)[:70]}"
    text_path = OUT / f"{stem}.txt"
    text_path.write_text("".join(pages), encoding="utf-8")
    full_text = "\n".join(pages)
    records.append({
        "index": index,
        "source": str(path),
        "text_path": str(text_path),
        "pages": len(reader.pages),
        "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
        "dois": sorted({m.group(0).rstrip(".,;)") for m in doi_re.finditer(full_text)}),
        "first_page": pages[0][:6000] if pages else "",
        "hits": hits,
    })
    print(f"[{index:02d}/19] {path.name}: {len(reader.pages)} pages, {len(hits)} keyword hits")

(OUT.parent / "corpus_index.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
)

