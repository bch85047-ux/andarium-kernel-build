#!/usr/bin/env python3
"""拆分 system.img 为各 erofs 分区文件"""
import os

SECTOR = 512
PARTS = [
    ('init_boot', 20480, 3874816),
    ('recovery', 3895296, 16314368),
    ('system', 20209664, 542203904),
    ('product', 562413568, 223920128),
    ('system_ext', 786333696, 169660416),
    ('vendor', 955994112, 100225024),
    ('odm', 1056219136, 286720),
]

os.makedirs('parts', exist_ok=True)
with open('system.img', 'rb') as f:
    for name, start, size in PARTS:
        f.seek(start)
        with open(f'parts/{name}.img', 'wb') as out:
            out.write(f.read(size))
        print(f'{name}: {size} bytes')

print('✅ 分区拆分完成')
