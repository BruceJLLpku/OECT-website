from pathlib import Path
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
import pdfplumber
from PIL import Image, ImageDraw

papers = {
    'marozas-2019': 'Marozas_2019_New_J._Phys._21_045004.pdf',
    'campos-2024': '2024 AM Campos 光二硫酯 动态弛豫时间.pdf',
}
base = Path('D:/Work in Zheng Group/Dynamic Network-光')

def prepare(item):
    key, name = item
    source = base / name
    out = Path('tmp/pdfs') / key
    out.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(source)
    text = '\n\n'.join(f'=== PAGE {i+1} ===\n{p.extract_text()}' for i, p in enumerate(reader.pages))
    (out/'article.txt').write_text(text, encoding='utf-8')
    with pdfplumber.open(source) as pdf:
        geometry = []
        for i, page in enumerate(pdf.pages):
            words = page.extract_words()
            geometry.append({'page': i+1, 'width': page.width, 'height': page.height,
                'labels': [w for w in words if w['text'] in ('Figure','FIGURE','Fig.','Scheme','Table','TABLE')]})
        (out/'geometry.json').write_text(json.dumps(geometry, indent=2), encoding='utf-8')
    subprocess.run(['pdftoppm','-r','100','-png',str(source),str(out/'page')],check=True)
    files = sorted(out.glob('page-*.png'))
    canvas = Image.new('RGB',(1080,((len(files)+3)//4)*400),'white')
    for i, file in enumerate(files):
        with Image.open(file) as im:
            im.thumbnail((260,370))
            canvas.paste(im,((i%4)*270,(i//4)*400+25))
        ImageDraw.Draw(canvas).text(((i%4)*270+8,(i//4)*400+5),file.stem,fill='black')
    canvas.save(out/'overview.jpg')
    return f'=== {key}: {len(reader.pages)} pages ===\n{text[:6500]}'

with ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(prepare, papers.items()):
        print(result)
