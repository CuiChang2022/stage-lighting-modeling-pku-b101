import builtins
import time

import bpy


ENERGY_SCALE = 100000.0
DIM_GAMMA = 0.5
SHUTTER_MAX_FREQUENCY_HZ = 20.0
SHUTTER_TIMER_KEY = "_lighting_console_strobe"


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


def stop_shutter():
    state = bpy.app.driver_namespace.pop(SHUTTER_TIMER_KEY, None)
    if state is None:
        return
    timer = state.get("timer")
    if timer is not None and bpy.app.timers.is_registered(timer):
        bpy.app.timers.unregister(timer)
    for light, energy in state["lights"]:
        light["dmx_Shutter"] = 0.0
        light["dmx_Shutter_Hz"] = 0.0
        light.data.energy = energy
    _redraw()
    _announce("Shutter 已停止，灯具恢复常亮。")


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
    stop_shutter()
    value = max(0.0, min(100.0, float(value)))
    energy = ENERGY_SCALE * (value / 100.0) ** DIM_GAMMA
    for light in _require_selection():
        _remove_drivers(light)
        light["dmx_Dim"] = value
        light["console_base_energy"] = energy
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


def shutter(value, frequency=None):
    """设置当前选择的硬切频闪；Shutter=0 停止频闪。"""
    value = max(0.0, min(100.0, float(value)))
    if value <= 0.0:
        stop_shutter()
        for light in _require_selection():
            light["dmx_Shutter"] = 0.0
            light["dmx_Shutter_Hz"] = 0.0
        return

    lights = _require_selection()
    stop_shutter()
    if frequency is None:
        frequency = SHUTTER_MAX_FREQUENCY_HZ * value / 100.0
    frequency = max(0.01, float(frequency))
    for light in lights:
        light["dmx_Shutter"] = value
        light["dmx_Shutter_Hz"] = frequency
    state = {
        "lights": [
            (light, float(light.get("console_base_energy", light.data.energy)))
            for light in lights
        ],
        "frequency": frequency,
        "started": time.monotonic(),
        "timer": None,
    }

    def update():
        if bpy.app.driver_namespace.get(SHUTTER_TIMER_KEY) is not state:
            return None
        phase = (time.monotonic() - state["started"]) * state["frequency"]
        is_open = phase % 1.0 < 0.5
        for light, energy in state["lights"]:
            light.data.energy = energy if is_open else 0.0
        _redraw()
        return 1.0 / 60.0

    state["timer"] = update
    bpy.app.driver_namespace[SHUTTER_TIMER_KEY] = state
    bpy.app.timers.register(update, first_interval=0.0)
    _announce(f"Shutter = {value:g}，频率 = {frequency:g} Hz。")


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
        "shutter": shutter,
        "stop_shutter": stop_shutter,
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