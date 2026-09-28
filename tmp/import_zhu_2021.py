import hashlib
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest_path = root / 'notes/zhu-2021/user-notes.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
segments = manifest['original_segments']
blocks = []

def heading(text):
    blocks.append({'type': 'heading', 'text': text})

def paragraph(text):
    blocks.append({'type': 'paragraph', 'text': text})

def append_segment(segment, number=None):
    if segment['type'] == 'list_item':
        if blocks and blocks[-1]['type'] == 'list':
            blocks[-1]['items'].append(segment['text'])
        else:
            blocks.append({'type': 'list', 'items': [segment['text']]})
    elif number is not None:
        heading(f"{number}. {segment['text']}")
    else:
        blocks.append(dict(segment))

def figure(index):
    f = manifest['figures'][index]
    width = struct.unpack('>I', (root / f['output']).read_bytes()[16:20])[0]
    blocks.append({'type': 'figure', 'figure': {
        'src': f['output'], 'alt': f['label'] + '：用户提供的完整论文图及英文图注',
        'caption': f['label'] + '｜用户提供的原图，含英文图注。', 'maxWidth': f'{width}px'}})
    blocks.append({'type': 'link', 'label': '查看 ' + f['label'] + ' 原尺寸图片（含图注）', 'href': f['output']})

heading('标题')
paragraph('Reconstructable Gradient Structures and Reprogrammable 3D Deformations of Hydrogels with Coumarin Units as the Photolabile Crosslinks')
heading('期刊')
paragraph('Advanced Materials，33(18)，2008057（2021）；在线发表于 2021 年 3 月 31 日。')
heading('文章链接与 DOI')
blocks.extend([
    {'type': 'link', 'label': '文章链接：Wiley Online Library', 'href': 'https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.202008057'},
    {'type': 'link', 'label': 'DOI：10.1002/adma.202008057', 'href': 'https://doi.org/10.1002/adma.202008057'}])
heading('通讯作者')
paragraph('Zi Liang Wu：浙江大学，高分子科学与工程学系，高分子合成与功能构造教育部重点实验室；wuziliang@zju.edu.cn。')
heading('科学问题及解决方法')
number = 0
for segment in segments:
    if segment['type'] == 'heading':
        number += 1
        if number == 4:
            heading('具体细节及亮点')
        append_segment(segment, number)
        if number == 4:
            figure(0)
        elif number == 6:
            figure(1)
    else:
        append_segment(segment)

assert number == 7
article = {'id': manifest['article_id'],
           'title': '2021 AM Wu 香豆素光交联水凝胶的可擦写三维形变',
           'blocks': blocks}
script_path = root / 'script.js'
source = script_path.read_text(encoding='utf-8')
assert manifest['doi'] not in source, 'Existing DOI'
assert 'Dissociative Exchange' not in source, 'Category already exists'
assert source.count('const literatureRecords = [];') == 1
category_anchor = '      articles: [carberryThioesterArticle, kalowDithioalkylideneArticle, enamineDasaArticle, schloglPhotoacidArticle]\n    }'
assert source.count(category_anchor) == 1
updated = source.replace('const literatureRecords = [];',
    'const zhuCoumarinReprogrammableArticle = ' + json.dumps(article, ensure_ascii=False, indent=2) + ';\n\nconst literatureRecords = [];')
updated = updated.replace(category_anchor, category_anchor + ",\n    {\n      title: 'Dissociative Exchange',\n      image: 'assets/cans-zhu-2021-figure1.png',\n      alt: '香豆素可逆光二聚与光解交联网络示意图',\n      articles: [zhuCoumarinReprogrammableArticle]\n    }")
for f in manifest['figures']:
    raw = (root / f['output']).read_bytes()
    assert raw == Path(f['source']).read_bytes(), 'Image changed'
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    f['sha256'] = hashlib.sha256(raw).hexdigest()
    f['pixels'] = list(struct.unpack('>II', raw[16:24]))
script_path.write_text(updated, encoding='utf-8', newline='\r\n')
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Imported one article from all', len(segments), 'user text segments; added Dissociative Exchange category; original image bytes verified.')
