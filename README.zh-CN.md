# OccultationVisualiser

[English](README.md) | **简体中文**

将已有的掩星测光结果与观测星场同步，制作 GIF、MP4 和 PNG 预览。掩星指天体从恒星前方经过，使恒星短暂变暗。本软件负责可视化，不从录像重新测光，也不运行 PyOTE 拟合。已有导出文件后，无需安装 Tangra、PyMovie 或 PyOTE 即可制作。

原名 **OccultationMedia**。新构建使用 `OccultationVisualiser.app` / `OccultationVisualiser.exe` 和 `occultationvisualiser` 命令；旧 `occultation-media` 命令及 Python 导入名 `occultation_media` 保留兼容。GitHub 仓库已改名为 OccultationVisualiser；现有本地目录可以保留旧名称。

## GUI 快速开始（v1.5）

所有输入都可以在窗口内完成，无需手写 JSON。

1. 在主窗口填写共同的 **Event、小行星／目标星、UTC 日期、显示起止 UTC、显示间隔**及输出语言。跨午夜时，结束时间填写完整日期，例如 `2026-09-13T00:00:05`。
2. 选择或拖入输出文件夹。点击 **添加 Add** 新建 observer；双击列表或点击 **编辑 Edit** 修改，**删除 Delete** 移除。支持 1–8 位观测者，各站使用绝对 UTC。
3. 在 observer 窗口切换 **Tangra / PyMovie–PyOTE**，选择或拖入曲线、影像及可选的 PyOTE 结果。FITS 序列使用文件夹按钮或拖入整个文件夹。每个文件框一次接收一个文件／文件夹。
4. 每站填写姓名、曝光毫秒数、影像第 0 帧对应的原始帧号、可选 **Expected UTC**。PyMovie 目标列会从 CSV 中建议第一条 `signal-` 列；有多个目标时请核实。
5. **高级 Advanced** 可填写保存的 D/R、目标坐标、FITS HDU、SER 字节序、已知相机时差及核验容差。无需选择 start/middle/end。
6. 点击 **仅核验 Verify** 检查数据和原始 UTC，再点击 **生成 Generate**。在日志下方查看状态，使用 **打开输出** 查看 GIF、MP4、PNG 和时间核验记录。
7. **保存项目 Save / 打开项目 Open** 保留公共事件和所有 observer；不需要编辑保存的 JSON。运行时另存解析后的配置，以便复现。

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
