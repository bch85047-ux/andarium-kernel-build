#!/bin/bash
set -euo pipefail

# Andarium 内核编译 + system.img 压缩一键脚本
# 适用于：GitHub Codespaces / GitPod / UTM Ubuntu VM / 任意 ARM64 Linux

KERNEL_DIR="/workspaces/linux-6.18"
OUT_DIR="/workspaces/out"
PATCHES_DIR="/workspaces/patches"
ORIGINAL_SYSTEM_IMG="/workspaces/system.img"

mkdir -p "$OUT_DIR"

echo "=== [1/6] 编译优化内核 ==="
cd "$KERNEL_DIR"
make ARCH=um andarium_opt_defconfig
make ARCH=um -j$(nproc) CC=clang LLVM=1 2>&1 | tee "$OUT_DIR/build.log"

# 产出：linux (UML 内核二进制)
cp linux "$OUT_DIR/linux-optimized"
echo "✅ 内核编译完成: $OUT_DIR/linux-optimized ($(du -h $OUT_DIR/linux-optimized | cut -f1))"

echo "=== [2/6] 压缩 system.img (erofs lz4hc) ==="
if [ -f "$ORIGINAL_SYSTEM_IMG" ]; then
  python3 /workspaces/scripts/compress_system_img.py \
    "$ORIGINAL_SYSTEM_IMG" \
    "$OUT_DIR/system.img.compressed"
  echo "✅ system.img 压缩完成"
else
  echo "⚠️ 未找到原版 system.img，跳过压缩"
  echo "   请将原版 system.img 放到 /workspaces/system.img"
fi

echo "=== [3/6] 生成优化 kernel cmdline ==="
cat > "$OUT_DIR/kernel-command-line-optimized.txt" << 'EOF'
init=/init console=ttyS0 androidboot.hardware=cutf_cvm androidboot.fstab_suffix=uml androidboot.boot_devices=uml-blkdev.0,uml-blkdev.1 androidboot.selinux=enforcing androidboot.serialconsole=1 androidboot.console=hvc0 androidboot.hypervisor.vm.supported=0 androidboot.hypervisor.protected_vm.supported=0 androidboot.vendor.apex.com.android.hardware.graphics.composer=com.android.hardware.graphics.composer.drm_hwcomposer androidboot.hardware.gralloc=minigbm androidboot.hardware.hwcomposer=drm_hwcomposer androidboot.hardware.hwcomposer.display_finder_mode=drm androidboot.hardware.hwcomposer.display_framebuffer_format=rgba androidboot.hardware.egl=kernarium androidboot.hardware.vulkan=virtio androidboot.opengles.version=196610 androidboot.cpuvulkan.version=0 androidboot.hardware.guest_hwui_renderer=skiagl androidboot.hardware.guest_disable_renderer_preload=false androidboot.vendor.apex.com.google.emulated.camera.provider.hal=none androidboot.uml_bpf_interpreter=1 androidboot.setupwizard_mode=OPTIONAL androidboot.enable_bootanimation=0 androidboot.serialno=umlandroid17 androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked androidboot.flash.locked=0 printk.devkmsg=off audit=1 panic=-1 rcupdate.rcu_expedited=1 nohz_full=1-7 rcu_nocbs=1-7 8250.nr_uarts=4 loop.max_part=7 nbd.nbds_max=0 virtio_snd.pcm_period_ms_min=5 firmware_class.path=/vendor/etc/
EOF

echo "=== [4/6] 生成优化 build.prop 补丁 ==="
cat > "$OUT_DIR/build.prop.patch" << 'EOF'
# 追加到 system/product/system_ext/vendor 的 build.prop
# 启动优化
dalvik.vm.boot-dex2oat-threads=8
dalvik.vm.dex2oat-threads=8
dalvik.vm.image-dex2oat-filter=interpret-only
dalvik.vm.usejit=false
dalvik.vm.usejitprofiles=false
dalvik.vm.dex2oat-cpu-set=0,1,2,3,4,5,6,7

# GPU/图形优化
ro.hardware.egl=kernarium
ro.hardware.vulkan=virtio
ro.hardware.gralloc=minigbm
ro.hardware.hwcomposer=drm_hwcomposer
debug.egl.force_msaa=0
debug.hwui.renderer=skiagl
debug.hwui.use_gpu_pixel_buffers=true

# SurfaceFlinger 高刷/ProMotion
ro.surface_flinger.max_frame_buffer_acquired_buffers=3
ro.surface_flinger.use_content_detection_for_refresh_rate=true
ro.surface_flinger.set_idle_timer_ms=8
ro.surface_flinger.set_touch_timer_ms=200
ro.surface_flinger.set_display_power_timer_ms=300

# ART 优化
dalvik.vm.dex2oat-minidebuginfo=true
dalvik.vm.minidebuginfo=true
dalvik.vm.use-art-volume-optimization=true

# 内存管理
ro.config.low_ram=false
ro.config.max_starting_bg=8
ro.sys.fw.bg_apps_limit=32
EOF

echo "=== [5/6] 生成 IPA 重打包脚本 ==="
cat > "$OUT_DIR/repack_ipa.py" << 'PYEOF'
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
PYEOF

chmod +x "$OUT_DIR/repack_ipa.py"

echo "=== [6/6] 打包所有产物 ==="
cd /workspaces
tar -czf "$OUT_DIR/andarium-kernel-build-artifacts.tar.gz" -C "$OUT_DIR" .
echo "✅ 所有产物打包: $OUT_DIR/andarium-kernel-build-artifacts.tar.gz"

echo ""
echo "=== 🎉 全部完成 ==="
echo "产物目录: $OUT_DIR"
ls -lh "$OUT_DIR"