#!/usr/bin/env python3
"""组装新的 system.img 并生成同步哈希的 partition-layout.json"""
import hashlib, json, os

SECTOR = 512
PARTS = [
    ('init_boot', 20480, 3874816, None),
    ('recovery', 3895296, 16314368, None),
    ('system', 20209664, 542203904, 'rebuilt/system.img'),
    ('product', 562413568, 223920128, 'rebuilt/product.img'),
    ('system_ext', 786333696, 169660416, 'rebuilt/system_ext.img'),
    ('vendor', 955994112, 100225024, 'rebuilt/vendor.img'),
    ('odm', 1056219136, 286720, 'rebuilt/odm.img'),
]
TOTAL = 1056526336

with open('system.img', 'rb') as src:
    orig = src.read()

comp = {}
for name, start, size, rf in PARTS:
    if rf and os.path.exists(rf):
        data = open(rf, 'rb').read()
        comp[name] = data
        pct = len(data) / size * 100
        flag = '⚠️ 数据量过少!' if pct < 50 else '✅'
        print(f'{name}: {len(data)} bytes / {size} ({pct:.1f}%) {flag}')

new = bytearray(TOTAL)
for name, start, size, rf in PARTS:
    if name in comp:
        new[start:start+len(comp[name])] = comp[name]
    else:
        new[start:start+size] = orig[start:start+size]

# 修复 GPT (主表 + 备表)
new[:34 * 512] = orig[:34 * 512]
new[-33 * 512:] = orig[-33 * 512:]

with open('system.img.rebuilt', 'wb') as f:
    f.write(new)

layout = json.load(open('partition-layout.json'))
layout['system_disk']['sha256'] = hashlib.sha256(new).hexdigest()
for p in layout['system_disk']['partitions']:
    part = new[p['start_bytes']:p['start_bytes'] + p['size_bytes']]
    p['sha256'] = hashlib.sha256(part).hexdigest()

with open('partition-layout.rebuilt.json', 'w') as f:
    json.dump(layout, f, indent=2)

print(f'\n✅ system.img.rebuilt ({os.path.getsize("system.img.rebuilt")} bytes)')
print(f'✅ partition-layout.rebuilt.json (system_disk.sha256={layout["system_disk"]["sha256"][:16]}...)')
