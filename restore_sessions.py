"""Restore the bundled session snapshot into local, ignored runtime storage.

Uses Python's standard library. Existing sessions are skipped, not overwritten.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parent


def bundled_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f'Missing or invalid bundled file: {relative}')
    return path


def verify_media(item):
    path = bundled_path(item['path'])
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    if h.hexdigest() != item['sha256']:
        raise ValueError(f"Checksum mismatch: {item['path']}")
    return path


def restore():
    manifest = json.loads((ROOT / 'outputs/manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported session manifest version')
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    restored = 0
    with sqlite3.connect(data / 'sessions.sqlite3') as db:
        db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL, mode TEXT NOT NULL, source TEXT NOT NULL, filename TEXT NOT NULL, result TEXT, error TEXT)')
        for item in manifest['sessions']:
            sid = str(uuid.UUID(item['id']))
            if db.execute('SELECT 1 FROM sessions WHERE id=?', (sid,)).fetchone():
                continue
            filename = item['filename']
            if Path(filename).name != filename or filename in ('', '.', '..'):
                raise ValueError('Invalid session filename')
            source = verify_media(item['input']) if item.get('input') else None
            playable = verify_media(item['playable']) if item.get('playable') else None
            result = bundled_path(item['analysis_path']).read_text(encoding='utf-8') if item.get('analysis_path') else None
            if result is not None:
                json.loads(result)
            folder = data / sid
            if folder.exists():
                raise FileExistsError(f'Unregistered session folder already exists: {sid}')
            folder.mkdir()
            if source:
                shutil.copy2(source, folder / filename)
            if playable:
                shutil.copy2(playable, folder / 'playable.mp4')
            db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (sid, item['created_at'], item['status'], item['mode'], item['source'], filename, result, item.get('error')))
            db.commit()
            restored += 1
    print(f'Restored {restored} saved sessions; existing sessions were preserved.')


if __name__ == '__main__':
    restore()
