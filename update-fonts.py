#!/usr/bin/env python3
"""Remplace Google Fonts par les polices auto-hébergées dans tous les fichiers .html.
Usage (à la racine du dépôt) : python3 update-fonts.py
Relançable sans risque : les fichiers déjà mis à jour sont ignorés."""
import re, pathlib

BLOCK = (
    '<link rel="preload" href="/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
    '<link rel="preload" href="/fonts/space-grotesk-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
    '<link rel="stylesheet" href="/css/fonts.css">\n'
)
PATTERNS = [
    r'[ \t]*<link[^>]+rel="preconnect"[^>]+fonts\.googleapis\.com[^>]*>[ \t]*\n?',
    r'[ \t]*<link[^>]+rel="preconnect"[^>]+fonts\.gstatic\.com[^>]*>[ \t]*\n?',
    r'[ \t]*<link[^>]+fonts\.googleapis\.com/css2[^>]*>[ \t]*\n?',
]

changed = skipped = 0
for path in sorted(pathlib.Path('.').rglob('*.html')):
    if any(p in ('node_modules', '.git') for p in path.parts):
        continue
    src = path.read_text(encoding='utf-8')
    if '/css/fonts.css' in src:
        skipped += 1
        continue
    if 'fonts.googleapis.com' not in src and 'fonts.gstatic.com' not in src:
        skipped += 1
        continue
    first = min(m.start() for p in PATTERNS for m in [re.search(p, src)] if m)
    out = src
    for p in PATTERNS:
        out = re.sub(p, '', out)
    out = out[:first] + BLOCK + out[first:]
    path.write_text(out, encoding='utf-8')
    changed += 1
    print('mis à jour :', path)
print(f'Terminé : {changed} fichier(s) modifié(s), {skipped} ignoré(s).')
