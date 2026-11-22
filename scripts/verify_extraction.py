#!/usr/bin/env python3
"""验证 erofs 提取完整性"""
import os

PARTS = ['system', 'product', 'system_ext', 'vendor', 'odm']
EXPECTED_MIN = {
    'system': 20000,
    'product': 1000,
    'system_ext': 1000,
    'vendor': 1000,
    'odm': 10,
}

all_ok = True
for part in PARTS:
    dst = f'/mnt/erofs/{part}'
    n = 0
    size = 0
    if os.path.isdir(dst):
        for root, dirs, files in os.walk(dst):
            n += len(files)
            for f in files:
                try:
                    size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    status = '✅' if n >= EXPECTED_MIN.get(part, 10) else '❌ 不完整'
    if n < EXPECTED_MIN.get(part, 10):
        all_ok = False
    print(f'{part}: {n} files, {size/1024/1024:.1f} MB {status}')
    if os.path.isdir(dst):
        entries = sorted(os.listdir(dst))[:12]
        print(f'   顶层: {entries}')

print('\n=== 关键文件检查 ===')
for probe in ['/mnt/erofs/system/system/build.prop',
              '/mnt/erofs/system/system/bin',
              '/mnt/erofs/system/system/framework',
              '/mnt/erofs/product/etc/build.prop',
              '/mnt/erofs/vendor/build.prop',
              '/mnt/erofs/vendor/bin']:
    print(f'  {probe}: {"✅" if os.path.exists(probe) else "❌"}')

if not all_ok:
    print('\n⚠️ 提取不完整！')
    raise SystemExit(1)
print('\n✅ 提取完整')
