#!/usr/bin/env python3
import zipfile, sys, os, shutil, tempfile

def repack(input_ipa, output_ipa, new_kernel_cmdline, new_system_img):
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(input_ipa, 'r') as z:
            z.extractall(tmpdir)
        
        app_dir = os.path.join(tmpdir, 'Payload', 'Andarium.app')
        
        # 替换 kernel cmdline
        if new_kernel_cmdline:
            cmdline_path = os.path.join(app_dir, 'andarium-system', 'boot', 'kernel-command-line.txt')
            shutil.copy2(new_kernel_cmdline, cmdline_path)
        
        # 替换 system.img
        if new_system_img:
            sysimg_path = os.path.join(app_dir, 'andarium-system', 'guest', 'system.img')
            shutil.copy2(new_system_img, sysimg_path)
        
        # 重打包
        with zipfile.ZipFile(output_ipa, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    fp = os.path.join(root, f)
                    arc = os.path.relpath(fp, tmpdir)
                    z.write(fp, arc)
    
    print(f"✅ IPA 重打包完成: {output_ipa}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 repack_ipa.py <输入.ipa> <输出.ipa> [kernel_cmdline] [system.img]")
        sys.exit(1)
    repack(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else None, sys.argv[4] if len(sys.argv)>4 else None)