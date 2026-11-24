#!/usr/bin/env python3
"""Validate the initial infographic knowledge base without third-party packages."""
from __future__ import annotations
import re
import sys
import csv
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
LOGIC = ROOT / '01-信息图形数据逻辑'
CASE = ROOT / '02-信息图形类型案例'
issues = []

files = sorted(ROOT.rglob('*.md'))
logic_files = sorted(LOGIC.glob('*.md'))
if len(logic_files) != 5:
    issues.append(f'01/ expected exactly 5 .md files, got {len(logic_files)}')
for path in LOGIC.rglob('*'):
    if path.is_file() and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
        issues.append(f'image not allowed in logic directory: {path.relative_to(ROOT)}')

for f in logic_files:
    text=f.read_text('utf-8')
    for name in ('## A.', '## B.', '## C.', '## D.', '## E.'):
        if name not in text:
            issues.append(f'missing {name} section in {f.relative_to(ROOT)}')
    if '../02-信息图形类型案例/' not in text:
        issues.append(f'missing 02/ case cross-reference in {f.relative_to(ROOT)}')

pattern = re.compile(r'!?\[[^\]\n]*\]\(([^\)\n]+)\)')
for f in files:
    src=f.read_text(encoding='utf-8')
    # Avoid interpreting example markdown in fenced code and inline code as real links.
    src=re.sub(r'^\s*(```|~~~)[\s\S]*?^\s*\1[^\n]*(?:\n|$)', '', src, flags=re.MULTILINE)
    src=re.sub(r'`[^`\n]*`', '', src)
    for link in pattern.findall(src):
        link=link.strip()
        if not link:
            continue
        if link.startswith('<') and link.endswith('>'):
            link=link[1:-1]
        # Plain path; authored links do not use optional markdown titles.
        if link.startswith('#'):
            continue
        scheme=urlparse(link).scheme.lower()
        if scheme or link.startswith('//') or link.startswith('mailto:'):
            continue
        pure=unquote(link.split('#',1)[0].split('?',1)[0])
        target=(f.parent/pure).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            issues.append(f'link escapes repository: {f.relative_to(ROOT)} -> {link}')
        elif not target.exists():
            issues.append(f'broken link: {f.relative_to(ROOT)} -> {link}')

for folder in ['01-混合型-Mixed-Charts', '02-文字型列表型-Informational-List', '03-时间轴型-Timeline', '04-示意图型-How-to', '05-流程图型-Process', '06-比较型-Comparison', '07-地标型-Location', '08-图片式-Photo-graphic', '09-层级表现型-Hierarchical', '10-单一图表型-Single-Chart', '11-文字可视化-Visualized-Text', '12-解剖型-Anatomical', '13-视觉简历-Visual-Resume', '14-手稿型-Hand-drawn', '15-编年编目复合型-Hybrid', '16-三维型-3D', '17-词云信息图-Word-Cloud']:
    if not (CASE/folder/'00-标签说明.md').is_file():
        issues.append(f'missing tag definition: {folder}')

for f in files:
    for link in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', f.read_text(encoding='utf-8')):
        if not urlparse(link).scheme:
            target = (f.parent / unquote(link)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                issues.append(f'broken HTML image: {f.relative_to(ROOT)} -> {link}')

for f in ROOT.rglob('*.csv'):
    with f.open(encoding='utf-8-sig', newline='') as stream:
        rows = [row for row in csv.reader(stream) if row]
    if not rows or len(set(rows[0])) != len(rows[0]):
        issues.append(f'invalid CSV header: {f.relative_to(ROOT)}')
    elif any(len(row) != len(rows[0]) for row in rows):
        issues.append(f'inconsistent CSV fields: {f.relative_to(ROOT)}')

if issues:
    for i in issues:
        print('ERROR:',i)
    sys.exit(1)
print(f'OK: {len(files)} markdown documents, {len(logic_files)} logic definitions, no broken local links, no images in 01/.')
