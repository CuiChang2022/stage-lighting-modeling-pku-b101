# 舞台灯光 Blender 模拟工具（北京大学新太阳B101九一剧场用）

本目录提供一套已经生成好的 Blender 舞台场景，以及一个不依赖 MA2、Art-Net 或 Python 外部环境的基础灯光控台脚本。用户可以直接打开 `.blend` 文件，在 Blender Python Console 中选择灯具、设置 Dim 和 RGBW 颜色，并在 Rendered 视图中观察效果。

## 许可证与贡献规则

本项目选择 **GNU General Public License v3.0 (GPLv3)**。使用、发布或贡献本项目时，请同时阅读仓库中的 `LICENSE` 文件。

项目署名要求：

- 转载、发布或制作衍生版本时，必须保留原作者署名、项目链接和许可证声明；
- 不得移除现有的作者信息、README 说明或许可证文本。

本项目的发布政策是**仅限非商业使用**。不得将本项目或其衍生场景、脚本用于商业演出、商业制作、付费软件或其他营利性服务，除非事先取得项目维护者的书面许可。

同时，我希望任何新增函数、灯控命令、场景改进或修复，都可以联系我并提交到本仓库（发起pull request），以合并出一个功能完善的大仓库。提交时请说明修改内容、适用的 Blender 版本，并同步更新 README 或相关文档。

- 作者联系方式：CuiChang2022@gmail.com，CuiChang2022@stu.pku.edu.cn

## 安装须知

- 需要安装 Blender 5.0.1 或兼容的 Blender 5.x 版本；
- 不需要安装 Python、conda、`bpy` 或其他 pip 包；
- 不要用系统 Python 运行 `lighting_console_commands.py`。该脚本必须在 Blender 内运行，因为 `bpy` 是 Blender 内置模块，无法经由`pip`安装。

## 打开场景

1. 启动 Blender。
2. 选择 `File > Open`。
3. 打开 `lighting_modeling.blend`。
4. 如果只想看舞台模型和中控室，不想让灯具挡住观察视线，也可以打开 `stage_modeling.blend`。
5. 切换到 `Rendered` 视图，或者使用 `F12` 渲染当前相机画面。

## 加载灯光控台命令

打开 `lighting_modeling.blend` 后：

1. 切换到 `Scripting` 工作区。
2. 在 Text Editor 中打开 `lighting_console_commands.py`。
3. 点击 `Text > Reload`，确保使用磁盘上的最新版本。
4. 点击 `Run Script`。
5. 将任意区域切换为 `Python Console`。

脚本会把命令注册到 Blender 当前 Python 环境中。如果文件刚刚被修改过，需要重新执行一次 `Run Script` 即可。起初，46盏灯是全灭的。

## 基本控台命令

每条命令在 Python Console 中单独输入并按 Enter：

```python
fixture(1, 46)
```

选择 1 到 46 号灯，等价于 Grandma2 中的 `Fixture 1 Thru 46`。

```python
fixture(1, 10)
dim(50)
```

选择 1 到 10 号灯，并将它们设置为 Dim 50。

```python
fixture(8)
dim(0)
```

关闭 8 号灯。

```python
fixture(1, 46)
rgbw(100, 0, 0)
```

将选中灯具设置为红色。RGBW 参数范围为 `0-100`：

```python
rgbw(red, green, blue, white)
```

设置当前选择的硬切频闪。默认将 `Shutter` 的 `0-100` 换算为 `0-20 Hz`：

```python
fixture(1, 10)
shutter(25)          # 约 5 Hz
shutter(50, 8.0)     # 手动指定 8 Hz
stop_shutter()       # 停止频闪并恢复常亮
```

当前可用命令：

```python
blackout()   # 关闭当前选中的灯
out()        # 选择并关闭全部 46 盏灯
full()       # 将当前选中的灯设置为 Dim 100
shutter(25)  # 以约 5 Hz 进行硬切频闪
stop_shutter()  # 停止当前频闪
status()     # 查看当前选择的 Dim、Energy 和颜色
```

`dim()` 脚本使用一条低亮度补偿曲线，当前 `Dim=50` 对应约 `Energy=70710.7`（Blender 预览标定）。

## 相机与渲染

`lighting_modeling.blend` 中应包含：

- `Audience_Camera`：观众区视角；
- `Control_Room_Camera`：中控室视角。

在 Outliner 中选择相机后，可以使用 `Ctrl + 小键盘 0` 将它设为当前活动相机。单帧预览使用 `F12`；频闪或其他动画需要播放时间轴或使用 `Ctrl + F12` 渲染动画。

## 已知限制

- 这个控台脚本是 Blender 内部预览工具，离 Grandma2 目前很远，很远......；
- `Dim` 的功率曲线和 RGBW 颜色是用于预览的近似值，后续可使用现场照度、颜色和 Shutter 测量数据重新标定；
- `shutter()` 使用 Blender 定时器进行实时预览，关闭 Blender 或重新运行脚本前，建议先执行 `stop_shutter()`；
