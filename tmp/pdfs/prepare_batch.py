from pathlib import Path
import json
import subprocess
import pdfplumber
from pypdf import PdfReader

base = Path('D:/Work in Zheng Group/Dynamic Network-光')
papers = {
    'ann-biomed-2020': 's10439-020-02460-w.pdf',
    'sciadv-2022': 'sciadv.add5668.pdf',
    'rosales-2017': 'Angew Chem Int Ed - 2017 - Rosales - Hydrogels with Reversible Mechanics to Probe Dynamic Cell Microenvironments.pdf'
}
for key, name in papers.items():
    source = base / name
    out = Path('tmp/pdfs') / key
    out.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(source)
    text = '\n\n'.join(f'=== PAGE {i+1} ===\n{p.extract_text()}' for i, p in enumerate(reader.pages))
    (out/'article.txt').write_text(text, encoding='utf-8')
    print(f'=== {key}: {len(reader.pages)} pages ===\n{text[:6500]}')
    with pdfplumber.open(source) as pdf:
        geometry = []
        for i, page in enumerate(pdf.pages):
            matches = [{k:w[k] for k in ('text','x0','top','x1','bottom')} for w in page.extract_words() if w['text'] in ('Figure','FIGURE','Fig.','Scheme','Table','TABLE')]
            geometry.append({'page':i+1,'width':page.width,'height':page.height,'labels':matches})
        (out/'geometry.json').write_text(json.dumps(geometry,indent=2),encoding='utf-8')
    subprocess.run(['pdftoppm','-r','90','-png',str(source),str(out/'page')],check=True)
