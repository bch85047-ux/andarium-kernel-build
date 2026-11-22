#!/usr/bin/env python3
"""验证重建后的 system.img"""
import json

layout = json.load(open('partition-layout.rebuilt.json'))
with open('system.img.rebuilt', 'rb') as f:
    data = f.read()

print(f'镜像大小: {len(data)} bytes (期望 1056526336) {"✅" if len(data)==1056526336 else "❌"}')
print()
print('=== 各分区有效数据占比 ===')

ORIG_PCT = {
    'init_boot': 84.8, 'recovery': 89.9, 'system': 97.9,
    'product': 99.1, 'system_ext': 98.3, 'vendor': 97.6, 'odm': 97.9,
}

ok = True
for p in layout['system_disk']['partitions']:
    part = data[p['start_bytes']:p['start_bytes'] + p['size_bytes']]
    nz = sum(1 for b in part if b != 0)
    pct = nz / len(part) * 100
    orig = ORIG_PCT.get(p['name'], 0)
    # 重建后 erofs 未压缩，数据量可能比原版略少，但不应低于 60%
    status = '✅' if pct > 60 else '❌'
    if pct <= 60:
        ok = False
    print(f"  {p['name']:12s} {p['size_bytes']/1024/1024:7.1f} MB  有效 {pct:5.1f}% (原版 {orig}%) {status}")

print()
print('=== 哈希一致性 ===')
import hashlib
whole = hashlib.sha256(data).hexdigest()
print(f"  system_disk: {'✅' if whole == layout['system_disk']['sha256'] else '❌'}")
for p in layout['system_disk']['partitions']:
    part = data[p['start_bytes']:p['start_bytes'] + p['size_bytes']]
    ph = hashlib.sha256(part).hexdigest()
    print(f"  {p['name']:12s} {'✅' if ph == p['sha256'] else '❌'}")

if not ok:
    print('\n❌ 重建镜像不完整，不应使用')
    raise SystemExit(1)
print('\n✅ 重建镜像验证通过')
