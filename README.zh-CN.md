# OccultationVisualiser

OccultationVisualiser 将已有的小行星掩星光变曲线与观测星场同步，制作视频、动图和预览图。支持 1–8 个观测站共用绝对 UTC 时间轴，左侧显示光变，右侧显示对应影像。

[下载最新版](https://github.com/hjs12345678900/OccultationVisualiser/releases/latest) · [English](README.md) · [详细配置说明](docs/native_station_media.md)

## 下载与启动

独立软件包包含运行环境、字体和视频编码器。打开软件并处理已导出的观测文件，无需安装 Python、Tangra、PyMovie 或 PyOTE。

| 平台 | 启动方式 |
| --- | --- |
| Windows 10/11 x64 | 完整解压 Windows ZIP，打开 `OccultationVisualiser.exe`；保留旁边的 `_internal` 文件夹。 |
| macOS 14+，Apple Silicon（M 系列） | 下载 `OccultationVisualiser-macOS-Apple-Silicon.zip`，解压后打开 `OccultationVisualiser.app`。原生运行，无需 Rosetta。 |
| macOS 14+，Intel | 下载 `OccultationVisualiser-macOS-Intel.zip`，解压后打开 `OccultationVisualiser.app`。 |

macOS 软件包未进行 Apple 公证。

## 准备文件

生成动画需要一条保存的光变曲线，以及与它对应的原始录像或图像序列。观测文件可以保留在原来的目录。

| 光变曲线 | 对应影像 |
| --- | --- |
| Tangra CSV | AVI（显式帧号对应）、ADV2、SER、RAVF、带时标的 FITS 序列，或对应 Tangra LC 中的目标小图 |
| 带时间记录的 Tangra LC | 原始录像，或 LC 内嵌的目标小图 |
| PyMovie CSV 或原生 `.pymovie` v1 | AVI（显式帧号对应）、原始 ADV2、SER、RAVF 或带时标的 FITS 序列 |
| 保存的 C3/C4 分析 CSV | 原始录像；缺少目标位置时可附原始跟踪 CSV |

Tangra CSV 使用目标 1；PyMovie 使用选定的 `signal-<目标名>` 列。LC 内嵌影像是记录的 35×35 目标裁剪图；需要完整星场时请选择原始录像。

AVI 已支持包内 FFmpeg 解码：高级设置须填写 AVI 第 0 帧对应的曲线帧号，文件页须选择曲线时标基准。容器 FPS 不用于推断绝对 UTC 或曝光。录像须保持原始帧顺序；重排、合帧或删除中间帧后的副本不支持。AVI 使用曲线 UTC，结果明确标注无法独立核验源时标。MP4 输入仍不支持。FITS 序列需要逐帧 UTC。PyOTE 的 `fit_metrics.txt` 或 `<名称>.pyote_log.txt` 放在 **PyOTE 原生结果 TXT** 栏；原始 PyMovie CSV 或处理后的 `<名称>.pyote.csv` 放在 **光变曲线** 栏。无需生成 JSON 或改扩展名。软件直接导入保存的 D/R 和 `B/σB`，不重新拟合；日志还保留记录的合并读数和 95% 时间误差。同一目标/曲线存在多个结果时，在高级设置填写 **PyOTE 拟合记录** 序号（从 1 开始）。旧版适配 JSON 继续支持，见 [配置说明](docs/native_station_media.md)。

## 影像亮度与原生 PyMovie 文件

站点编辑器新增 **影像亮度** 页，仅改变显示。自动 AVI 用首个显示帧上方
85% 星场的 0.5/99.99 百分位估计固定黑白点，避免底部时间字幕压暗星场；
完整画面仍保留。其它来源保留全画面自动方式。可选旧版全画面自动，或手动
设置解码像素黑白点及强度（0 为线性，默认 8）。光变和 D/R 不变。

二进制 `.pymovie` 测光文件（原生格式 v1）放 **光变曲线** 栏，对应原始
AVI/SER 等放 **原始影像** 栏。读取保存的净信号、帧号和 UTC，不把二进制当
CSV 文本。目标列为 `signal-<孔径名>`。文件头位置是初始静态位置；目标移动时
附对应原始跟踪 CSV。该格式没有曝光字段，仍需其它记录或明确覆盖。
半帧场模式目前会给出不支持的明确提示。

选影像时使用保存曲线的采样间隔作为保守的显示支持范围，曝光另行保留；
处理后的曲线不会因采样间隔大于单帧曝光而变空白。影像标注实际帧号和 UTC，
录制范围外和长空档仍为空。完全没选中影像时给出 UTC/帧号对应检查提示。

## 制作第一个视频

1. 点击 **导入／粘贴预测元素…**，选择 `.occelmnt`/XML 文件或粘贴一个完整事件 XML，点击 **核对并导入**。小行星名称、目标星和 UTC 日期自动填写，仍可编辑；也可以手动填写。选择输出文件夹。
2. 点击 **添加站点**，选择曲线和影像，核对自动建议的目标列。曝光从文件记录自动读取。
3. 选择下方的时间范围和播放方式。
4. 点击 **核验时间戳**，检查影像与曲线记录的时刻是否一致。
5. 点击 **生成动画**，完成后用 **打开结果文件夹** 查看 MP4、GIF 和 PNG 预览。

若日志显示 **0 mapped real images**，请比较日志或 `media/alignment_report.json` 中的**曲线 UTC**与**原始影像 UTC**。只有时分秒的 CSV 使用界面的**观测 UTC 日期**补全首个样本日期；应填录像实际 UTC 日期，而不是制作动画当天。文件名只能作为线索，请以录像内部 UTC 记录核实。所有站点均无匹配影像时，核验和生成都会明确失败。请修正日期或选择对应的曲线与录像；程序不会自动移动日期。AVI 没有独立 UTC，仍需明确填写帧号对应。

每个站点可独立填写 **观测者（可选） / Observer**，位于站点名称下方。填写后会显示在对应光变图上方，并保存到项目、导出配置和结果元数据；留空则不显示。观测者姓名不影响路径排序和地图标签。

每个站点还有 **站点颜色（留空自动）**：点击 **选择颜色…**，或填写 `#RRGGBB`；留空自动分配，点击 **自动** 可清除手动选择。颜色随站点排序，统一用于光变、影像标签/边框及地图标记/图例，并保存在项目中。

**保存项目 / 打开项目** 可复用输入。右上角 **中文 / English** 切换界面语言；**输出视频语言** 独立控制中文、英文或两种媒体版本。

### 时间范围与播放方式

| 设置 | 含义 |
| --- | --- |
| 完整录制范围 | 使用保存曲线的录制范围，无需填写起止 UTC 或提供 D/R。 |
| 消失/复现（D/R）周围 | 保留 D 前和 R 后指定秒数，默认各 5 秒（新项目默认范围）；每站需要保存或输入的 D/R。 |
| 自选起止 UTC | 裁剪视频显示区间，例如 09:54:20–09:54:45 UTC。跨日时填写结束日期，如 `2026-09-13T00:00:10`。 |
| 加速空档 | 默认以 50 倍连续播放空档中的阴影移动；D/R 窗口按正常速度播放，加速倍数可调整。时间轴用阴影带、双斜线和倍数标签标出压缩空档。 |
| 跳过空档 | 略过保留的录制段或事件窗口之间的空档；时钟仍显示真实 UTC，横轴断点标出跳转。 |
| 按真实事件速度 | 按保留区间的真实时间尺度播放。 |
| 指定视频总时长 | 调整播放速度，使视频达到指定长度，例如 20 秒；原始 UTC 和 D/R 不变。 |

各站按绝对 UTC 同步；某站在当前时刻没有对应影像时显示空白。MP4 时长按 25 fps 取整，GIF 使用厘秒。

### 哪些输入可选

一个或多个站点都可不填坐标、海拔和预报。**北 → 南** 只排序已知位置，未知位置放在最后；使用坐标时同时提供纬度和经度。

完整录制视频不强制提供 PyOTE 结果。需要 D/R 时，也可在 **高级覆盖** 中直接输入。预报是单独的标签，不作为测得的事件边界。

第一帧对应字段是 **高级覆盖** 中的可选帧号映射，用于裁剪录像。默认按原始 UTC 匹配影像与曲线，它不决定视频显示的起始时刻。

曝光读取自 FITS/ADV/RAVF/LC、PyMovie 快门元数据或 CameraSettings。SER 时间戳提供帧间隔，不等于曝光；缺少曝光记录时，可选择 CameraSettings 或使用高级曝光覆盖。旧项目保留原先明确填写的覆盖值。

**曲线数据类型** 表示导入的已有数据：`raw` 是原始目标计数；支持的 `C3/C4` 导出曲线已使用对应参考星归一化。默认读取旧版适配 JSON 的模式；原生 TXT 没有 C3/C4 标记，必要时明确选择与导出曲线匹配的数据类型。C3/C4 需要匹配的分析 CSV 和结果文件。本软件导入这些值，不重新测光、归一化或拟合。

## 噪声诊断

**噪声诊断** 只读取保存曲线，不解码影像。它分别显示保存的 SNR 与保护区基线 SNR，以及曝光、binning、相机来源和可用的背景/掩膜统计。

基线 SNR 为 `B/σB`。原生 TXT 的 σB 对应 PyOTE 拟合所用的采样，可能已经合并；标签明确标为 PyOTE 拟合，并在日志提供时显示合并读数。它不自动等同于原始相机每帧的 SNR。曲线诊断使用保存曲线采样的散布。诊断默认排除 D 前 1 秒至 R 后 1 秒，与视频裁剪秒数独立；缺少 D/R 时，已识别掩食外基线的统计显示不可用。

可选择两站比较共同绝对 UTC 的基线。没有共同录制时段时显示无法比较。像素背景预算是近似估计，不能分离探测器读出噪声；指标定义和假设保存在 `quality_report.json`。

## 输出与排错

每次运行创建新的结果目录。动画任务输出 MP4、GIF 和 PNG 预览；配置任务还保存 `resolved_config.json`、`media_metadata.json`、`run_metadata.json`、代码快照、输入哈希及诊断报告。桌面任务保留 `run.log` 和 `result.json`，结果位于 `media` 子目录。

| 问题 | 检查内容 |
| --- | --- |
| 未找到曝光 | 原始影像头部、对应 CameraSettings 或高级覆盖 |
| UTC 不一致 | 观测日期、曝光开始/中点约定、已经应用的相机时差 |
| PyOTE 模式不匹配 | 对应的分析曲线及结果文件 |
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

在目标平台运行 `Build-Windows.bat` 或 `Build-Mac.command`。Mac 脚本按当前 Python 的架构构建，M 系列使用 arm64；如需 Intel 版，可用 universal2 Python 执行 `python3 build_tools/create_macos_env.py --architecture x86_64`。Apple Silicon 版从随包保留的固定版本 ADVCore 源码编译解码库，同时附带 MPL 许可，ADV2 读取也原生运行。直接运行 ARM 源码时，可先执行 `python build_tools/prepare_adv_bundle.py`，再用 `PYTHONPATH=build_vendor python launch.py` 启动。支持的打包环境为 Python 3.13、Tcl/Tk 8.6，拖放依赖固定为兼容版本。版本标签通过 GitHub Actions 构建 Windows/macOS 包并执行独立应用自测。压缩包附带中英文说明、示例配置及视觉素材。

版本记录见 [CHANGELOG.md](CHANGELOG.md)，依赖许可证见 [THIRD_PARTY.md](THIRD_PARTY.md)。旧 `occultation-media` 命令和 Python 导入名 `occultation_media` 保留兼容。

## 路径北侧到南侧排序

在站点排列中选择 **路径北侧 → 南侧**。程序根据各站自身的预报最近接近时刻，
计算相对阴影路径的带符号横向偏移，并考虑地球自转；正值为北侧，负值为南侧。
需导入预测元素，即使不启用视频底部地图也能按路径排序。
光变行、对应影像和地图配色使用同一顺序；无法计算位置的站点放在最后。
`station_path_order.json` 保存偏移（公里）、预报最近接近 UTC 和计算残差。
**地理纬度 北 → 南** 是单独的排序选项。原始 UTC、测光和实测 D/R 保持不变。

## 可选的同步阴影地图

在主窗口日志下方勾选 **在视频／GIF底部加入同步地图**，点击 **设置预测元素**。
选择一个事件的 `.occelmnt` / XML 文件，或粘贴完整 XML。`examples/` 中附有本次
Altona 预测元素，可直接用于 2026-09-12 的观测。

通过 **地图视图** 选择 **完整阴影路径**（默认，固定展示整段路径和观测站）或
**跟随小行星**（阴影中心保持在画面中央，地图与观测站随之移动）。跟随模式整段
使用固定缩放比例。选择会保存在项目中，并应用于 MP4、GIF 和 PNG。

地图占满底部宽度，沿阴影路径重新投影，使运动方向从左到右，并放大至阴影通道。
深色圆形阴影按显示 UTC 移动；站点彩点和紧凑图例与上方光变行配色一致。
地图标注主要城市和投影后的地理北向，移除站点面板底部两行说明。
不显示右侧信息栏；原始帧号和曝光中点仍保留在上方影像标签和逐帧 CSV 中。地图离线生成。

输出 `shadow_frame_positions.csv`，记录每个通过核验的原始影像帧的预测位置，
同时保留曲线 UTC、原始源 UTC 与已应用时差。模拟不改变光变和测得的 D/R。
阴影按名义圆形轮廓计算，未包含预测或形状误差，不能当作实测掩食判断。
