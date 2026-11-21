#!/usr/bin/env python3
"""
Andarium system.img erofs 压缩脚本
将 system 和 vendor 分区用 lz4hc 压缩，保持分区边界与 GPT 完全一致
"""
import os, sys, hashlib, subprocess, tempfile, shutil

def run_cmd(cmd, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)

def compress_partition(input_img, partition_name, start_byte, size, output_dir, algo='lz4hc'):
    """提取分区 -> 解压 erofs -> 重建压缩 erofs -> 返回压缩数据"""
    part_file = os.path.join(output_dir, f"{partition_name}.img")
    extract_dir = os.path.join(output_dir, f"{partition_name}_extracted")
    compressed_file = os.path.join(output_dir, f"{partition_name}_compressed.img")
    
    # 1. 提取分区
    with open(input_img, 'rb') as f:
        f.seek(start_byte)
        data = f.read(size)
    with open(part_file, 'wb') as f:
        f.write(data)
    
    # 2. 解压 erofs
    os.makedirs(extract_dir, exist_ok=True)
    run_cmd(['fsck.erofs', f'--extract={extract_dir}', part_file])
    
    # 3. 重建压缩 erofs
    if algo == 'lz4hc':
        run_cmd(['mkfs.erofs', '-b', '4096', '-z', 'lz4hc', compressed_file, extract_dir])
    elif algo == 'zstd':
        run_cmd(['mkfs.erofs', '-b', '4096', '-z', 'zstd:3', compressed_file, extract_dir])
    
    # 4. 读取压缩数据
    with open(compressed_file, 'rb') as f:
        compressed_data = f.read()
    
    print(f"  {partition_name}: {size} -> {len(compressed_data)} bytes (节省 {size-len(compressed_data)} bytes, {100*(1-len(compressed_data)/size):.1f}%)")
    
    return compressed_data

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <输入system.img> <输出system.img>")
        sys.exit(1)
    
    input_img = sys.argv[1]
    output_img = sys.argv[2]
    
    # Andarium 分区布局 (来自 partition-layout.json)
    # 单位：字节
    partitions = [
        # name, start_byte, size, compress?
        ('init_boot', 20480, 3874816, False),
        ('recovery', 3895296, 16314368, False),
        ('system', 20209664, 542203904, True),
        ('product', 562413568, 223920128, False),   # 太小不压缩
        ('system_ext', 786333696, 169660416, False),
        ('vendor', 955994112, 100225024, True),
        ('odm', 1056219136, 286720, False),
    ]
    
    TOTAL_SIZE = 1056526336
    
    with open(input_img, 'rb') as f:
        orig_data = f.read()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        compressed_parts = {}
        
        for name, start, size, compress in partitions:
            if compress:
                compressed_parts[name] = compress_partition(input_img, name, start, size, tmpdir)
            else:
                compressed_parts[name] = None
        
        # 构建新镜像
        new_img = bytearray(TOTAL_SIZE)
        current = 0
        
        for name, start, size, compress in partitions:
            # 填充 gap
            if current < start:
                new_img[current:start] = b'\x00' * (start - current)
                current = start
            
            if compress and compressed_parts[name]:
                comp_data = compressed_parts[name]
                new_img[current:current+len(comp_data)] = comp_data
                current += len(comp_data)
                # 零填充剩余分区空间
                remaining = size - len(comp_data)
                if remaining > 0:
                    new_img[current:current+remaining] = b'\x00' * remaining
                    current += remaining
            else:
                new_img[current:current+size] = orig_data[current:current+size]
                current += size
        
        # 填充尾部
        if current < TOTAL_SIZE:
            new_img[current:] = b'\x00' * (TOTAL_SIZE - current)
        
        with open(output_img, 'wb') as f:
            f.write(new_img)
        
        # 修复 GPT (复制原版主/备 GPT)
        with open(input_img, 'rb') as f:
            main_gpt = f.read(34 * 512)
            f.seek(-33 * 512, 2)
            backup_gpt = f.read(33 * 512)
        
        with open(output_img, 'r+b') as f:
            f.seek(0)
            f.write(main_gpt)
            f.seek(-33 * 512, 2)
            f.write(backup_gpt)
        
        # 验证
        result = subprocess.run(['sgdisk', '-p', output_img], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GPT 分区表验证通过")
            print(result.stdout)
        else:
            print("⚠️ GPT 验证失败，尝试 sgdisk -e 修复")
            subprocess.run(['sgdisk', '-e', output_img], capture_output=True)
        
        print(f"✅ 压缩完成: {output_img} ({os.path.getsize(output_img)/1024/1024:.1f} MB)")
        print(f"   原版: {os.path.getsize(input_img)/1024/1024:.1f} MB")
        print(f"   节省: {(os.path.getsize(input_img)-os.path.getsize(output_img))/1024/1024:.1f} MB")

if __name__ == '__main__':
    main()