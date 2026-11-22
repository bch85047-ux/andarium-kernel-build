#!/usr/bin/env python3
"""注入性能优化配置到 build.prop / init.rc"""
import glob, os

OPT_BLOCK = """
# ==== Andarium performance tweaks (injected by build pipeline) ====
# ART: AOT 优先，禁用 JIT（对齐 twoyi 的 AOT 理念）
dalvik.vm.boot-dex2oat-threads=8
dalvik.vm.dex2oat-threads=8
dalvik.vm.image-dex2oat-filter=interpret-only
dalvik.vm.usejit=false
dalvik.vm.usejitprofiles=false
dalvik.vm.dex2oat-cpu-set=0,1,2,3,4,5,6,7
dalvik.vm.dex2oat-minidebuginfo=true
dalvik.vm.minidebuginfo=true
dalvik.vm.use-art-volume-optimization=true
dalvik.vm.heapsize=512m
dalvik.vm.heapgrowthlimit=512m
dalvik.vm.heapminfree=8m
dalvik.vm.heapmaxfree=32m

# 图形: 强制 GPU 硬件加速路径
ro.hardware.egl=kernarium
ro.hardware.vulkan=virtio
ro.hardware.gralloc=minigbm
ro.hardware.hwcomposer=drm_hwcomposer
debug.egl.force_msaa=0
debug.hwui.renderer=skiagl
debug.hwui.use_gpu_pixel_buffers=true
debug.sf.enable_hwc_vds=1
ro.opengles.version=196610
ro.hardware.guest_hwui_renderer=skiagl
ro.hardware.guest_disable_renderer_preload=false

# SurfaceFlinger: 高刷新率 / ProMotion / 流畅度
ro.surface_flinger.max_frame_buffer_acquired_buffers=3
ro.surface_flinger.use_content_detection_for_refresh_rate=true
ro.surface_flinger.set_idle_timer_ms=8
ro.surface_flinger.set_touch_timer_ms=200
ro.surface_flinger.set_display_power_timer_ms=300
ro.surface_flinger.enable_frame_rate_override=false

# 内存管理: 减少 LMK 杀后台，提升多任务流畅度
ro.config.low_ram=false
ro.config.max_starting_bg=8
ro.sys.fw.bg_apps_limit=32
ro.lmk.critical_upgrade=2000
ro.lmk.swap_available_low=1

# 调度: 性能优先而非省电
ro.sched.low_power_mark=0
"""

INIT_RC_BLOCK = """
# Andarium perf tweaks
on property:sys.boot_completed=1
    setprop sys.bootstat.first_boot_completed 1
    setprop dalvik.vm.dex2oat-threads 8
"""


def main():
    count = 0
    props = glob.glob('/mnt/erofs/**/build.prop', recursive=True)
    print(f'找到 {len(props)} 个 build.prop')
    for path in props:
        try:
            with open(path, 'a') as f:
                f.write(OPT_BLOCK)
            print(f'  ✅ {path}')
            count += 1
        except Exception as e:
            print(f'  ⚠️ {path}: {e}')

    # init.rc / init.environ.rc
    rcs = glob.glob('/mnt/erofs/**/init*.rc', recursive=True)
    print(f'\n找到 {len(rcs)} 个 init rc')
    for path in rcs:
        try:
            with open(path, 'a') as f:
                f.write(INIT_RC_BLOCK)
            print(f'  ✅ {path}')
            count += 1
        except Exception as e:
            print(f'  ⚠️ {path}: {e}')

    print(f'\n✅ 共修改 {count} 个文件')

    if count == 0:
        raise SystemExit('❌ 未找到任何可修改的配置文件')


if __name__ == '__main__':
    main()
