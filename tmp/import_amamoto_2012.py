import hashlib
import json
import re
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest_path = root / 'notes/amamoto-2012/user-notes.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
segments = manifest['original_segments']
blocks = []

def heading(text):
    blocks.append({'type': 'heading', 'text': text})

def paragraph(text):
    blocks.append({'type': 'paragraph', 'text': text})

def append_segments(items):
    for segment in items:
        if segment['type'] == 'list_item':
            if blocks and blocks[-1]['type'] == 'list':
                blocks[-1]['items'].append(segment['text'])
            else:
                blocks.append({'type': 'list', 'items': [segment['text']]})
        else:
            blocks.append(dict(segment))

def group(label, new_heading=None):
    start = next(i for i, s in enumerate(segments) if s['type'] == 'heading' and s['text'] == label)
    end = next((i for i in range(start + 1, len(segments)) if segments[i]['type'] == 'heading'), len(segments))
    result = [dict(s) for s in segments[start:end]]
    if new_heading:
        result[0]['text'] = new_heading
    return result

def figure(index):
    f = manifest['figures'][index]
    blocks.append({'type': 'figure', 'figure': {
        'src': f['output'], 'alt': f['label'] + '：用户提供的完整论文图及英文图注',
        'caption': f['label'] + '｜用户提供的原图，含英文图注。', 'maxWidth': '1000px'}})
    blocks.append({'type': 'link', 'label': '查看 ' + f['label'] + ' 原尺寸图片（含图注）', 'href': f['output']})

heading('标题')
paragraph('Self-Healing of Covalently Cross-Linked Polymers by Reshuffling Thiuram Disulfide Moieties in Air under Visible Light')
heading('期刊')
paragraph('Advanced Materials，24(29)，3975–3980（2012）；在线发表于 2012 年 6 月 22 日。')
heading('文章链接与 DOI')
blocks.extend([
    {'type': 'link', 'label': '文章链接：Wiley Online Library', 'href': 'https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.201201928'},
    {'type': 'link', 'label': 'DOI：10.1002/adma.201201928', 'href': 'https://doi.org/10.1002/adma.201201928'}])
heading('通讯作者')
blocks.append({'type': 'list', 'items': [
    'Atsushi Takahara：日本九州大学，Institute for Materials Chemistry and Engineering；takahara@cstf.kyushu-u.ac.jp。',
    'Krzysztof Matyjaszewski：美国卡内基梅隆大学，Department of Chemistry；km3b@andrew.cmu.edu。']})
heading('科学问题及解决方法')
append_segments(segments[:2])
append_segments(group('1. 研究背景与突破点'))
append_segments(group('2. 核心愈合机制'))
heading('具体细节及亮点')
materials = group('3. 材料设计')
append_segments(materials[:2])
figure(0)
append_segments(materials[2:])
append_segments(group('4. 关键实验结果'))
append_segments(group('聚合物网络结构设计', '5. 聚合物网络结构设计'))
figure(1)
append_segments(group('流变学性能对比 (25 °C, 可见光照射)', '6. 流变学性能对比 (25 °C, 可见光照射)'))
append_segments(group('总结'))

article = {'id': manifest['article_id'],
           'title': '2012 AM Takahara/Matyjaszewski 可见光驱动 TDS 聚氨酯自愈合',
           'blocks': blocks}
script_path = root / 'script.js'
source = script_path.read_text(encoding='utf-8')
assert manifest['doi'] not in source, 'Existing DOI'
assert source.count('const literatureRecords = [];') == 1
assert source.count('        weiLivingPolymerNetworkArticle,') == 1
updated = source.replace('const literatureRecords = [];',
    'const amamotoTdsSelfHealingArticle = ' + json.dumps(article, ensure_ascii=False, indent=2) + ';\n\nconst literatureRecords = [];')
updated = updated.replace('        weiLivingPolymerNetworkArticle,',
    '        amamotoTdsSelfHealingArticle,\n        weiLivingPolymerNetworkArticle,')
for f in manifest['figures']:
    raw = (root / f['output']).read_bytes()
    assert raw == Path(f['source']).read_bytes(), 'Image changed'
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    f['sha256'] = hashlib.sha256(raw).hexdigest()
    f['pixels'] = list(struct.unpack('>II', raw[16:24]))
script_path.write_text(updated, encoding='utf-8', newline='\r\n')
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Imported one article from all', len(segments), 'user text segments; original image bytes verified.')
