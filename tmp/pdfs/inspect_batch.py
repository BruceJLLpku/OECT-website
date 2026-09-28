from PIL import Image, ImageDraw
from pathlib import Path
import pdfplumber

for key in ['ann-biomed-2020','sciadv-2022','rosales-2017']:
    directory = Path('tmp/pdfs') / key
    files = sorted(directory.glob('page-*.png'))
    canvas = Image.new('RGB',(1080,((len(files)+3)//4)*375),'white')
    for i, file in enumerate(files):
        with Image.open(file) as im:
            im.thumbnail((260,345))
            canvas.paste(im,((i%4)*270,(i//4)*375+25))
        ImageDraw.Draw(canvas).text(((i%4)*270+8,(i//4)*375+5),file.stem,fill='black')
    canvas.save(directory/'overview.jpg')

source=Path('D:/Work in Zheng Group/Dynamic Network-光/sciadv.add5668.pdf')
with pdfplumber.open(source) as pdf:
    texts = []
    for i,page in enumerate(pdf.pages):
        texts.append(f'=== PAGE {i+1} ===\n'+page.extract_text(x_tolerance=2))
    Path('tmp/pdfs/sciadv-2022/readable.txt').write_text('\n\n'.join(texts),encoding='utf-8')
