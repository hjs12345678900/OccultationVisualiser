# OccultationVisualiser

OccultationVisualiser 将已有的小行星掩星光变曲线与观测星场同步，制作视频、动图和预览图。支持 1–8 个观测站共用绝对 UTC 时间轴，左侧显示光变，右侧显示对应影像。

[下载最新版](https://github.com/hjs12345678900/OccultationVisualiser/releases/latest) · [English](README.md) · [详细配置说明](docs/native_station_media.md)

## 下载与启动

独立软件包包含运行环境、字体和视频编码器。打开软件并处理已导出的观测文件，无需安装 Python、Tangra、PyMovie 或 PyOTE。

| 平台 | 启动方式 |
| --- | --- |
| Windows 10/11 x64 | 完整解压 Windows ZIP，打开 `OccultationVisualiser.exe`；保留旁边的 `_internal` 文件夹。 |
| macOS 14+ | 解压 macOS ZIP，打开 `OccultationVisualiser.app`。当前构建面向 Intel，Apple Silicon 需要 Rosetta。 |

macOS 软件包未进行 Apple 公证。

## 准备文件

生成动画需要一条保存的光变曲线，以及与它对应的原始录像或图像序列。观测文件可以保留在原来的目录。

| 光变曲线 | 对应影像 |
| --- | --- |
| Tangra CSV | ADV2、SER、RAVF、带时标的 FITS 序列，或对应 Tangra LC 中的目标小图 |
| 带时间记录的 Tangra LC | 原始录像，或 LC 内嵌的目标小图 |
| PyMovie CSV | 原始 ADV2、SER、RAVF 或带时标的 FITS 序列 |
| 保存的 C3/C4 分析 CSV | 原始录像；缺少目标位置时可附原始跟踪 CSV |

Tangra CSV 使用目标 1；PyMovie 使用选定的 `signal-<目标名>` 列。LC 内嵌影像是记录的 35×35 目标裁剪图；需要完整星场时请选择原始录像。

普通 AVI/MP4 不作为观测输入，FITS 序列需要逐帧 UTC。兼容的 PyOTE 结果 JSON 可提供 D/R，具体结构见 [配置说明](docs/native_station_media.md)。

## 制作第一个视频

1. 填写小行星名称、目标星和 UTC 观测日期，选择输出文件夹。
2. 点击 **添加站点**，选择曲线和影像，核对自动建议的目标列。曝光从文件记录自动读取。
3. 选择下方的时间范围和播放方式。
4. 点击 **核验时间戳**，检查影像与曲线记录的时刻是否一致。
5. 点击 **生成动画**，完成后用 **打开结果文件夹** 查看 MP4、GIF 和 PNG 预览。

**保存项目 / 打开项目** 可复用输入。右上角 **中文 / English** 切换界面语言；**输出视频语言** 独立控制中文、英文或两种媒体版本。

### 时间范围与播放方式

| 设置 | 含义 |
| --- | --- |
| 完整录制范围 | 使用保存曲线的录制范围，无需填写起止 UTC 或提供 D/R。 |
| 消失/复现（D/R）周围 | 保留 D 前和 R 后指定秒数，默认各 10 秒；每站需要保存或输入的 D/R。 |
| 自选起止 UTC | 裁剪视频显示区间，例如 09:54:20–09:54:45 UTC。跨日时填写结束日期，如 `2026-09-13T00:00:10`。 |
| 跳过空档 | 略过保留的录制段或事件窗口之间的空档；时钟仍显示真实 UTC，横轴断点标出跳转。 |
| 按真实事件速度 | 按保留区间的真实时间尺度播放。 |
| 指定视频总时长 | 调整播放速度，使视频达到指定长度，例如 20 秒；原始 UTC 和 D/R 不变。 |

各站按绝对 UTC 同步；某站在当前时刻没有对应影像时显示空白。MP4 时长按 25 fps 取整，GIF 使用厘秒。

### 哪些输入可选

一个或多个站点都可不填坐标、海拔和预报。**北 → 南** 只排序已知位置，未知位置放在最后；使用坐标时同时提供纬度和经度。

完整录制视频不强制提供 PyOTE 结果。需要 D/R 时，也可在 **高级覆盖** 中直接输入。预报是单独的标签，不作为测得的事件边界。

第一帧对应字段是 **高级覆盖** 中的可选帧号映射，用于裁剪录像。默认按原始 UTC 匹配影像与曲线，它不决定视频显示的起始时刻。

曝光读取自 FITS/ADV/RAVF/LC、PyMovie 快门元数据或 CameraSettings。SER 时间戳提供帧间隔，不等于曝光；缺少曝光记录时，可选择 CameraSettings 或使用高级曝光覆盖。旧项目保留原先明确填写的覆盖值。

**曲线数据类型** 表示导入的已有数据：`raw` 是原始目标计数；支持的 `C3/C4` 导出曲线已使用对应参考星归一化。默认从保存结果读取模式，无结果则使用 raw。C3/C4 需要匹配的分析 CSV 和结果文件。本软件导入这些值，不重新测光、归一化或拟合。

## 噪声诊断

**噪声诊断** 只读取保存曲线，不解码影像。它分别显示保存的 SNR 与保护区基线 SNR，以及曝光、binning、相机来源和可用的背景/掩膜统计。

基线 SNR 为 `B/σB`，使用每次曝光的散布。诊断默认排除 D 前 1 秒至 R 后 1 秒，与视频裁剪秒数独立；缺少 D/R 时，已识别掩食外基线的统计显示不可用。

可选择两站比较共同绝对 UTC 的基线。没有共同录制时段时显示无法比较。像素背景预算是近似估计，不能分离探测器读出噪声；指标定义和假设保存在 `quality_report.json`。

## 输出与排错

每次运行创建新的结果目录。动画任务输出 MP4、GIF 和 PNG 预览；配置任务还保存 `resolved_config.json`、`media_metadata.json`、`run_metadata.json`、代码快照、输入哈希及诊断报告。桌面任务保留 `run.log` 和 `result.json`，结果位于 `media` 子目录。

| 问题 | 检查内容 |
| --- | --- |
| 未找到曝光 | 原始影像头部、对应 CameraSettings 或高级覆盖 |
| UTC 不一致 | 观测日期、曝光开始/中点约定、已经应用的相机时差 |
| PyOTE 模式不匹配 | 对应的分析曲线及兼容结果 JSON |
| 某站画面空白 | 录制覆盖范围和时间核验记录 |
| 目标标记位置不对 | 目标列、原始跟踪 CSV 或高级目标 X/Y |
| 生成失败 | 该任务的 `run.log` 和失败元数据 |

完整时标约定、来源格式和结果文件要求见 [详细配置说明](docs/native_station_media.md)。

## 从源码运行

使用带 Tk 的 Python 3.13，在项目目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python launch.py
```

Windows 前两步改为 `py -3.13 -m venv .venv` 和 `.venv\Scripts\activate`。可用 `python -m tkinter` 检查 Tk。

使用保存的站点配置：

```bash
occultationvisualiser --media-config project.json
occultationvisualiser --media-config project.json --verify-only
occultationvisualiser --media-config project.json --quality-only
```

## 开发

```bash
python -m unittest discover -s tests -v
python launch.py --self-test
python -m pip install -e ".[build]"
```

在目标平台运行 `Build-Windows.bat` 或 `Build-Mac.command`。版本标签通过 GitHub Actions 构建 Windows/macOS 包并执行独立应用自测。压缩包附带中英文说明、示例配置及视觉素材。

版本记录见 [CHANGELOG.md](CHANGELOG.md)，依赖许可证见 [THIRD_PARTY.md](THIRD_PARTY.md)。旧 `occultation-media` 命令和 Python 导入名 `occultation_media` 保留兼容。
