import builtins

import bpy


ENERGY_SCALE = 100000.0
DIM_GAMMA = 0.5


_selected_lights = []


def _announce(message):
    text = f"[Lighting Console] {message}"
    print(text)
    print()


def _get_light(number):
    name = f"PAR-{number:02d}_DMX_Light"
    light = bpy.data.objects.get(name)
    if light is None or light.type != "LIGHT":
        raise KeyError(f"找不到灯具：{name}")
    return light


def _redraw():
    bpy.context.view_layer.update()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _remove_drivers(light):
    light.data.driver_remove("energy")
    light.data.driver_remove("color")


def fixture(first, last=None):
    """选择灯具，类似 Fixture first Thru last。"""
    global _selected_lights
    if last is None:
        last = first
    if first > last:
        first, last = last, first
    _selected_lights = [_get_light(number) for number in range(first, last + 1)]

    bpy.ops.object.select_all(action="DESELECT")
    for light in _selected_lights:
        light.select_set(True)
    if _selected_lights:
        bpy.context.view_layer.objects.active = _selected_lights[-1]
    _announce(f"已选择 Fixture {first} Thru {last}，共 {len(_selected_lights)} 盏。")


def thru(last):
    """扩展当前选择到 1 至 last，适合快速输入 Fixture 1 Thru 46。"""
    return fixture(1, last)


def _require_selection():
    if not _selected_lights:
        raise RuntimeError("请先运行 fixture(first, last) 选择灯具。")
    return _selected_lights


def dim(value):
    """直接设置选中灯具的 Dim，绕过 Driver。"""
    value = max(0.0, min(100.0, float(value)))
    energy = ENERGY_SCALE * (value / 100.0) ** DIM_GAMMA
    for light in _require_selection():
        _remove_drivers(light)
        light["dmx_Dim"] = value
        light.data.energy = energy
    _redraw()
    _announce(f"Dim = {value:g}，Energy = {energy:g}。")


def rgbw(red, green, blue, white=0.0):
    """直接设置选中灯具的 RGBW 颜色，绕过 Driver。"""
    values = [max(0.0, min(100.0, float(value))) for value in (red, green, blue, white)]
    color = tuple(min(1.0, (channel + values[3]) / 100.0) for channel in values[:3])
    for light in _require_selection():
        _remove_drivers(light)
        for name, value in zip(("Red", "Green", "Blue", "White"), values):
            light[f"dmx_{name}"] = value
        light.data.color = color
    _redraw()
    _announce(f"RGBW = {values}，Blender color = {color}。")


def blackout():
    """关闭当前选择。"""
    dim(0.0)


def out():
    """关闭所有 46 盏灯。"""
    fixture(1, 46)
    blackout()


def full():
    """将当前选择设为满 Dim。"""
    dim(100.0)


def status():
    """打印当前选择的实际 Blender Energy。"""
    messages = []
    for light in _require_selection():
        messages.append(
            f"{light.name}: Dim={light.get('dmx_Dim', 0.0):g}, "
            f"Energy={light.data.energy:g}, Color={tuple(round(v, 3) for v in light.data.color)}"
        )
    _announce("\n".join(messages))


def expose_console_commands():
    commands = {
        "fixture": fixture,
        "thru": thru,
        "dim": dim,
        "rgbw": rgbw,
        "blackout": blackout,
        "out": out,
        "full": full,
        "status": status,
    }
    bpy.app.driver_namespace.update(commands)
    for name, command in commands.items():
        setattr(builtins, name, command)


expose_console_commands()
_announce(
    "命令已加载：fixture(1, 46)、dim(50)、rgbw(100, 0, 0)、"
    "blackout()、out()、full()、status()"
)