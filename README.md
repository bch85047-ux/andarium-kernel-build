# Andarium Kernel Build - GitHub Actions 自动化构建

## 一键构建
1. 仓库 Actions 页面 → **Andarium Kernel Build** → **Run workflow**
2. 选项: `compress_system_img=true`, `build_ipa=true`
3. 等 ~30 分钟，下载 Artifacts:
   - `uml-kernel-optimized` - 优化 UML 内核
   - `system-img-compressed` - lz4hc 压缩镜像
   - `andarium-optimized-ipa` - 最终优化 IPA

## 优化内容
- 内核: PREEMPT_VOLUNTARY, HZ=250, NO_HZ_FULL, erofs lz4hc/zstd 支持
- 镜像: system/vendor 分区 lz4hc 压缩 (IPA 1013MB → ~300MB)
- cmdline: 仅追加 nohz_full/rcu_nocbs，原版参数 100% 保留

## Release 资产
- `v1.0-system-img` 标签下有 system.img (21 分块) 和原版 IPA (22 分块)

v2
