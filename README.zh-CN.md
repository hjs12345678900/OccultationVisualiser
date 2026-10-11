# OccultationMedia

[English](README.md) | **简体中文**

桌面掩星动画生成器：将观测星场与 Tangra 或已保存的 PyMovie/PyOTE 光变同步，导出 GIF、PNG 和 MP4。支持中文 / English 界面。

## 下载与使用

从 [Releases](https://github.com/hjs12345678900/OccultationMedia/releases/latest) 下载：

- **Windows 10/11 x64**：完整解压后打开 `OccultationMedia.exe`，保留 `_internal` 文件夹。
- **macOS 14+**：解压后打开 `OccultationMedia.app`。Intel 版；Apple Silicon 需要 Rosetta。

选择观测文件、Tangra CSV 和输出目录，填写日期、曝光时间及目标名称，点击生成。预报时间和区间可留空。

使用原生 PyMovie/PyOTE 或四站布局时，点击 **PyMovie / 四站配置…**，选择参照 [examples](examples) 编写的 JSON。路径、曝光和 D/R 字段见 [配置与 UTC 说明](docs/native_station_media.md)。左边排列四条光变，右边对应四站完整星场；统一绝对 UTC，未录到或缺失原始帧时显示无画面。

## 功能

- 输入：ADV2、SER、FITS 图像 / 序列 / 数据立方、RAVF，以及 Tangra LC 星点切片。
- 使用 Tangra CSV 测光与 UTC；填写源文件第 0 帧对应的 CSV 帧号以对齐。
- 自动读取 CSV 目标初始坐标，支持手动覆盖；标记仅右侧和下方两条线，不做逐帧跟踪。
- 首个显示帧的 0.5% / 99.95% 分位数确定固定拉伸，整段保持一致。
- 原生导入保留净计数、逐帧目标坐标及 raw/C3/C4 导出；直接显示保存的 PyOTE D/R，不重新拟合，不额外加半曝光。
- 配置模式在编码前核对原始帧号与曝光中点 UTC，支持 SER 的 100 ns 精度、ADV 已应用采集延迟、RAVF 时间及部分 FITS 序列。记录逐帧匹配残差、输入哈希和代码快照。
- 可选中英文输出，内置中文字体、Python 和 FFmpeg。

本工具用于动画展示，不用于正式掩星时刻测量。发布包未签名 / 公证；打包流程运行测试套件与冻结应用的编解码、字体、原生时间戳自检，另在本机核对真实 Altona ADV/SER/FITS 数据。

## 源码运行与打包

使用包含 Tk 的 Python 3.13，在虚拟环境中执行：

```bash
python -m pip install -e ".[build]"
python launch.py
python launch.py --media-config examples/four_stations.json --verify-only
python launch.py --media-config examples/four_stations.json
```

Windows 打包入口：`Build-Windows.bat`；Mac：`Build-Mac.command`。两者包含测试。
仅打包 Windows：`python package_windows_only.py`；仅打包 Mac：`python -m PyInstaller --noconfirm --clean OccultationMedia.spec`。
GitHub Actions 可手动触发，发布 tag 也会触发构建；验证后的应用包上传到对应草稿 release。第三方组件与许可见 [THIRD_PARTY.md](THIRD_PARTY.md)。
