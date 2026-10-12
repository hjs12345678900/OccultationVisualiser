# OccultationVisualiser

[English](README.md) | **简体中文**

![OccultationVisualiser 软件封面](src/occultation_media/assets/branding/cover.png)

启动封面在 1.2 秒后自动关闭，也可点击或按 Escape 关闭；主窗口“封面 / 关于”可重新查看。配套图标已接入原生应用包。图案是概念品牌插画，不是实测光变。[素材生成提示词](src/occultation_media/assets/branding/prompts.json) 已保存，发布压缩包也附带 `branding` 文件夹。

将已有的掩星测光结果与观测星场同步，制作 GIF、MP4 和 PNG 预览。掩星指天体从恒星前方经过，使恒星短暂变暗。本软件负责可视化，不从录像重新测光，也不运行 PyOTE 拟合。已有导出文件后，无需安装 Tangra、PyMovie 或 PyOTE 即可制作。

原名 **OccultationMedia**。新构建使用 `OccultationVisualiser.app` / `OccultationVisualiser.exe` 和 `occultationvisualiser` 命令；旧 `occultation-media` 命令及 Python 导入名 `occultation_media` 保留兼容。GitHub 仓库已改名为 OccultationVisualiser；现有本地目录可以保留旧名称。

## GUI 快速开始（v1.9）

右上角的 **中文 / English** 切换界面语言；视频输出语言独立设置。切换语言会保留已填参数和正在运行的任务。

1. 填写小行星、目标星、UTC 日期，选择输出文件夹。带 * 的项目必填。
2. 添加站点，选择光变 CSV/LC，生成动画时再选择原始影像。软件自动识别曲线来源、建议目标列并读取曝光；PyOTE 结果 JSON 可留空。
3. 默认 **完整录制范围**，无需填写起止时刻或 D/R。**消失/复现（D/R）周围** 使用保存或输入的事件边界，前后秒数可调。**自选起止 UTC** 只裁剪视频显示区间，例如 09:54:20 至 09:54:45；跨日填写完整日期。它不改变原始帧号或测得的 D/R。
4. 位置和预报放在可选页签。一个或多个站点都可不填坐标。北→南排序只排列已知位置，未知位置保留添加顺序并放在最后。
5. 选择跳过/保留录制空档，以及真实速度/指定视频总时长。跳过空档仍保留绝对 UTC，并显示横轴断点；指定时长只改变播放速度。
6. **核验时间戳** 检查原始帧时刻；**生成动画** 输出 GIF、MP4、PNG。**噪声诊断** 只读曲线并输出 JSON/CSV，支持两站共同 UTC 对照。识别基线需要 D/R；缺少 D/R 时该统计显示不可用，不会补造边界。
7. 保存/打开项目可复用设置；查看诊断可打开已有 `quality_report.json`。每次运行记录配置、输入哈希和代码来源。

| 输入 | 什么时候需要 |
| --- | --- |
| 原始影像 | 生成动画或核验；仅做曲线诊断时可留空 |
| 坐标、海拔、预报 | 可选，用于标签和排序，不影响 UTC 核验 |
| PyOTE 结果或 D/R | D/R 裁剪和掩食外基线统计需要；完整录制视频不强制提供 |
| 曝光 | 自动读取 FITS/ADV/RAVF/LC、PyMovie 快门头部或 CameraSettings；文件缺失记录时才在高级设置覆盖 |
| 第一帧的帧号对应 | 默认按 UTC 自动匹配；裁剪录像需要覆盖时才使用高级字段 |
| 原始跟踪 CSV | 归一化曲线缺少目标位置时可提供 |

**曝光不等于帧间隔。** SER 时间戳只有帧间隔，软件会读取拍摄设置，不用它推测曝光。旧项目保留原先明确填写的曝光和帧号覆盖，并在编辑器显示手动覆盖状态；缺少曝光记录会明确提示。

**曲线数据类型** 描述导入的已有数据。`raw` 是原始目标计数；我们归约流程里的 `C3/C4` 表示使用对应参考星归一化后导出的光变，不是三个拟合算法。默认从结果读取模式，无结果则使用 raw。C3/C4 必须配套对应的分析 CSV 和结果文件，本应用不执行归一化或重新拟合。

站点标签显示基线单曝光 SNR（`B/σB`），优先保存的 PyOTE 参数；缺失时直接从完整掩食外曝光计数计算。诊断将保存 SNR 与保护区基线 SNR 分开展示，默认排除 D 前 1 秒至 R 后 1 秒，与视频的 10 秒裁剪设置独立。两站比较保留共同绝对 UTC，并排除双方事件；没有共同录制时段就显示无法比较。线性残差和相邻差分仅为诊断，不替换曲线或 SNR。PyMovie 的 `σpixel×√Nmask` 背景预算假设像素独立且背景有代表性，不能隔离读出噪声，未计源泊松噪声和背景估计误差；C3/C4 禁用原始像素预算。详见 [定义及配置](docs/native_station_media.md)。

命令行：`occultationvisualiser --media-config project.json --quality-only`；`diagnostic_margin_s` 可调整保护区。曲线诊断不核验影像时间戳，该检查使用“核验时间戳”。

### 时间戳约定

GUI 按当前 SharpCap 的约定：SER 和 FITS `DATE-OBS` 为曝光开始，显示时间加半曝光；`DATE-AVG` 和 ADV 为曝光中点，RAVF 使用原生曝光开始。PyMovie 曲线沿用影像源的约定；Tangra CSV 使用导出的曝光中点。保存的 PyOTE D/R 不再加半曝光。

这套约定显示在窗口，并写入运行配置；原始影像与曲线仍须通过 UTC 核验。旧版 SharpCap、外部重新定时或已转换过时间的 CSV 可能不适用，核验失败时须检查来源，不应任意放宽容差。[SharpCap 作者说明](https://forums.sharpcap.co.uk/viewtopic.php?t=9540)。

### 文件清单

| 流程 | 文件 |
| --- | --- |
| Tangra 全场 | 测光 CSV（目标 1）或带时标 LC + ADV2/SER/RAVF/带 UTC 的 FITS 序列 |
| Tangra 小图 | CSV 或 LC 曲线 + 对应 LC 影像；仅为 35×35 目标裁剪图 |
| PyMovie | CSV + 原始影像；可选原始跟踪 CSV |
| PyOTE 区间 | 额外提供兼容的结果 JSON，或在高级设置填写 D 与 R UTC |

普通 AVI/MP4 不是输入格式。截图、报告、CSV 本身不能提供星场。严格时标模式不支持无逐帧 UTC 的 FITS cube。

## 2. 启动软件

已有安装包见 [Releases](https://github.com/hjs12345678900/OccultationVisualiser/releases)。旧版仍使用旧软件名；本次源码改名不会改变已经下载的安装包。

- **Windows 10/11 x64**：完整解压 ZIP，打开 `OccultationVisualiser.exe`，保留旁边的 `_internal` 文件夹。
- **macOS 14+**：解压并打开 `OccultationVisualiser.app`。当前构建面向 Intel，Apple Silicon 需要 Rosetta。安装包未签名／公证。

从源码运行：使用带 Tk 的 Python 3.13，在**项目目录**打开终端：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python launch.py
```

Windows 将前两行换成 `py -3.13 -m venv .venv` 和 `.venv\Scripts\activate`。可用 `python -m tkinter` 检查 Tk。安装依赖包含 FFmpeg，项目附带字体。观测文件可以保留在自己的事件目录，无需复制到代码仓库。

### PyOTE 结果文件的具体要求

当前读取的是我们归约流程保存的原生结果 JSON 结构，**并非任意 PyOTE 报告、XLSX、日志或截图**。通常命名 `native_results.json`，文件名可以更改。必需字段：`timesAreValid: true`、`Dframe`、`Rframe`、`Dtime`、`Rtime`。`mode` 默认 `raw`，须与配置的 `native_mode` 一致。D/R 指消失／复现；时间是从 UTC 零点起的数值秒，帧号必须对应同一条曲线。可选 `xlsxDict.Derr95/Rerr95` 保留在来源记录中。两边界须在曲线内部并与对应帧时间一致，不要根据猜测拼装结果文件。

若只有可靠的观测报告时刻，可省略 `pyote_result`，同时提供完整 UTC ISO 格式的 `D_utc` 和 `R_utc`，可附 `timing_source_file` 记录来源。软件不会重新拟合或再次对 D/R 加半曝光修正。此叠加功能不支持仅 D 或仅 R。

C3/C4：`curve` 指向保存的 `native_analysis.csv`，设置匹配的 `native_mode` 和结果 JSON。如果缺失坐标，`tracking_csv` 指向原始 `pymovie_native.csv`。坐标列为 `xcentroid-<目标名>`、`ycentroid-<目标名>`，可选缺陷列 `hit-defect-<目标名>`；跟踪文件的帧号／UTC 必须与分析曲线逐点一致。本软件不执行归一化或去趋势。

完整字段、Tangra JSON 输入、相机延迟、SER 字节序及部分 FITS 覆盖见 [配置与 UTC 约定](docs/native_station_media.md)。

## 5. 输出与排错

每次生成新的结果目录，按语言输出 GIF、PNG 预览及 MP4（Tangra 表单可关闭 MP4）。配置模式还保存阶段拼图、解析后配置、代码快照、输入哈希及 `media_metadata.json` / `run_metadata.json` 时间核验记录。`--verify-only` 只写核验产品，不生成动画。桌面任务保留 `run.log`、`result.json`；配置模式媒体在其 `media` 子目录。

| 问题 | 检查 |
| --- | --- |
| 文件不存在 | 模板路径是否全部替换；相对路径以 JSON 目录为基准 |
| 缺列／找不到表头 | 使用原始支持格式的导出 CSV，核对目标列名，避免表格软件改写格式 |
| 帧号／UTC 不一致 | 第一采样日期、曝光单位、开始／中点／结束约定、帧映射和已知相机延迟 |
| SER/FITS 没有时间戳 | 提供原始带时标文件；严格模式不会编造时间 |
| PyOTE 时刻无效／模式不符 | 使用匹配结果，或删除 `pyote_result` |
| 某站图像空白 | 录像可能未覆盖显示 UTC，查看时间核验记录 |
| 标记位置不对 | 修改 Tangra X Y，或提供匹配的原生跟踪列 |
| 生成失败 | 先查看 `run.log` 和失败元数据，再重试 |

产品用于观测可视化。记录时钟相互一致不等于独立验证了时钟准确度，也不代替正式掩星定时。

## 开发与打包

```bash
python -m unittest discover -s tests -v
python launch.py --self-test
python -m pip install -e ".[build]"
```

`Build-Windows.bat` / `Build-Mac.command` 会测试并打包。仅打包可使用 Windows 的 `python package_windows_only.py`，或 Mac 的 `python -m PyInstaller --noconfirm --clean OccultationVisualiser.spec`。发布压缩包在应用旁附带中英文说明和可编辑 JSON 模板。GitHub Actions 支持手动构建和版本标签。许可证见 [THIRD_PARTY.md](THIRD_PARTY.md)。
