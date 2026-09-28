// Validate real article data without depending on a browser or extra packages.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'script.js'), 'utf8');
const data = source.split('const pageContent =')[0];
const names = [...data.matchAll(/const (\w*Article) = \{/g)].map(match => match[1]);
const articles = vm.runInNewContext(`${data}\n[${names.join(',')}];`);
const ids = new Set();
let figures = 0;
for (const article of articles) {
  assert.ok(article.id && article.title && article.blocks.length, 'Missing article data');
  assert.ok(!ids.has(article.id), `Duplicate article ID: ${article.id}`);
  ids.add(article.id);
  for (const block of article.blocks) {
    if (block.type === 'figure') {
      assert.ok(fs.existsSync(path.join(root, block.figure.src)), block.figure.src);
      figures++;
    }
    if (block.type === 'link' && !/^https?:/.test(block.href)) {
      assert.ok(fs.existsSync(path.join(root, block.href)), block.href);
    }
  }
}
const required = ['标题', '期刊', '文章链接与 DOI', '通讯作者', '科学问题及解决方法', '具体细节及亮点'];
const dois = new Set();
let checked = 0;
for (const folder of fs.readdirSync(path.join(root, 'notes'))) {
  const manifestPath = path.join(root, 'notes', folder, 'figures.json');
  if (!fs.existsSync(manifestPath)) continue;
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  // Older OECT screenshot collections use a legacy figures.json schema and are
  // validated through their article/image checks above rather than the PDF extractor.
  if (!manifest.article_id) continue;
  assert.ok(!dois.has(manifest.doi.toLowerCase()), `Duplicate DOI: ${manifest.doi}`);
  dois.add(manifest.doi.toLowerCase());
  const added = articles.find(article => article.id === manifest.article_id);
  assert.ok(added, `Article missing: ${manifest.article_id}`);
  const headings = added.blocks.filter(block => block.type === 'heading').map(block => block.text);
  let previous = -1;
  for (const heading of required) {
    const index = headings.indexOf(heading);
    assert.ok(index > previous, `${folder}: missing or out-of-order heading: ${heading}`);
    previous = index;
  }
  const doiLink = `https://doi.org/${manifest.doi}`;
  assert.equal(articles.filter(article => article.blocks.some(block => block.href === doiLink)).length, 1,
    `${folder}: DOI must identify exactly one article`);
  const imageBlocks = added.blocks.filter(block => block.type === 'figure');
  assert.equal(imageBlocks.length, manifest.figures.length, `${folder}: figure count`);
  const report = JSON.parse(fs.readFileSync(path.join(path.dirname(manifestPath), 'extraction-report.json'), 'utf8'));
  assert.equal(report.dpi, manifest.dpi);
  assert.ok(manifest.dpi >= 300);
  for (let i = 0; i < imageBlocks.length; i++) {
    const figure = manifest.figures[i];
    assert.equal(imageBlocks[i].figure.src, figure.output);
    assert.ok(added.blocks.some(block => block.type === 'link' && block.href === figure.output));
    const bytes = fs.readFileSync(path.join(root, figure.output));
    assert.equal(bytes.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', 'Invalid PNG');
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), report.figures[i].sha256);
    assert.deepEqual([bytes.readUInt32BE(16), bytes.readUInt32BE(20)], report.figures[i].pixels);
  }
  checked++;
}
// User-supplied note screenshots have no PDF/DPI requirement; preserve their text and image bytes.
let checkedUserNotes = 0;
for (const folder of fs.readdirSync(path.join(root, 'notes'))) {
  const manifestPath = path.join(root, 'notes', folder, 'user-notes.json');
  if (!fs.existsSync(manifestPath)) continue;
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const article = articles.find(item => item.id === manifest.article_id);
  assert.ok(article, `${folder}: user-note article missing`);
  const normalizeHeading = text => text.replace(/^\d+\.\s*/, '').replace(/doi/ig, 'DOI').replace(/\s+/g, '');
  const headings = article.blocks.filter(block => block.type === 'heading').map(block => normalizeHeading(block.text));
  let previous = -1;
  for (const heading of required) {
    const index = headings.indexOf(normalizeHeading(heading));
    assert.ok(index > previous, `${folder}: missing or out-of-order heading: ${heading}`);
    previous = index;
  }
  const doiLink = `https://doi.org/${manifest.doi}`;
  assert.equal(articles.filter(item => item.blocks.some(block => block.href === doiLink)).length, 1,
    `${folder}: DOI must identify exactly one article`);
  const actualSegments = article.blocks.flatMap(block => block.type === 'list'
    ? block.items.map(text => ({ type: 'list_item', text }))
    : ['heading', 'paragraph'].includes(block.type) ? [block] : []);
  for (const segment of manifest.original_segments) {
    assert.equal(actualSegments.filter(actual => actual.type === segment.type &&
      (segment.type === 'heading' ? normalizeHeading(actual.text) === normalizeHeading(segment.text)
        : actual.text === segment.text)).length, 1, `${folder}: changed or missing user text: ${segment.text}`);
  }
  const images = article.blocks.filter(block => block.type === 'figure');
  assert.equal(images.length, manifest.figures.length);
  manifest.figures.forEach((figure, index) => {
    assert.equal(images[index].figure.src, figure.output);
    assert.ok(article.blocks.some(block => block.type === 'link' && block.href === figure.output));
    const bytes = fs.readFileSync(path.join(root, figure.output));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), figure.sha256);
    assert.deepEqual([bytes.readUInt32BE(16), bytes.readUInt32BE(20)], figure.pixels);
  });
  for (const screenshot of manifest.source_screenshots) assert.ok(fs.existsSync(path.join(root, screenshot)));
  checkedUserNotes++;
}

// Evaluate the category declarations too, catching misspelled registration references.
const categorySource = source.split('function renderCans() {')[1].match(/const categories = (\[[\s\S]*?\n  \]);/)[1];
const categories = vm.runInNewContext(`${data}\n${categorySource};`);
const registeredIds = categories.flatMap(category => category.articles.map(article => article.id));
const literatureSource = data.match(/const literatureRecords = (\[[^;]+\]);/)[1];
const literature = vm.runInNewContext(`${data}\n${literatureSource};`);
registeredIds.push(...literature.map(article => article.id));
assert.equal(new Set(registeredIds).size, registeredIds.length, 'Duplicate article registration');
for (const article of articles) assert.ok(registeredIds.includes(article.id), `Unreachable article: ${article.id}`);
console.log(`PASS: ${articles.length} unique, registered articles; ${figures} existing images; ${checked} PDF collections have six ordered sections, unique DOIs, linked figures and verified PNG hashes/dimensions.`);
if (checkedUserNotes) console.log(`PASS: ${checkedUserNotes} user-note collections retain every transcribed text segment and original image hash/dimensions.`);
