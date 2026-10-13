# OccultationVisualiser v1.16.0 开发与审阅记录

日期：2026-10-13。范围：当前连续开发工作区，不以 Git HEAD 代表此前 1.15.0 的完整实现。保留原有未提交修改及原始观测资料；未提交、推送或发布。

## 按严重程度排列的具体发现

本轮没有确认 P0/P1 问题。以下 P2/P3 均有具体触发条件和代码证据；已修复问题与待处理限制分别标明。

| 优先级 / 状态 | 位置 | 触发、影响及验证证据 |
| --- | --- | --- |
| P2 / 已修复 | `compute_shadow_geometry.py:125–140`、`compute_station_path_offset.py:39–58` | 原实现以地心 FP 的 `z>0` 判断恒星可见性，椭球的地心方向并非当地地平法向。在纬度 45°、赤纬 −30°、时角略越过当地地平 0.05° 的构造例中，旧 z 仍为正，但独立计算的法向与恒星单位向量点积为负，会错误报告可见并影响近地平线的预报排序。现改为 geodetic normal 的点积。`test_geodetic_horizon_disagrees_with_geocentric_z` 验证反例；Altona 排序及数值保持不变。未加入大气折射或海拔造成的地平下沉。 |
| P2 / 已修复 | `read_tangra_photometry.py:99–108` | 旧 Tangra 命令行入口把每行时刻拼到同一日期；跨午夜 CSV 随后因时间倒退被拒绝，整秒标签也不符合原解析格式。现复用严格 UTC 序列解析，只有 >12 h 的倒退视作跨午夜，小倒退和重复仍拒绝。`test_legacy_tangra_midnight_and_whole_seconds` 核对 23:59:59.800 → 次日 00:00:00 为 0.2 s；净计数保持原值。现代多站入口原本已支持午夜，本次保留。 |
| P2 / 已修复 | `OccultationVisualiser.spec:16`、`record_media_run.py:55–66`、`self_test.py` | 冻结配置只打包字节码，`snapshot_code()` 查找 `*.py` 得到空集。实际用第一轮冻结版导出复现：`outputs/v1.16.0_frozen_before_source_fix/run_metadata.json` 中 `source_sha256={}`，虽然任务成功。现将对应构建源文件随包提供；冻结版自检要求关键源码哈希存在，修复后实际导出包含 68 个 Python 源文件哈希。 |
| P2 / 尚未修复的地图边界限制 | `render_shadow_map.py:93–94,118–126` | 阴影圆部分越过地球投影边缘时，`footprint()` 产生部分 NaN 顶点。当前静态走廊跳过该轮廓，动态层只画可见弧线，不沿椭球视边缘闭合、填充真实交集。`test_limb_rim_has_missing_vertices_documented_limitation` 用 FP 中心 `(0.998,0)` 复现部分有效顶点及此分支。近地平线事件不能把这段弧线视为完整阴影边界。Altona 本次时段所有边缘射线都在地球上，因此不受此限制影响；它不是 Altona 形状变化的原因。后续应对“圆盘与地球投影椭圆的交集”求闭合边界，再投到地表。 |
| P3 / 尚未修复的显示限制 | `render_shadow_map.py:100–106`、`render_station_panels.py:16` | 最多支持 8 站，但两处调色板只有 4 色并循环使用；第 1/5、2/6 站会同色。地图图例仅横向累加文字宽度，没有换行或截断，8 个测试长站名的累加终点为 x=3036，而右边界为 1884（`outputs/v1.16.0_legend_review.json`），会越过地图宽度。行和地图之间的颜色对应仍一致；Altona 四个短站名无溢出。应在扩展站数/长名称布局时提供 8 色和限定宽度图例。 |

新增 AVI 的 GUI 噪声诊断也复用所选曲线时标基准：生成、核验、quality-only 不因入口不同引入半曝光差。质量诊断不需要填 AVI 帧号，但 CSV 的时标约定仍须明确。该行为纳入 GUI 配置测试。

## AVI 已实现行为

- 包内 FFmpeg 顺序解码第一个视频流；禁止自动旋转及补帧/丢帧，不使用关键帧随机跳转。不新增 OpenCV 冻结依赖。
- 实际解码确定帧数，并检查 RIFF 容器截断、帧完整性、解码失败及帧范围。`source_index = curve_frame − source_first_frame`；不猜裁剪录像的首帧。
- CSV 必须明确曝光及 start/midpoint/end 约定。Tangra LC 使用已记录的曝光中点；GUI 可从配套 LC 读取曝光。
- 容器 FPS 不参与 UTC 或曝光推导。支持不规则曲线时刻、跨午夜、稀疏曲线帧号及部分影像覆盖；无覆盖时报错。
- 没有独立源 UTC 时，`source_midpoint_utc` 和 `residual_s` 为 null；映射标记 `independent_source_utc_verified=false`，图像与 metadata 均说明 UTC 来自曲线。阴影 CSV 同样保留该证据区别。
- 无压缩 BGR、FFV1、MJPEG 的六帧合成序列均通过实解码及双语导出；前两者 RGB 像素完全相同，MJPEG 选中帧最大平均绝对像素误差 0.7473/255。视频故意标 25 fps，而曲线使用 0.2/0.25 s 不规则间隔，验证程序不会拿容器时钟替代曲线。

不可独立验证用户给错的首帧号，或录像中间被删除/插入/重排的帧。当前不支持这类编辑录像、场级时序、自动去隔行、OCR 时间叠字或 MP4 输入。RGB8 是显示转换，不声称保持高位深原始 ADU；光变直接来自原保存曲线。顺序校验和读取需要两遍解码，长录像会增加准备时间。除三种已测编码外，其他 AVI 编码取决于包内 FFmpeg 支持情况，不能据此宣称覆盖全部 AVI。

## Altona 形状变化：计算、投影与渲染证据

`compute_shadow_geometry.py:102–111` 每帧使用同一个 **76.2 km** 直径，在基本平面取圆，再沿恒星方向与旋转地球椭球求交。这里没有小行星自转、三维形状模型，也没有按时间修改直径。

用 512 个等角圆周采样，在 5 个真实动画 UTC 上，将地面轮廓反投影回基本平面，半径均为 38.1 km，最大数值偏差小于 1e-8 km。独立用地表 ECEF 三维点的主轴估计地面尺寸，再与地图二维坐标的主轴比较：

| UTC 2026-09-12 | 地面主轴尺寸 km（近似） | 地面轴比 | 地图轴比 | 中心恒星高度 |
| --- | --- | --- | --- | --- |
| 09:54:23.412583057 | 78.8578 × 76.2000 | 1.034880 | 1.038906 | 75.0824° |
| 09:54:36.212583057 | 79.1369 × 76.2000 | 1.038541 | 1.042277 | 74.3421° |
| 09:55:51.693386741 | 81.5000 × 76.2000 | 1.069554 | 1.071262 | 69.2236° |
| 09:57:57.693386741 | 89.0902 × 76.2000 | 1.169163 | 1.168009 | 58.7951° |
| 09:58:18 | 90.9308 × 76.2000 | 1.193317 | 1.191780 | 56.9304° |

尺寸使用 `2*sqrt(2/N)*singular_values` 的等效椭圆直径；有限曲率地面边缘不是严格的平面椭圆，不能把这些数值解释为重新测量的小行星轴长。当地平面近似下，长轴随 `1/sin(恒星高度)` 拉伸，符合上述结果。

`project_shadow_path_map.py:42–55` 对地理数据和阴影使用同一个固定斜轴 Mercator；`render_shadow_map.py:54–68` 初始化后只使用一个固定 `scale`。本次始终为 **0.761768584 px/km**，x/y 符号相反但尺度相等。地图轴比和地面轴比的差约不超过 0.0041，源于绘图球面与地理投影；不是逐帧非等比缩放。

因此保留这段随位置变化的地面阴影，不能为了“看起来不变”强行画同一个圆。约 60 px 的轮廓加 3 px 描边可能表现出像素级边缘跳动，但不会产生这里约 15% 的轴比增长。

复现脚本：`build_tools/audit_shadow_shape.py`。
结果：`outputs/v1.16.0_shadow_shape/shape_metrics.json`、`shadow_shape_comparison.png` 和包含输入哈希的 `run_metadata.json`。

## 验证范围和交付

- 源码测试：75 项，`PYTHONPATH=src:build_vendor .venv313/bin/python -m unittest discover -s tests -q`。
- 原始 Altona：共 1794 帧（233 + 524 + 391 + 646），与前版每条 `frame_alignment`、D/R、255 个动画 UTC 完全一致。Peter 的 723 条曲线仅有 646 张匹配源图，77 条缺失仍留空；未补造影像。
- 顺序及路径偏移：R. Paine +36.166002 km；Unimelb 2 −0.364944 km；Unimelb 1 −5.968218 km；Peter Shottle −12.840628 km。保留各站前后 5 s、50x 连续空档、压缩标记、Observer 字段、离线地图和北向。
- 新真实双语导出：`outputs/v1.16.0_altona_media/`；AVI 合成示例：`outputs/v1.16.0_avi_example/`。已查看中文帧图、目标细节、地图、时间轴及形状比较图。
- GUI：通过中英文启动和站点编辑器字段可见性检查；`outputs/v1.16.0_gui_audit.json` 记录新时标选择器与首帧号字段的尺寸和值。GUI 测试使用本机窗口服务。
- 冻结版：原生 arm64；实际自检包含 ADV 原生解码、SER/FITS/RAVF/AVI、双语 GIF/MP4、Unicode、阴影、加速空档、路径排序、Observer 和源码哈希。报告位于 `dist/v1.16.0/package-self-test.json`。
- 本轮只构建 macOS Apple Silicon；没有运行 Windows/Intel 包，不能把本机结果视为跨平台验证。应用仍未经过 Apple notarization。

源码继续按 I/O（`read_avi_frames.py`）、科学核（`compute_shadow_geometry.py`）、编排（`prepare_avi_frames.py`、`make_station_media.py`）、绘图（`render_station_panels.py`）分工。源文件结构检查 0 error、1 warning：既有 `render_occultation_media.py` 249 行，是紧密耦合的旧版单画布渲染器，本次没有为 AVI 修改该布局。完整仓库检查会包含虚拟环境和历史源快照，不能把第三方文件告警算作本轮源码问题。

## 参考定义

- [FFmpeg 的帧率模式与转码参数](https://ffmpeg.org/ffmpeg.html)：使用 passthrough，保留解码帧顺序；它不提供观测绝对 UTC。
- [PROJ 球面 Mercator 定义](https://proj.org/en/stable/operations/projections/merc.html)及 [oblique transformation](https://proj.org/en/stable/operations/projections/ob_tran.html)：用于解释既有地图变换。
- 仓库既有预测字段来源固定为 Astrid 的 commit `11a3d320cc675567f1c28514585ff7a9c1a8cf28`；本轮网络未能重新读取该固定源码，未据此声称完成独立星历精度认证。验证覆盖本地几何逆变换、已知中心、固定半径、地平法向反例与真实逐帧回归，不等于验证 JPL 预报本身的天文误差。
