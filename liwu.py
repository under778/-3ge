# -*- coding: utf-8 -*-

import os

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.audio import SoundLoader
from kivy.resources import resource_find
from kivy.core.text import LabelBase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_path(filename):
    p = resource_find(filename)
    if p:
        return p
    return os.path.join(BASE_DIR, filename)


# ================= 注册字体（解决乱码） =================
FONT_NAME = "Roboto"
font_path = get_path("game_font.ttf")
if os.path.exists(font_path):
    try:
        LabelBase.register(name="LiwuFont", fn_regular=font_path)
        FONT_NAME = "LiwuFont"
    except Exception:
        pass

# ================= 音频播放（解决被垃圾回收导致无声） =================
sound_obj = None


def play_sound():
    global sound_obj
    try:
        sound_obj = SoundLoader.load(get_path("shabi.wav"))
        if sound_obj:
            sound_obj.play()
    except Exception:
        pass


# ================= 模拟系统窗口的弹窗组件 =================
class CaiDanWindow(ModalView):
    def __init__(self, title, text="", bg_color=(1, 1, 1, 1), text_color=(0, 0, 0, 1), font_size=20, width=400,
                 height=200, close_callback=None, **kwargs):
        super().__init__(size_hint=(None, None), size=(width, height), background_color=(0, 0, 0, 0),
                         auto_dismiss=False, **kwargs)
        self.close_callback = close_callback

        main_layout = BoxLayout(orientation='vertical')

        # 1. 模拟顶部灰色标题栏
        title_bar = BoxLayout(size_hint_y=None, height=30, padding=[5, 0, 5, 0])
        with title_bar.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.title_bg = Rectangle(pos=title_bar.pos, size=title_bar.size)

        # 正确的更新方法，避免报错
        def update_title_bg(instance, value):
            self.title_bg.pos = instance.pos
            self.title_bg.size = instance.size

        title_bar.bind(pos=update_title_bg, size=update_title_bg)

        title_label = Label(text=title, color=(0, 0, 0, 1), font_name=FONT_NAME, font_size=14, halign='left',
                            valign='middle', size_hint_x=0.8)
        title_label.bind(size=lambda *a: setattr(title_label, 'text_size', title_label.size))
        title_bar.add_widget(title_label)

        # 2. 手工制作右上角“X”按钮
        self.close_btn = Button(text="X", size_hint=(None, 1), width=40, font_name=FONT_NAME, font_size=14,
                                background_color=(0, 0, 0, 0), color=(0, 0, 0, 1))
        self.close_btn.bind(on_release=self.on_close_clicked)
        title_bar.add_widget(self.close_btn)
        main_layout.add_widget(title_bar)

        # 3. 内容区
        self.content_area = BoxLayout()
        with self.content_area.canvas.before:
            self.bg_color_inst = Color(*bg_color)
            self.content_bg = Rectangle(pos=self.content_area.pos, size=self.content_area.size)

        def update_content_bg(instance, value):
            self.content_bg.pos = instance.pos
            self.content_bg.size = instance.size

        self.content_area.bind(pos=update_content_bg, size=update_content_bg)

        self.text_label = Label(text=text, color=text_color, font_name=FONT_NAME, font_size=font_size, halign='center',
                                valign='middle')
        self.text_label.bind(size=lambda *a: setattr(self.text_label, 'text_size', self.text_label.size))
        self.content_area.add_widget(self.text_label)
        main_layout.add_widget(self.content_area)

        self.add_widget(main_layout)

    def set_content_widget(self, widget):
        """供主菜单用：替换掉原本的文字Label，放入按钮布局"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(widget)

    def on_close_clicked(self, *args):
        if not self.close_btn.disabled:
            self.dismiss()
            if self.close_callback:
                self.close_callback()


# ================= 核心流程还原 =================

def abc():
    # 1. 弹出白底空窗，禁用 X 按钮（模拟原版的 time.sleep 卡死不可操作）
    win = CaiDanWindow(title="tk", text="", bg_color=(1, 1, 1, 1), width=320, height=200)
    win.close_btn.disabled = True
    win.open()

    def timer_end(dt):
        # 2. 10秒后：变红底、蓝字、字号80，窗口放大
        win.text_label.text = "准备好了吗?"
        win.text_label.font_size = 80
        win.text_label.color = (0, 0, 1, 1)
        win.bg_color_inst.rgba = (1, 0, 0, 1)
        win.size = (650, 220)

        # 3. 恢复 X 按钮的可用状态
        win.close_btn.disabled = False

        # 4. 定义关闭后的瞬间爆发：播声音 + 蓝底红字大图
        def on_close():
            play_sound()
            gh = CaiDanWindow(title="《真礼物》", text="傻逼！！！", bg_color=(0, 0, 1, 1), text_color=(1, 0, 0, 1),
                              font_size=208, width=1100, height=450)
            gh.open()

        win.close_callback = on_close

    Clock.schedule_once(timer_end, 10)


def abcd():
    # 1. 弹出红底蓝字警告窗
    def on_close():
        # 关闭后等 5 秒，进入 abc 流程
        Clock.schedule_once(lambda dt: abc(), 5)

    win = CaiDanWindow(title="tk", text="不要也得要！！！", bg_color=(1, 0, 0, 1), text_color=(0, 0, 1, 1), font_size=80,
                       width=800, height=220, close_callback=on_close)
    win.open()


def aa():
    abc()


def xin_dong():
    # 主窗：彩蛋-礼物
    win = CaiDanWindow(title="彩蛋-礼物", text="", bg_color=(1, 1, 1, 1), width=360, height=180)

    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    layout.add_widget(Label(text="我有一个礼物,你要吗？", color=(0, 0, 0, 1), font_name=FONT_NAME, font_size=18))

    btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
    btn_yes = Button(text="要，yes！", font_name=FONT_NAME, font_size=16)
    btn_no = Button(text="不要，NO！", font_name=FONT_NAME, font_size=16)
    btn_layout.add_widget(btn_yes)
    btn_layout.add_widget(btn_no)
    layout.add_widget(btn_layout)

    win.set_content_widget(layout)

    def click_yes(*a):
        win.dismiss()
        Clock.schedule_once(lambda dt: abc(), 0.1)

    def click_no(*a):
        win.dismiss()
        Clock.schedule_once(lambda dt: abcd(), 0.1)

    btn_yes.bind(on_release=click_yes)
    btn_no.bind(on_release=click_no)
    win.open()


# 兼容旧调用的壳子
class _XinGou:
    def mainloop(self, *a, **kw):
        return xin_dong()


xin = _XinGou()

# ================= 独立测试运行 =================
if __name__ == "__main__":
    from kivy.app import App


    class LiwuApp(App):
        def build(self):
            root = FloatLayout()
            with root.canvas.before:
                Color(0.2, 0.2, 0.2, 1)
                Rectangle(pos=root.pos, size=root.size)

            def sync(*a):
                root.canvas.before.clear()
                with root.canvas.before:
                    Color(0.2, 0.2, 0.2, 1)
                    Rectangle(pos=root.pos, size=root.size)

            root.bind(pos=sync, size=sync)
            Clock.schedule_once(lambda dt: xin_dong(), 0.5)
            return root


    LiwuApp().run()

