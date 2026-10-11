# OccultationVisualiser

[English](README.md) | **简体中文**

将已有的掩星测光结果与观测星场同步，制作 GIF、MP4 和 PNG 预览。掩星指天体从恒星前方经过，使恒星短暂变暗。本软件负责可视化，不从录像重新测光，也不运行 PyOTE 拟合。已有导出文件后，无需安装 Tangra、PyMovie 或 PyOTE 即可制作。

原名 **OccultationMedia**。新构建使用 `OccultationVisualiser.app` / `OccultationVisualiser.exe` 和 `occultationvisualiser` 命令；旧 `occultation-media` 命令及 Python 导入名 `occultation_media` 保留兼容。GitHub 仓库已改名为 OccultationVisualiser；现有本地目录可以保留旧名称。

## 1. 需要准备什么？

| 已有结果 | 必需文件 | 使用入口 |
| --- | --- | --- |
| Tangra，全星场 | 测光 CSV + 对应的 ADV2 / SER / RAVF 原始录像或 FITS 图像 | 主窗口表单 |
| Tangra，仅目标小图 | 测光 CSV + 含目标图像的对应 `.lc` 文件 | 主表单，观测文件选择 `.lc` |
| PyMovie，单站 | 原始导出 CSV + 对应录像或带 UTC 的 FITS 序列 + 配置 JSON | **PyMovie / 四站配置…** |
| PyMovie + PyOTE 拟合 | 上述文件 + 符合下述字段约定的 `native_results.json`（可选） | 同一配置入口 |
| 四站联合展示 | 每站各自的曲线和图像源 + 列出四站的 JSON | 同一配置入口 |

**只有曲线截图、PyOTE 报告、CSV 或录像快捷方式，不能生成真实星场动画。** 当前不支持 AVI/MP4 输入；MP4 是输出格式。Tangra `.lc` 内嵌图像只有 35×35 的目标裁剪图，不能还原全星场。配置模式目前只接受 **1 或 4 站**，不接受 2、3 站。

另外准备：曲线第一个采样点的 UTC 日期、小行星／事件和目标星名称、实际曝光时长、时间戳代表曝光开始／中点／结束，以及原始录像与 CSV 的帧号对应关系。**表单曝光单位是毫秒，JSON `exposure_s` 单位是秒。** Tangra 表单的预报时刻和误差可留空。

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

## 3. Tangra：第一次制作

1. 在 Tangra 保存 `.lc` 并导出包含帧号、UTC、信号和背景的测光 CSV。软件绘制**目标 1**，需要 `FrameNo`、`Time (UT)`、`Signal (1)`、`Background (1)` 列，计算信号减背景。
2. **观测文件**选择原始录像；只要目标裁剪图则选 `.lc`。FITS 序列点击 **FITS 文件夹…**。选择对应 CSV 和输出目录。
3. 填写名称、UTC 日期及曝光毫秒数；没有预报则留空。
4. 核实**源第 0 帧对应的 CSV 帧号**。例如录像第一张图对应 CSV 第 1500 帧，就填 1500，不要默认填 0。LC 裁剪图使用内嵌帧号。
5. 目标 X Y 默认从 CSV 读取，也可手填以 0 为起点的像素坐标。主表单的标记位置不会逐帧跟踪。选择输出语言，点击**生成动画**。
6. 打开输出目录，先看 PNG，再播放 GIF/MP4，检查目标位置及曲线和星场变暗是否同步。自动低光区间只是展示估计；必要时手填首末低光通量帧号。

主表单按帧号对齐，不进行下面配置模式的原生 UTC 严格核验。主表单支持 FITS cube；严格模式需要每张图有独立 UTC。整段动画采用固定亮度拉伸，避免自动调亮掩盖恒星变暗。

## 4. PyMovie / PyOTE：编辑配置、核验、制作

将 [native_single.json](examples/native_single.json) 复制到事件目录，用文本编辑器修改。它是模板，不附带可直接运行的观测数据。

1. 将 `curve`、`source` 改成真实 CSV 和图像源路径。相对路径（包括 `output_root`）以 JSON 所在目录为基准。
2. `target_column` 填 CSV 的真实列名，例如 `signal-target`。需要 `FrameNum`、`timeInfo` 和目标信号列，表头以 `FrameNum,` 开始。读取保存的净计数，不再次减背景。至少三个采样，帧号和 UTC 严格递增；不支持小数／积分帧号。
3. 修改 `date_utc`、`start_utc`、`end_utc`、`exposure_s`、适用的时间戳约定及 `source_first_frame`。全部使用 UTC。`step_s >= 0.01`，显示帧数为 2–2,000；显示抽样不改变原曲线。
4. 按导出精度设置 `mapping_tolerance_s`。示例的 1 ns 并非通用值。SER 必须有原生时间戳尾部，FITS 必须逐图带 UTC；不要通过任意放大容差掩盖时间差。
5. **没有 PyOTE 结果时删除模板的 `pyote_result` 字段**，仍可制作曲线与星场，只是不显示 D/R 区间。
6. 替换下面路径，先核验，再制作：

```bash
python launch.py --media-config "/path/to/event/media.json" --verify-only
python launch.py --media-config "/path/to/event/media.json"
```

也可在界面点击 **PyMovie / 四站配置…**，选择编辑好的 JSON，再选择输出目录。这个入口使用 JSON 参数，与 Tangra 表单独立。四站从 [four_stations.json](examples/four_stations.json) 修改；各站共用绝对 UTC，缺少覆盖的图像留空。

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
