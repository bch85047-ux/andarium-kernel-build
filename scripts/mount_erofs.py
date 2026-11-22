#!/usr/bin/env python3
"""用 erofsfuse 挂载并复制所有 erofs 分区内容"""
import os, subprocess, shutil

PARTS = ['system', 'product', 'system_ext', 'vendor', 'odm']

os.makedirs('/mnt/erofs', exist_ok=True)

for part in PARTS:
    dst = f'/mnt/erofs/{part}'
    tmp = f'/tmp/fuse_{part}'
    os.makedirs(dst, exist_ok=True)
    os.makedirs(tmp, exist_ok=True)

    print(f'=== mount {part} ===')
    r = subprocess.run(['sudo', 'erofsfuse', '-o', 'ro', f'parts/{part}.img', tmp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  erofsfuse 失败: {r.stderr[:150]}')
        # fallback: fsck.erofs --extract
        for cmd in (['fsck.erofs', f'--extract={dst}', f'parts/{part}.img'],
                    ['fsck.erofs', '--extract', dst, f'parts/{part}.img']):
            r2 = subprocess.run(cmd, capture_output=True, text=True)
            if r2.returncode == 0:
                print(f'  fsck.erofs 提取成功')
                break
        continue

    print('  挂载成功，复制中...')
    r2 = subprocess.run(['sudo', 'cp', '-a', f'{tmp}/.', f'{dst}/'], capture_output=True, text=True)
    subprocess.run(['sudo', 'umount', tmp], capture_output=True)

    n = sum(len(files) for _, _, files in os.walk(dst))
    print(f'  文件数: {n}')

print('✅ 挂载提取完成')
for part in PARTS:
    dst = f'/mnt/erofs/{part}'
    if os.path.isdir(dst):
        n = sum(len(files) for _, _, files in os.walk(dst))
        print(f'  {part}: {n} files')
