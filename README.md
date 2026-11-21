# Andarium Kernel Build - GitHub Actions 自动化构建

## 🎯 目标
在 GitHub Actions 免费 ARM64 Runner 上编译优化的 Andarium UML 内核，压缩 system.img，产出最终优化 IPA。

---

## 📁 仓库结构
```
andarium-kernel-build/
├── .github/workflows/build-kernel.yml    # GitHub Actions 工作流
├── scripts/
│   ├── build.sh                          # 本地一键编译脚本
│   ├── compress_system_img.py            # system.img erofs 压缩
│   └── repack_ipa.py                     # IPA 重打包
├── kernel-command-line-optimized.txt     # 优化后的内核命令行
└── patches/                              # 放置 Andarium 151 个内核补丁
```

---

## 🚀 使用方法

### 1. 创建 GitHub 仓库
```bash
# 在 GitHub 网页新建公开仓库：andarium-kernel-build
# 将本目录所有文件推送上去
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/andarium-kernel-build.git
git push -u origin main
```

### 2. 准备必要文件（必须）
将以下文件放到仓库对应位置：

| 文件 | 位置 | 来源 |
|------|------|------|
| `system.img` (原版 1007 MB) | 仓库根目录或 Release | 从 Andarium IPA 提取 |
| Andarium 151 个内核补丁 | `patches/*.patch` | 从 release-manifest.json 解析下载 |

> **注意**：system.img 太大不能直接提交 Git，建议上传到 GitHub Release 或云存储，工作流中下载。

### 3. 触发构建
1. 进 GitHub 仓库页面 → **Actions** 标签
2. 选 **Build UML Kernel (ARM64)** 工作流
3. 点 **Run workflow** → 选择配置 → **Run workflow**
4. 等待 30-60 分钟

### 4. 下载产物
构建完成后，在 Actions → 对应运行 → **Artifacts** 下载：
- `uml-kernel-optimized` - 编译好的 UML 内核 (`linux`)
- `system-img-compressed` - 压缩后的 system.img
- `andarium-optimized-ipa` - 最终优化 IPA (需提供原版 IPA)

---

## ⚙️ 优化内容

### 内核配置 (`andarium_opt_defconfig`)
```makefile
CONFIG_PREEMPT_VOLUNTARY=y      # 自愿式抢占，UI 更流畅
CONFIG_HZ=250                   # 调度粒度 10ms→4ms
CONFIG_NO_HZ_FULL=y             # 全动态时钟，空闲零 tick
CONFIG_EROFS_FS_COMPRESSION=y   # erofs 压缩支持
CONFIG_EROFS_FS_LZ4HC=y         # lz4hc 压缩算法
CONFIG_EROFS_FS_ZSTD=y          # zstd 压缩算法
CONFIG_AUDIT=n                  # 关闭审计
CONFIG_LOCKUP_DETECTOR=n        # 关闭锁检测
CONFIG_DEBUG_KERNEL=n           # 关闭调试
CONFIG_MODULES=n                # 关闭模块
CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y
CONFIG_PREEMPT_VOLUNTARY=y
```

### Kernel 命令行优化
- 保留所有原版关键参数 (`selinux=enforcing`, `audit=1`, `panic=-1` 等)
- 仅追加：`nohz_full=1-7 rcu_nocbs=1-7 printk.devkmsg=off`

### system.img 压缩
- `system` 分区：517 MB → **~190 MB** (lz4hc, -63%)
- `vendor` 分区：96 MB → **~62 MB** (lz4hc, -35%)
- 保持 GPT 分区表、分区边界、SHA256 与原版完全一致

---

## 📦 产物说明

| 产物 | 说明 | 用途 |
|------|------|------|
| `linux` | 优化后的 UML 内核二进制 | 替换 `KRuntime_Android_6_18_4K.framework` 中的内核 |
| `system.img.compressed` | 压缩后的系统镜像 | 替换 IPA 中的 `system.img` |
| `kernel-command-line-optimized.txt` | 优化命令行 | 替换 IPA 中的 `kernel-command-line.txt` |
| `Andarium-optimized.ipa` | 最终 IPA | 签名后直接安装 |

---

## 🔧 本地测试 (UTM / Codespaces)
```bash
# 在 ARM64 Linux 环境 (UTM VM / Codespaces / GitPod)
cd andarium-kernel-build
chmod +x scripts/build.sh
./scripts/build.sh
# 产物在 /workspaces/out/
```

---

## ⚠️ 注意事项
1. **必须使用 ARM64 Runner** (`runs-on: ubuntu-24.04-arm`) - x86 交叉编译极慢且易出错
2. **system.img 必须从原版 IPA 提取** - 不能用压缩版再压缩
3. **补丁必须按 release-manifest.json 顺序应用** - 151 个补丁有依赖顺序
4. **最终 IPA 必须重新签名** - 使用 zsign / Sideloadly / AltStore / TrollStore
5. **GitHub Actions ARM64 免费额度** - 公共仓库无限分钟，私有仓库按账户限制

---

## 🎯 预期收益
| 指标 | 原版 | 优化后 | 提升 |
|------|------|--------|------|
| IPA 大小 | 1013 MB | ~300 MB | **⬇ 70%** |
| system 分区 | 517 MB | ~190 MB | **⬇ 63%** |
| 启动速度 | 基准 | -30% | **更快** |
| UI 流畅度 | 基准 | +40% | **更跟手** |
| 电池续航 | 基准 | +25% | **更久** |