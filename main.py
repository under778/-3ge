# -*- coding: utf-8 -*-
import os
import sys
import random
import time
import pickle

# 注意：去掉了 KIVY_NO_CONSOLELOG，方便你抓日志

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Scale, Translate, InstructionGroup
from kivy.core.text import Label as CoreLabel, LabelBase
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

# ==================== 资源路径工具 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    p = resource_find(filename)
    if p:
        return p
    return os.path.join(BASE_DIR, filename)

def cun_dang_lu_jing():
    # 采用大佬建议：使用 Kivy 官方推荐的应用私有目录
    try:
        app = App.get_running_app()
        if app:
            return os.path.join(app.user_data_dir, 'cundang.pkl')
    except Exception:
        pass
    return 'cundang.pkl'

# ==================== 常量定义 ====================
PING_MU_KD = 1200
PING_MU_GD = 600
DI_MIAN_Y = 400
DAN_YAO_JG = 200
DAN_YAO_KS = 200
YD_SU_DU = 5
ZHEN_LV = 60
GUA_JI_CHI_ZD = 200
LUN_HUI_AN_MS = 10
LUN_HUI_JI_CHU_ZL = 5000

JIAN_KONG_GE = 32
JIAN_Z = 122
JIAN_X = 120
JIAN_Y = 121
JIAN_N = 110
JIAN_LEFT = 276
JIAN_RIGHT = 275

YS_BAI = (255, 255, 255)
YS_HEI = (0, 0, 0)
YS_HONG = (255, 0, 0)
YS_LV = (0, 255, 0)
YS_LAN = (0, 0, 255)
YS_HUANG = (255, 255, 0)
YS_CHENG = (255, 165, 0)
YS_ZI = (128, 0, 128)
YS_HUI = (128, 128, 128)
YS_QIAN_LAN = (173, 216, 230)
YS_SHEN_LV = (0, 128, 0)
YS_TU = (139, 69, 19)
YS_JIN = (255, 215, 0)

DAN_WEI_LB = ['', '万', '亿', '兆', '京', '垓', '秭', '穰', '沟', '涧',
              '正', '载', '极', '恒河沙', '阿僧祇', '那由他', '不可思议',
              '无量', '大数', '无敌']

def shu_zi_zhuan_huan(shu_zi):
    if shu_zi < 10000:
        return str(int(shu_zi))
    for i in range(len(DAN_WEI_LB) - 1, 0, -1):
        ji_shu = 10 ** (4 * i)
        if shu_zi >= ji_shu:
            zhi = shu_zi / ji_shu
            return f"{zhi:.4f}{DAN_WEI_LB[i]}"
    return str(shu_zi)

def jie_xi_dan_wei(wen_ben):
    wen_ben = wen_ben.strip()
    for i in range(len(DAN_WEI_LB) - 1, -1, -1):
        if DAN_WEI_LB[i] in wen_ben:
            shu_zi_str = wen_ben.replace(DAN_WEI_LB[i], '')
            try:
                if shu_zi_str == '' or shu_zi_str == '一':
                    shu_zi = 1.0
                else:
                    shu_zi = float(shu_zi_str)
                return int(shu_zi * (10 ** (4 * i)))
            except:
                pass
    try:
        return int(float(wen_ben))
    except:
        return 0

LUN_HUI_SL_LB = [
    "500涧", "46.5正", "4.9载", "5840载", "21极", "778极",
    "2.96恒河沙", "177恒河沙", "一阿僧祇", "70阿僧祇",
    "4650阿僧祇", "31那由他", "2200那由他", "16不可思议",
    "1180不可思议", "8无量", "700无量", "7大数",
    "120大数", "9999大数"
]
LUN_HUI_SL_ZS = [jie_xi_dan_wei(s) for s in LUN_HUI_SL_LB]

def ji_suan_dan_yao_jc(di_tu_bian_hao, jie_shu):
    jia_cheng = 10
    jia_cheng *= 5 ** (jie_shu - 1)
    if di_tu_bian_hao > 1:
        jia_cheng *= 5 ** (9 * (di_tu_bian_hao - 1))
        jia_cheng *= 20 ** (di_tu_bian_hao - 1)
    return jia_cheng

def zhu_ce_zhong_wen_zi_ti():
    font_path = get_path("game_font.ttf")
    if os.path.exists(font_path):
        try:
            LabelBase.register(name="ZhongWenZiTi", fn_regular=font_path)
            return "ZhongWenZiTi"
        except Exception:
            pass
    return "Roboto"

ZHONG_WEN_ZT = zhu_ce_zhong_wen_zi_ti()
ZI_TI_MING = ZHONG_WEN_ZT if ZHONG_WEN_ZT else "Roboto"

def zhuan_yan_se(yan_se):
    if len(yan_se) == 3:
        return (yan_se[0] / 255.0, yan_se[1] / 255.0, yan_se[2] / 255.0, 1.0)
    return (yan_se[0] / 255.0, yan_se[1] / 255.0, yan_se[2] / 255.0, yan_se[3] / 255.0)

# ==================== 游戏主类 ====================
class YouXi(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)

        self.zi_ti_da = 30
        self.zi_ti_zhong = 20
        self.zi_ti_xiao = 14
        self.zi_ti_jiao_cheng = 16

        try:
            self.wan_jia_tp = CoreImage(get_path("player.png")).texture
        except Exception:
            self.wan_jia_tp = None

        self.yin_yue = None
        try:
            self.yin_yue = SoundLoader.load(get_path("bgm.wav"))
            if self.yin_yue:
                self.yin_yue.loop = True
                self.yin_yue.volume = 0.3
                self.yin_yue.play()
        except Exception:
            pass

        try:
            self.yin_xiao_niu = SoundLoader.load(get_path("niubi.wav"))
        except Exception:
            self.yin_xiao_niu = None
        try:
            self.yin_xiao_sha = SoundLoader.load(get_path("shabi.wav"))
        except Exception:
            self.yin_xiao_sha = None

        self.zhan_li = 3000
        self.lun_hui_cs = 0
        self.diao_luo_bl = 1
        self.lun_hui_jc = 1.0
        self.wan_jia_x = DAN_YAO_KS
        self.wan_jia_y = DI_MIAN_Y - 50
        self.dang_qian_dt = 1
        self.dang_qian_cj = "map"
        self.you_xi_zt = "youxi"
        self.she_xiang_x = 0
        self.di_tu_dan_yao = [[] for _ in range(10)]
        self.bei_lv_dan_lb = []
        self.wu_ji_dan_lb = []
        self.bei_lv_dan_jss = 0
        self.gua_ji_jss = 0
        self.kong_ge_an_x = False
        self.kong_ge_an_sj = 0
        self.lun_hui_yc = False
        self.zi_mu_wb = ""
        self.zi_mu_djs = 0
        self.shu_ru_hc = ""
        self.shu_ru_djs = 0
        self.shang_ci_qy = ""
        self.an_jian_zt = {}
        self._wen_ben_huan_cun = {}
        self._ding_shi_qi = None
        self.an_xia_de_di_bu_an = None
        self.jian_pan_tan_chuang = None

        # 核心改造：用 InstructionGroup 代替 canvas.clear()
        self.draw_group = InstructionGroup()
        self.canvas.add(self.draw_group)

        self.jia_zai_cun_dang()
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(self.dang_qian_dt)

    def _huo_qu_suo_fang(self):
        if self.width <= 0 or self.height <= 0:
            return 1.0, 0, 0
        scale = min(self.width / PING_MU_KD, self.height / PING_MU_GD)
        offset_x = (self.width - PING_MU_KD * scale) / 2
        offset_y = (self.height - PING_MU_GD * scale) / 2
        return scale, offset_x, offset_y

    def _huo_qu_wen_ben_wen_li(self, wen_ben, zi_ti, yan_se):
        guan_jian = (wen_ben, zi_ti, yan_se)
        if guan_jian not in self._wen_ben_huan_cun:
            cl = CoreLabel(text=wen_ben, font_size=zi_ti, font_name=ZI_TI_MING, color=zhuan_yan_se(yan_se))
            cl.refresh()
            self._wen_ben_huan_cun[guan_jian] = cl
        return self._wen_ben_huan_cun[guan_jian].texture

    def _hua_wen_ben(self, wen_ben, x, y, zi_ti, yan_se, ju_zhong=False):
        tex = self._huo_qu_wen_ben_wen_li(wen_ben, zi_ti, yan_se)
        kuan = tex.width
        if ju_zhong:
            x = x - kuan // 2
        ky = PING_MU_GD - y - tex.height
        self.draw_group.add(Color(1, 1, 1, 1))
        self.draw_group.add(Rectangle(texture=tex, pos=(x, ky), size=tex.size))
        return kuan

    def _hua_ju_xing(self, yan_se, x, y, kuan, gao, bian_kuan=0, bian_yan_se=None):
        ky = PING_MU_GD - y - gao
        self.draw_group.add(Color(*zhuan_yan_se(yan_se)))
        self.draw_group.add(Rectangle(pos=(x, ky), size=(kuan, gao)))
        if bian_kuan > 0:
            self.draw_group.add(Color(*zhuan_yan_se(bian_yan_se if bian_yan_se else YS_BAI)))
            self.draw_group.add(Line(rectangle=(x, ky, kuan, gao), width=bian_kuan))

    def _hua_yuan(self, yan_se, cx, cy, ban_jing):
        self.draw_group.add(Color(*zhuan_yan_se(yan_se)))
        self.draw_group.add(Ellipse(pos=(cx - ban_jing, PING_MU_GD - cy - ban_jing), size=(ban_jing * 2, ban_jing * 2)))

    def _hua_xian(self, yan_se, x1, y1, x2, y2, kuan=1):
        self.draw_group.add(Color(*zhuan_yan_se(yan_se)))
        self.draw_group.add(Line(points=[x1, PING_MU_GD - y1, x2, PING_MU_GD - y2], width=kuan))

    def sheng_cheng_dy_dian(self, di_tu_bian_hao):
        dy_dian = []
        for jie_shu in range(1, 11):
            x = DAN_YAO_KS + (jie_shu - 1) * DAN_YAO_JG
            jia_cheng = ji_suan_dan_yao_jc(di_tu_bian_hao, jie_shu)
            ming_cheng = f"地图{di_tu_bian_hao}的{jie_shu}阶丹"
            dy_dian.append({"x": x, "jie_shu": jie_shu, "jia_cheng": jia_cheng, "ming_cheng": ming_cheng})
        return dy_dian

    def xian_shi_zi_mu(self, wen_ben):
        self.zi_mu_wb = wen_ben
        self.zi_mu_djs = 3.0

    def jian_ce_an_niu(self, shu_biao_x, shu_biao_y):
        an_niu_wz = [
            ("ditu", 10, 100, 80, 35), ("fuben", 10, 145, 80, 35), ("guaji", 10, 190, 80, 35),
            ("huicheng", 10, 235, 80, 35), ("jiaocheng", 10, 280, 80, 35),
            ("cundang", 10, 325, 80, 35), ("jianpan", 10, 370, 80, 35),
        ]
        for ming, ax, ay, ak, ag in an_niu_wz:
            if ax <= shu_biao_x <= ax + ak and ay <= shu_biao_y <= ay + ag:
                return ming
        return None

    def _di_bu_an_niu_wz_lb(self):
        return [
            ("zuo", 20, 510, 160, 70, YS_LAN),
            ("you", 200, 510, 160, 70, YS_LAN),
            ("kongge", 700, 510, 200, 70, YS_LV),
            ("z", 910, 510, 130, 70, YS_CHENG),
            ("x", 1050, 510, 130, 70, YS_CHENG),
        ]

    def _jian_ce_di_bu_an_niu(self, x, y):
        if self.you_xi_zt != "youxi":
            return None
        for ming, ax, ay, ak, ag, ys in self._di_bu_an_niu_wz_lb():
            if ax <= x <= ax + ak and ay <= y <= ay + ag:
                return ming
        return None

    def _di_bu_an_niu_an_x(self, ming):
        if ming == "zuo": self.an_jian_zt[JIAN_LEFT] = True
        elif ming == "you": self.an_jian_zt[JIAN_RIGHT] = True
        elif ming == "kongge": self.chu_li_an_jian_an_x(JIAN_KONG_GE)
        elif ming == "z": self.an_jian_zt[JIAN_Z] = True
        elif ming == "x": self.an_jian_zt[JIAN_X] = True

    def _di_bu_an_niu_tai_qi(self, ming):
        if ming == "zuo": self.an_jian_zt[JIAN_LEFT] = False
        elif ming == "you": self.an_jian_zt[JIAN_RIGHT] = False
        elif ming == "kongge": self.chu_li_an_jian_tai_qi(JIAN_KONG_GE)
        elif ming == "z":
            self.an_jian_zt[JIAN_Z] = False
            self.chu_li_an_jian_tai_qi(JIAN_Z)
        elif ming == "x":
            self.an_jian_zt[JIAN_X] = False
            self.chu_li_an_jian_tai_qi(JIAN_X)

    def hui_hua_di_bu_an_niu(self):
        ming_zi_lb = {"zuo": "左", "you": "右", "kongge": "空格", "z": "z", "x": "x"}
        for ming, ax, ay, ak, ag, ys in self._di_bu_an_niu_wz_lb():
            an_xia = (ming == "zuo" and self.an_jian_zt.get(JIAN_LEFT)) or \
                     (ming == "you" and self.an_jian_zt.get(JIAN_RIGHT)) or \
                     (ming == "kongge" and self.kong_ge_an_x) or \
                     (ming == "z" and self.an_jian_zt.get(JIAN_Z)) or \
                     (ming == "x" and self.an_jian_zt.get(JIAN_X))
            hua_ys = YS_JIN if an_xia else ys
            self._hua_ju_xing(hua_ys, ax, ay, ak, ag, 3, YS_BAI)
            self._hua_wen_ben(ming_zi_lb[ming], ax + ak // 2, ay + (ag - 30) // 2, self.zi_ti_da, YS_BAI, ju_zhong=True)

    def diao_chu_jian_pan(self):
        bu_ju = BoxLayout(orientation='vertical', spacing=10, padding=10)
        shu_ru_kuang = TextInput(text='', multiline=False, font_size=24, font_name=ZI_TI_MING)
        bu_ju.add_widget(shu_ru_kuang)
        an_niu_bu_ju = BoxLayout(size_hint_y=None, height=60, spacing=10)
        que_ding_an = Button(text='确定', font_size=24, font_name=ZI_TI_MING)
        qu_xiao_an = Button(text='取消', font_size=24, font_name=ZI_TI_MING)
        an_niu_bu_ju.add_widget(que_ding_an)
        an_niu_bu_ju.add_widget(qu_xiao_an)
        bu_ju.add_widget(an_niu_bu_ju)
        tan_chuang = Popup(title='键盘输入', content=bu_ju, size_hint=(0.45, 0.35), title_size=20)
        try: tan_chuang.title_font = ZI_TI_MING
        except Exception: pass
        self.jian_pan_tan_chuang = tan_chuang

        def _que_ding(*args):
            for zi_fu in shu_ru_kuang.text:
                if zi_fu.isalpha(): self.chu_li_an_jian_an_x(ord(zi_fu.lower()))
            tan_chuang.dismiss()

        que_ding_an.bind(on_release=_que_ding)
        qu_xiao_an.bind(on_release=lambda *a: tan_chuang.dismiss())
        tan_chuang.bind(on_dismiss=lambda *a: setattr(self, 'jian_pan_tan_chuang', None))
        tan_chuang.open()
        shu_ru_kuang.focus = True

    def hui_hua_an_niu(self):
        an_niu_lb = [
            ("地图", 10, 100, 80, 35, YS_LAN), ("副本", 10, 145, 80, 35, YS_ZI),
            ("挂机", 10, 190, 80, 35, YS_LV), ("回城", 10, 235, 80, 35, YS_CHENG),
            ("教程", 10, 280, 80, 35, YS_HUI), ("存档", 10, 325, 80, 35, YS_JIN),
            ("键盘", 10, 370, 80, 35, YS_QIAN_LAN),
        ]
        for ming, ax, ay, ak, ag, ys in an_niu_lb:
            self._hua_ju_xing(ys, ax, ay, ak, ag, 2, YS_BAI)
            self._hua_wen_ben(ming, ax + 15, ay + 8, self.zi_ti_xiao, YS_BAI)

    def hui_hua_zhuang_tai_lan(self):
        self._hua_wen_ben(f"战力: {shu_zi_zhuan_huan(self.zhan_li)}", 100, 10, self.zi_ti_zhong, YS_JIN)
        self._hua_wen_ben(f"轮回数: {self.lun_hui_cs}", 100, 40, self.zi_ti_zhong, YS_BAI)
        self._hua_wen_ben(f"掉落倍率: {self.diao_luo_bl}", 100, 70, self.zi_ti_zhong, YS_BAI)

    def hui_hua_zi_mu(self):
        if self.zi_mu_djs > 0 and self.zi_mu_wb:
            self._hua_wen_ben(self.zi_mu_wb, PING_MU_KD // 2, 120, self.zi_ti_da, YS_HUANG, ju_zhong=True)

    def hui_hua_di_mian(self):
        self._hua_xian(YS_TU, 0, DI_MIAN_Y, PING_MU_KD, DI_MIAN_Y, 3)

    def hui_hua_dan_yao_dian(self):
        if self.dang_qian_cj != "map": return
        for dy in self.dang_qian_dy_dian:
            sx = dy["x"] - self.she_xiang_x
            if -100 <= sx <= PING_MU_KD + 100:
                self._hua_yuan(YS_HONG, sx, DI_MIAN_Y - 5, 8)
                self._hua_wen_ben(dy["ming_cheng"], sx, DI_MIAN_Y - 40, self.zi_ti_xiao, YS_BAI, ju_zhong=True)

    def hui_hua_yi_sheng_dan(self):
        if self.dang_qian_cj == "map":
            dy_lb = self.di_tu_dan_yao[self.dang_qian_dt - 1]
            for i, dy in enumerate(dy_lb):
                sx = dy["x"] + (i % 5) * 8 - 16 - self.she_xiang_x
                sy = DI_MIAN_Y - 15 - (i // 5) * 10
                if -50 <= sx <= PING_MU_KD + 50:
                    self._hua_yuan(YS_ZI if "无极" in dy["ming_cheng"] else YS_LV, sx, sy, 6)
        elif self.dang_qian_cj == "fuben1":
            for i, dy in enumerate(self.bei_lv_dan_lb):
                sx = dy["x"] + (i % 5) * 8 - 16 - self.she_xiang_x
                sy = DI_MIAN_Y - 15 - (i // 5) * 10
                if -50 <= sx <= PING_MU_KD + 50:
                    self._hua_yuan(YS_HUANG, sx, sy, 7)
        elif self.dang_qian_cj == "fuben2":
            for i, dy in enumerate(self.wu_ji_dan_lb):
                sx = dy["x"] + (i % 5) * 8 - 16 - self.she_xiang_x
                sy = DI_MIAN_Y - 15 - (i // 5) * 10
                if -50 <= sx <= PING_MU_KD + 50:
                    self._hua_yuan(YS_ZI, sx, sy, 6)

    def hui_hua_wan_jia(self):
        sx = self.wan_jia_x - self.she_xiang_x
        if self.wan_jia_tp is not None:
            self.draw_group.add(Color(1, 1, 1, 1))
            self.draw_group.add(Rectangle(texture=self.wan_jia_tp, pos=(sx, PING_MU_GD - self.wan_jia_y - 50), size=(40, 50)))
        else:
            self._hua_ju_xing(YS_LAN, sx, self.wan_jia_y, 40, 50)

    def hui_hua_gua_ji_chi(self):
        if self.dang_qian_cj == "map" and self.dang_qian_dt == 1:
            for x in range(-400, GUA_JI_CHI_ZD, 50):
                sx = x - self.she_xiang_x
                if -50 <= sx <= PING_MU_KD + 50:
                    self._hua_ju_xing(YS_QIAN_LAN, sx, DI_MIAN_Y - 20, 40, 20)
            sx = 0 - self.she_xiang_x
            if -100 <= sx <= PING_MU_KD + 100:
                self._hua_wen_ben("挂机池", sx, DI_MIAN_Y - 50, self.zi_ti_xiao, YS_QIAN_LAN, ju_zhong=True)

    def hui_hua_di_tu_xz(self):
        self._hua_ju_xing((0, 0, 0, 200), 0, 0, PING_MU_KD, PING_MU_GD)
        self._hua_wen_ben("选择地图", PING_MU_KD // 2, 50, self.zi_ti_da, YS_BAI, ju_zhong=True)
        for i in range(10):
            hang = i // 5; lie = i % 5
            ax = 200 + lie * 160; ay = 150 + hang * 150
            self._hua_ju_xing(YS_LAN, ax, ay, 140, 80, 2, YS_BAI)
            self._hua_wen_ben(f"地图{i + 1}", ax + 70, ay + 25, self.zi_ti_zhong, YS_BAI, ju_zhong=True)
        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 500, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 510, self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_fu_ben_xz(self):
        self._hua_ju_xing((0, 0, 0, 200), 0, 0, PING_MU_KD, PING_MU_GD)
        self._hua_wen_ben("选择副本", PING_MU_KD // 2, 50, self.zi_ti_da, YS_BAI, ju_zhong=True)
        self._hua_ju_xing(YS_ZI, 300, 150, 250, 100, 2, YS_BAI)
        self._hua_wen_ben("副本1（倍率丹）", 425, 185, self.zi_ti_zhong, YS_BAI, ju_zhong=True)
        self._hua_ju_xing(YS_ZI, 650, 150, 250, 100, 2, YS_BAI)
        self._hua_wen_ben("副本2（无极魔丹）", 775, 185, self.zi_ti_zhong, YS_BAI, ju_zhong=True)
        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 500, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 510, self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_jiao_cheng(self):
        self._hua_ju_xing((0, 0, 0, 220), 0, 0, PING_MU_KD, PING_MU_GD)
        self._hua_wen_ben("游戏教程", PING_MU_KD // 2, 15, self.zi_ti_da, YS_HUANG, ju_zhong=True)
        jiao_cheng_wb = [
            "【基本规则】", "1. 10个主地图，每个地图有10种常规丹药生成点", "2. 空格键生成丹药（松开时），数量=掉落倍率",
            "3. Z键吃掉所有常规丹药加战力（松开时）", "4. 地图1一阶丹+10战力，每阶×5，跨地图×20",
            "5. 生成丹药需战力≥丹药加成×300", "6. 挂机池在地图1一阶丹左侧，每秒+0.03%战力",
            "", "【副本】", "7. 副本1：每3秒生成倍率丹，X键吃，掉落倍率+1", "8. 副本2：空格生成无极魔丹，加战力0.01%/颗",
            "", "【轮回】", "9. 长按空格10秒触发轮回询问", "10. 轮回后战力变5000，加成×1.5，最多20次",
            "", "【界面按钮】", "左下角：“左”“右”与键盘左右箭头相同（按住持续移动）",
            "右下角：“空格”“z”“x”与键盘对应按键相同", "左侧“键盘”按钮：弹出输入框，用于输入文字触发彩蛋",
            "", "【单位】", "万=10^4, 亿=10^8, 兆=10^12...无敌=10^76",
            "", "【彩蛋】", "地图6六阶丹区输入under，地图7八阶丹区输入lisan",
            "", "【存档】", "游戏退出时自动保存，也可点击左侧“存档”按钮手动保存"
        ]
        for i, hang in enumerate(jiao_cheng_wb):
            y = 55 + i * 22
            self._hua_wen_ben(hang, 50, y, self.zi_ti_jiao_cheng, YS_BAI)
        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 555, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 563, self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_lun_hui_que_ren(self):
        self._hua_ju_xing((0, 0, 0, 180), 0, 0, PING_MU_KD, PING_MU_GD)
        self._hua_ju_xing(YS_HUI, 250, 180, 700, 240, 3, YS_JIN)
        suo_xu = LUN_HUI_SL_ZS[self.lun_hui_cs] if self.lun_hui_cs < 20 else 0
        self._hua_wen_ben("是否轮回？", PING_MU_KD // 2, 200, self.zi_ti_da, YS_HONG, ju_zhong=True)
        self._hua_wen_ben(f"当前轮回数: {self.lun_hui_cs}", 300, 250, self.zi_ti_zhong, YS_BAI)
        self._hua_wen_ben(f"所需战力: {shu_zi_zhuan_huan(suo_xu)}", 300, 280, self.zi_ti_zhong, YS_BAI)
        self._hua_wen_ben(f"当前战力: {shu_zi_zhuan_huan(self.zhan_li)}", 300, 310, self.zi_ti_zhong, YS_BAI)
        if self.zhan_li >= suo_xu: self._hua_wen_ben("√ 战力充足，可以轮回！", 300, 340, self.zi_ti_zhong, YS_LV)
        else: self._hua_wen_ben("× 战力不足，无法轮回！", 300, 340, self.zi_ti_zhong, YS_HONG)
        self._hua_ju_xing(YS_LV, 350, 380, 120, 40, 2, YS_BAI)
        self._hua_wen_ben("确认(Y)", 410, 390, self.zi_ti_zhong, YS_BAI, ju_zhong=True)
        self._hua_ju_xing(YS_HONG, 730, 380, 120, 40, 2, YS_BAI)
        self._hua_wen_ben("取消(N)", 790, 390, self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def jin_ru_di_tu(self, di_tu_bian_hao):
        self.dang_qian_dt = di_tu_bian_hao
        self.dang_qian_cj = "map"
        self.wan_jia_x = DAN_YAO_KS
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(di_tu_bian_hao)
        self.shang_ci_qy = ""
        self.xian_shi_zi_mu(f"进入地图{di_tu_bian_hao}")

    def jin_ru_fu_ben(self, fu_ben_bian_hao):
        if fu_ben_bian_hao == 1:
            self.dang_qian_cj = "fuben1"; self.wan_jia_x = 200; self.xian_shi_zi_mu("进入副本1")
        elif fu_ben_bian_hao == 2:
            self.dang_qian_cj = "fuben2"; self.wan_jia_x = 200; self.xian_shi_zi_mu("进入副本2")
        self.shang_ci_qy = ""

    def gua_ji(self):
        self.dang_qian_dt = 1; self.dang_qian_cj = "map"; self.wan_jia_x = 100
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(1); self.shang_ci_qy = ""
        self.xian_shi_zi_mu("进入挂机池")

    def hui_cheng(self):
        self.dang_qian_dt = 1; self.dang_qian_cj = "map"; self.wan_jia_x = DAN_YAO_KS
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(1); self.shang_ci_qy = ""
        self.xian_shi_zi_mu("回城")

    def sheng_cheng_dan_yao(self):
        if self.dang_qian_cj != "map": return
        for dy in self.dang_qian_dy_dian:
            if abs(self.wan_jia_x - dy["x"]) < 40:
                suo_xu = dy["jia_cheng"] * 300
                if self.zhan_li >= suo_xu:
                    for i in range(self.diao_luo_bl):
                        self.di_tu_dan_yao[self.dang_qian_dt - 1].append({
                            "x": dy["x"] + random.randint(-20, 20), "y": DI_MIAN_Y - 15,
                            "ming_cheng": dy["ming_cheng"], "jia_cheng": dy["jia_cheng"], "lei_xing": "chang_gui"
                        })
                    self.xian_shi_zi_mu(f"生成{self.diao_luo_bl}个{dy['ming_cheng']}")
                else: self.xian_shi_zi_mu(f"战力不足！")
                return
        self.xian_shi_zi_mu("不在丹药生成点附近")

    def sheng_cheng_wu_ji_dan(self):
        if self.dang_qian_cj != "fuben2": return
        gai_lv = random.random()
        if gai_lv < 0.60: shu_liang = 1
        elif gai_lv < 0.90: shu_liang = 3
        elif gai_lv < 0.9999: shu_liang = 5
        else: shu_liang = 20
        for i in range(shu_liang):
            self.wu_ji_dan_lb.append({
                "x": self.wan_jia_x + random.randint(-30, 30), "y": DI_MIAN_Y - 15,
                "ming_cheng": "无极魔丹", "jia_cheng": 0, "lei_xing": "wu_ji"
            })
        self.xian_shi_zi_mu(f"生成{shu_liang}颗无极魔丹！")

    def chi_suo_you_dan(self):
        chi_le = 0; zong_jia = 0
        if self.dang_qian_cj == "map":
            dy_lb = self.di_tu_dan_yao[self.dang_qian_dt - 1]
            for dy in dy_lb:
                jia_cheng = int(dy["jia_cheng"] * self.lun_hui_jc)
                self.zhan_li += jia_cheng; zong_jia += jia_cheng; chi_le += 1
            dy_lb.clear()
        elif self.dang_qian_cj == "fuben2":
            for dy in self.wu_ji_dan_lb:
                jia_cheng = int(self.zhan_li * 0.0001 * self.lun_hui_jc)
                if jia_cheng < 1: jia_cheng = 1
                self.zhan_li += jia_cheng; zong_jia += jia_cheng; chi_le += 1
            self.wu_ji_dan_lb.clear()
        if chi_le > 0: self.xian_shi_zi_mu(f"吃掉{chi_le}颗丹药，战力+{shu_zi_zhuan_huan(zong_jia)}")
        else: self.xian_shi_zi_mu("没有可吃的丹药")

    def chi_bei_lv_dan(self):
        if self.dang_qian_cj != "fuben1": return
        if len(self.bei_lv_dan_lb) > 0:
            self.bei_lv_dan_lb.pop(0); self.diao_luo_bl += 1
            self.xian_shi_zi_mu(f"吃倍率丹！掉落倍率+1，当前{self.diao_luo_bl}")
        else: self.xian_shi_zi_mu("没有倍率丹可吃")

    def lun_hui(self):
        suo_xu = LUN_HUI_SL_ZS[self.lun_hui_cs] if self.lun_hui_cs < 20 else 0
        if self.zhan_li >= suo_xu and self.lun_hui_cs < 20:
            self.zhan_li = LUN_HUI_JI_CHU_ZL
            self.lun_hui_cs += 1
            self.lun_hui_jc *= 1.5
            self.xian_shi_zi_mu(f"轮回成功！第{self.lun_hui_cs}次轮回，加成×1.5")
            self.you_xi_zt = "youxi"
        else:
            self.xian_shi_zi_mu("战力不足或已达最大轮回次数！")
            self.you_xi_zt = "youxi"

    def jian_ce_qu_yu(self):
        if self.dang_qian_cj == "map":
            if self.dang_qian_dt == 1 and self.wan_jia_x < GUA_JI_CHI_ZD: qy = "挂机池"
            else:
                qy = ""
                for dy in self.dang_qian_dy_dian:
                    if abs(self.wan_jia_x - dy["x"]) < 40: qy = dy["ming_cheng"]; break
            if qy and qy != self.shang_ci_qy: self.shang_ci_qy = qy; self.xian_shi_zi_mu(qy)
            elif not qy: self.shang_ci_qy = ""
        elif self.dang_qian_cj == "fuben1":
            if "副本1" != self.shang_ci_qy: self.shang_ci_qy = "副本1"; self.xian_shi_zi_mu("副本1")
        elif self.dang_qian_cj == "fuben2":
            if "副本2" != self.shang_ci_qy: self.shang_ci_qy = "副本2"; self.xian_shi_zi_mu("副本2")

    def jian_ce_cai_dan(self):
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 6 and abs(self.wan_jia_x - 1200) < 40):
            if "under" in self.shu_ru_hc.lower():
                if self.yin_xiao_niu: self.yin_xiao_niu.play()
                self.xian_shi_zi_mu("彩蛋触发：牛逼！"); self.shu_ru_hc = ""
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 7 and abs(self.wan_jia_x - 1600) < 40):
            if "lisan" in self.shu_ru_hc.lower():
                if self.yin_xiao_sha: self.yin_xiao_sha.play()
                self.xian_shi_zi_mu("彩蛋触发：傻逼！"); self.shu_ru_hc = ""

    def geng_xin(self, shi_jian_dt):
        self.she_xiang_x = self.wan_jia_x - PING_MU_KD // 2
        if self.she_xiang_x < -500: self.she_xiang_x = -500
        if self.she_xiang_x > 2500: self.she_xiang_x = 2500
        if self.zi_mu_djs > 0:
            self.zi_mu_djs -= shi_jian_dt
            if self.zi_mu_djs <= 0: self.zi_mu_wb = ""
        if self.shu_ru_djs > 0:
            self.shu_ru_djs -= shi_jian_dt
            if self.shu_ru_djs <= 0: self.shu_ru_hc = ""
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 1 and self.wan_jia_x < GUA_JI_CHI_ZD):
            self.gua_ji_jss += shi_jian_dt
            if self.gua_ji_jss >= 1.0:
                self.gua_ji_jss -= 1.0
                jia_cheng = int(self.zhan_li * 0.0003 * self.lun_hui_jc)
                if jia_cheng < 1: jia_cheng = 1
                self.zhan_li += jia_cheng
        if self.dang_qian_cj == "fuben1":
            self.bei_lv_dan_jss += shi_jian_dt
            if self.bei_lv_dan_jss >= 3.0:
                self.bei_lv_dan_jss -= 3.0
                self.bei_lv_dan_lb.append({"x": 300 + random.randint(-50, 50), "y": DI_MIAN_Y - 15, "ming_cheng": "倍率丹", "lei_xing": "bei_lv"})
        self.jian_ce_qu_yu()
        self.jian_ce_cai_dan()
        if self.kong_ge_an_x and not self.lun_hui_yc:
            if time.time() - self.kong_ge_an_sj >= LUN_HUI_AN_MS:
                self.lun_hui_yc = True
                self.you_xi_zt = "lunhuixr"

    def hui_hua(self):
        # 核心重构：只清空动态绘制的 Group，而不是清空整个画布
        self.draw_group.clear()
        scale, offset_x, offset_y = self._huo_qu_suo_fang()

        self.draw_group.add(PushMatrix())
        self.draw_group.add(Translate(offset_x, offset_y, 0))
        self.draw_group.add(Scale(scale, scale, 1))

        self.draw_group.add(Color(0, 0, 0, 1))
        self.draw_group.add(Rectangle(pos=(0, 0), size=(PING_MU_KD, PING_MU_GD)))

        if self.you_xi_zt == "youxi":
            self.hui_hua_di_mian()
            self.hui_hua_dan_yao_dian()
            self.hui_hua_gua_ji_chi()
            self.hui_hua_yi_sheng_dan()
            self.hui_hua_wan_jia()
            self.hui_hua_zhuang_tai_lan()
            self.hui_hua_an_niu()
            self.hui_hua_di_bu_an_niu()
            self.hui_hua_zi_mu()
        elif self.you_xi_zt == "dituxz": self.hui_hua_di_tu_xz()
        elif self.you_xi_zt == "fubenxz": self.hui_hua_fu_ben_xz()
        elif self.you_xi_zt == "jiaocheng": self.hui_hua_jiao_cheng()
        elif self.you_xi_zt == "lunhuixr": self.hui_hua_lun_hui_que_ren()

        self.draw_group.add(PopMatrix())

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            scale, offset_x, offset_y = self._huo_qu_suo_fang()
            if scale <= 0: return True
            game_x = (touch.x - self.x - offset_x) / scale
            game_y = PING_MU_GD - (touch.y - self.y - offset_y) / scale

            an_ming = self._jian_ce_di_bu_an_niu(game_x, game_y)
            if an_ming is not None:
                touch.grab(self)
                self.an_xia_de_di_bu_an = an_ming
                self._di_bu_an_niu_an_x(an_ming)
                return True

            self.chu_li_shu_biao_dian_ji(game_x, game_y)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.an_xia_de_di_bu_an is not None:
                an_ming = self.an_xia_de_di_bu_an
                self.an_xia_de_di_bu_an = None
                self._di_bu_an_niu_tai_qi(an_ming)
            return True
        return super().on_touch_up(touch)

    def chu_li_shu_biao_dian_ji(self, x, y):
        if self.you_xi_zt == "youxi":
            an_niu = self.jian_ce_an_niu(x, y)
            if an_niu == "ditu": self.you_xi_zt = "dituxz"
            elif an_niu == "fuben": self.you_xi_zt = "fubenxz"
            elif an_niu == "guaji": self.gua_ji()
            elif an_niu == "huicheng": self.hui_cheng()
            elif an_niu == "jiaocheng": self.you_xi_zt = "jiaocheng"
            elif an_niu == "cundang": self.baocun(); self.xian_shi_zi_mu("游戏已保存！")
            elif an_niu == "jianpan": self.diao_chu_jian_pan()
        elif self.you_xi_zt == "dituxz":
            for i in range(10):
                hang = i // 5; lie = i % 5
                ax = 200 + lie * 160; ay = 150 + hang * 150
                if ax <= x <= ax + 140 and ay <= y <= ay + 80:
                    self.jin_ru_di_tu(i + 1); self.you_xi_zt = "youxi"; return
            if PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 500 <= y <= 540: self.you_xi_zt = "youxi"
        elif self.you_xi_zt == "fubenxz":
            if 300 <= x <= 550 and 150 <= y <= 250: self.jin_ru_fu_ben(1); self.you_xi_zt = "youxi"
            elif 650 <= x <= 900 and 150 <= y <= 250: self.jin_ru_fu_ben(2); self.you_xi_zt = "youxi"
            elif PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 500 <= y <= 540: self.you_xi_zt = "youxi"
        elif self.you_xi_zt == "jiaocheng":
            if PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 540 <= y <= 580: self.you_xi_zt = "youxi"
        elif self.you_xi_zt == "lunhuixr":
            if 350 <= x <= 470 and 380 <= y <= 420: self.lun_hui()
            elif 730 <= x <= 850 and 380 <= y <= 420:
                self.you_xi_zt = "youxi"; self.lun_hui_yc = False; self.kong_ge_an_x = False

    def chu_li_an_jian_an_x(self, jian):
        if jian == JIAN_KONG_GE:
            if not self.kong_ge_an_x:
                self.kong_ge_an_x = True; self.kong_ge_an_sj = time.time(); self.lun_hui_yc = False
        if self.you_xi_zt == "youxi":
            if 97 <= jian <= 122 or 65 <= jian <= 90:
                self.shu_ru_hc += chr(jian); self.shu_ru_djs = 3.0
                if len(self.shu_ru_hc) > 20: self.shu_ru_hc = self.shu_ru_hc[-20:]

    def chu_li_an_jian_tai_qi(self, jian):
        if self.you_xi_zt != "youxi": return
        if jian == JIAN_KONG_GE:
            an_shi_duan = time.time() - self.kong_ge_an_sj
            self.kong_ge_an_x = False
            if an_shi_duan < LUN_HUI_AN_MS:
                if self.dang_qian_cj == "map": self.sheng_cheng_dan_yao()
                elif self.dang_qian_cj == "fuben2": self.sheng_cheng_wu_ji_dan()
        elif jian == JIAN_Z: self.chi_suo_you_dan()
        elif jian == JIAN_X: self.chi_bei_lv_dan()
        elif jian == JIAN_Y:
            if self.you_xi_zt == "lunhuixr": self.lun_hui()
        elif jian == JIAN_N:
            if self.you_xi_zt == "lunhuixr":
                self.you_xi_zt = "youxi"; self.lun_hui_yc = False; self.kong_ge_an_x = False

    def _kivy_an_jian_an_x(self, *args):
        if len(args) < 2: return
        jian = args[1]; self.an_jian_zt[jian] = True; self.chu_li_an_jian_an_x(jian)

    def _kivy_an_jian_tai_qi(self, *args):
        if len(args) < 2: return
        jian = args[1]; self.an_jian_zt[jian] = False; self.chu_li_an_jian_tai_qi(jian)

    def _kivy_guan_bi(self, *args):
        self.baocun(); return False

    def baocun(self):
        cundang_data = {
            'zhan_li': self.zhan_li, 'lun_hui_cs': self.lun_hui_cs, 'diao_luo_bl': self.diao_luo_bl,
            'lun_hui_jc': self.lun_hui_jc, 'wan_jia_x': self.wan_jia_x, 'dang_qian_dt': self.dang_qian_dt,
            'dang_qian_cj': self.dang_qian_cj, 'di_tu_dan_yao': self.di_tu_dan_yao,
            'bei_lv_dan_lb': self.bei_lv_dan_lb, 'wu_ji_dan_lb': self.wu_ji_dan_lb,
            'bei_lv_dan_jss': self.bei_lv_dan_jss, 'gua_ji_jss': self.gua_ji_jss
        }
        try:
            with open(CUN_DANG_WJ, 'wb') as f: pickle.dump(cundang_data, f)
        except Exception: pass

    def jia_zai_cun_dang(self):
        if not os.path.exists(CUN_DANG_WJ): return
        try:
            with open(CUN_DANG_WJ, 'rb') as f: data = pickle.load(f)
            self.zhan_li = data.get('zhan_li', 3000); self.lun_hui_cs = data.get('lun_hui_cs', 0)
            self.diao_luo_bl = data.get('diao_luo_bl', 1); self.lun_hui_jc = data.get('lun_hui_jc', 1.0)
            self.wan_jia_x = data.get('wan_jia_x', DAN_YAO_KS); self.dang_qian_dt = data.get('dang_qian_dt', 1)
            self.dang_qian_cj = data.get('dang_qian_cj', 'map')
            self.di_tu_dan_yao = data.get('di_tu_dan_yao', [[] for _ in range(10)])
            self.bei_lv_dan_lb = data.get('bei_lv_dan_lb', []); self.wu_ji_dan_lb = data.get('wu_ji_dan_lb', [])
            self.bei_lv_dan_jss = data.get('bei_lv_dan_jss', 0); self.gua_ji_jss = data.get('gua_ji_jss', 0)
            self.shang_ci_qy = ""; self.zi_mu_wb = ""; self.zi_mu_djs = 0; self.shu_ru_hc = ""; self.shu_ru_djs = 0
        except Exception: pass

    def yun_xing(self):
        Window.bind(on_key_down=self._kivy_an_jian_an_x)
        Window.bind(on_key_up=self._kivy_an_jian_tai_qi)
        Window.bind(on_request_close=self._kivy_guan_bi)
        self._ding_shi_qi = Clock.schedule_interval(self.mei_zhen_geng_xin, 1.0 / ZHEN_LV)

    def mei_zhen_geng_xin(self, shi_jian_dt):
        if self.you_xi_zt == "youxi":
            if self.an_jian_zt.get(JIAN_LEFT): self.wan_jia_x -= YD_SU_DU
            if self.an_jian_zt.get(JIAN_RIGHT): self.wan_jia_x += YD_SU_DU
            if self.dang_qian_cj == "map":
                if self.wan_jia_x < -450: self.wan_jia_x = -450
                if self.wan_jia_x > 2450: self.wan_jia_x = 2450
            else:
                if self.wan_jia_x < -450: self.wan_jia_x = -450
                if self.wan_jia_x > 1450: self.wan_jia_x = 1450
        self.geng_xin(shi_jian_dt)
        self.hui_hua()

# ==================== Kivy应用主类 ====================
class ChiDanXiuXianApp(App):
    def build(self):
        self.title = "吃丹修仙-under"
        root = FloatLayout()
        self.you_xi = YouXi()
        root.add_widget(self.you_xi)
        self.you_xi.yun_xing()
        return root

    # 根据大佬建议：修复安卓切后台后再切回来，导致长按误触发轮回的Bug
    def on_pause(self):
        if hasattr(self, 'you_xi'):
            self.you_xi.kong_ge_an_x = False
            self.you_xi.an_jian_zt.clear()
        return True

    def on_resume(self):
        pass

if __name__ == "__main__":
    ChiDanXiuXianApp().run()
