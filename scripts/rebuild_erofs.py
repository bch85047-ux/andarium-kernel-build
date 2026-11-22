#!/usr/bin/env python3
"""重建未压缩 erofs 镜像（保持与内核兼容）"""
import os, subprocess

PARTS = ['system', 'product', 'system_ext', 'vendor', 'odm']

os.makedirs('rebuilt', exist_ok=True)

for part in PARTS:
    src = f'/mnt/erofs/{part}'
    dst = f'rebuilt/{part}.img'
    if not os.path.isdir(src):
        print(f'⚠️ {part}: 源目录不存在，跳过')
        continue

    n = sum(len(files) for _, _, files in os.walk(src))
    if n == 0:
        print(f'⚠️ {part}: 空目录，跳过')
        continue

    print(f'=== rebuild {part} ({n} files) ===')
    r = subprocess.run(['mkfs.erofs', '-b', '4096', '--all-time', dst, src],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ 失败: {r.stderr[:200]}')
        raise SystemExit(f'{part} 重建失败')

    size = os.path.getsize(dst)
    print(f'  ✅ {size} bytes ({size/1024/1024:.1f} MB)')

print('✅ 全部 erofs 重建完成')
