# -*- coding: utf-8 -*-
"""
横向2D吃丹修仙游戏（带存档功能）—— Kivy移植版
主要功能：
1. 10个主地图，每个地图有10种常规丹药生成点
2. 2个副本地图（倍率丹副本、无极魔丹副本）
3. 挂机池自动增加战力
4. 轮回系统（最多20次）
5. 彩蛋系统
6. 存档/读档（退出自动保存，也可手动存档）

"""

import os
# ---- 关闭 Kivy 控制台日志（必须在任何 kivy 模块导入前设置）----
os.environ['KIVY_NO_CONSOLELOG'] = '1'

import random
import time
import pickle

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.core.text import Label as CoreLabel, LabelBase
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
# ---- 虚拟键盘弹窗所需控件 ----
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

# ==================== 常量定义 ====================
# 屏幕尺寸
PING_MU_KD = 1200  # 屏幕宽度
PING_MU_GD = 600   # 屏幕高度

# 地面高度
DI_MIAN_Y = 400

# 丹药生成点间隔
DAN_YAO_JG = 200
# 第一个丹药生成点x坐标
DAN_YAO_KS = 200

# 玩家移动速度
YD_SU_DU = 5

# 帧率
ZHEN_LV = 60

# 挂机池范围（地图1中x<200为挂机池）
GUA_JI_CHI_ZD = 200

# 长按空格触发轮回的秒数
LUN_HUI_AN_MS = 10

# 存档文件名
CUN_DANG_WJ = "cundang.pkl"

# 轮回后基础战力（原来1000，现改为5000）
LUN_HUI_JI_CHU_ZL = 5000

# ==================== 按键码常量（替代原来pygame的按键常量） ====================
JIAN_KONG_GE = 32      # 对应原 pygame.K_SPACE
JIAN_Z = 122           # 对应原 pygame.K_z
JIAN_X = 120           # 对应原 pygame.K_x
JIAN_Y = 121           # 对应原 pygame.K_y
JIAN_N = 110           # 对应原 pygame.K_n
JIAN_LEFT = 276        # 对应原 pygame.K_LEFT
JIAN_RIGHT = 275       # 对应原 pygame.K_RIGHT

# 颜色定义
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

# ==================== 中文数字单位 ====================
DAN_WEI_LB = ['', '万', '亿', '兆', '京', '垓', '秭', '穰', '沟', '涧',
              '正', '载', '极', '恒河沙', '阿僧祇', '那由他', '不可思议',
              '无量', '大数', '无敌']


def shu_zi_zhuan_huan(shu_zi):
    """将大数字转换为中文单位显示"""
    if shu_zi < 10000:
        return str(int(shu_zi))
    for i in range(len(DAN_WEI_LB) - 1, 0, -1):
        ji_shu = 10 ** (4 * i)
        if shu_zi >= ji_shu:
            zhi = shu_zi / ji_shu
            return f"{zhi:.4f}{DAN_WEI_LB[i]}"
    return str(shu_zi)


def jie_xi_dan_wei(wen_ben):
    """解析中文单位数字（用于轮回所需战力）"""
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


# ==================== 轮回所需战力列表 ====================
LUN_HUI_SL_LB = [
    "500涧", "46.5正", "4.9载", "5840载", "21极", "778极",
    "2.96恒河沙", "177恒河沙", "一阿僧祇", "70阿僧祇",
    "4650阿僧祇", "31那由他", "2200那由他", "16不可思议",
    "1180不可思议", "8无量", "700无量", "7大数",
    "120大数", "9999大数"
]

# 将轮回所需战力转换为整数
LUN_HUI_SL_ZS = [jie_xi_dan_wei(s) for s in LUN_HUI_SL_LB]


# ==================== 计算丹药加成 ====================
def ji_suan_dan_yao_jc(di_tu_bian_hao, jie_shu):
    """
    计算丹药加成战力
    地图n的m阶丹加成 = 10 × 5^(m-1) × 5^(9×(n-1)) × 20^(n-1)
    """
    jia_cheng = 10
    jia_cheng *= 5 ** (jie_shu - 1)
    if di_tu_bian_hao > 1:
        jia_cheng *= 5 ** (9 * (di_tu_bian_hao - 1))
        jia_cheng *= 20 ** (di_tu_bian_hao - 1)
    return jia_cheng


# ==================== 字体与颜色工具函数 ====================
def zhu_ce_zhong_wen_zi_ti():
    """
    尝试注册系统中文字体，返回字体名称；找不到则返回None。
    """
    zi_ti_lu_jing_lb = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for lu_jing in zi_ti_lu_jing_lb:
        if os.path.exists(lu_jing):
            try:
                LabelBase.register(name="ZhongWenZiTi", fn_regular=lu_jing)
                return "ZhongWenZiTi"
            except Exception:
                continue
    return None


ZHONG_WEN_ZT = zhu_ce_zhong_wen_zi_ti()
ZI_TI_MING = ZHONG_WEN_ZT if ZHONG_WEN_ZT else "Roboto"


def zhuan_yan_se(yan_se):
    """把0-255的颜色元组转为Kivy需要的0-1浮点RGBA元组"""
    if len(yan_se) == 3:
        return (yan_se[0] / 255.0, yan_se[1] / 255.0, yan_se[2] / 255.0, 1.0)
    return (yan_se[0] / 255.0, yan_se[1] / 255.0,
            yan_se[2] / 255.0, yan_se[3] / 255.0)


# ==================== 游戏主类 ====================
class YouXi(Widget):
    """游戏主控件"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.size = (PING_MU_KD, PING_MU_GD)

        # 字号
        self.zi_ti_da = 30
        self.zi_ti_zhong = 20
        self.zi_ti_xiao = 14
        self.zi_ti_jiao_cheng = 16

        # 加载玩家图片
        try:
            self.wan_jia_tp = CoreImage("雨蚊捞屎.png").texture
        except Exception:
            self.wan_jia_tp = None

        # 背景音乐
        self.yin_yue = None
        try:
            self.yin_yue = SoundLoader.load("音乐.mp3")
            if self.yin_yue:
                self.yin_yue.loop = True
                self.yin_yue.volume = 0.3
                self.yin_yue.play()
        except Exception:
            self.yin_yue = None

        # 加载音效
        try:
            self.yin_xiao_niu = SoundLoader.load("牛逼.wav")
        except Exception:
            self.yin_xiao_niu = None
        try:
            self.yin_xiao_sha = SoundLoader.load("傻逼.wav")
        except Exception:
            self.yin_xiao_sha = None

        # ==================== 玩家属性 ====================
        self.zhan_li = 3000       # 初始战力
        self.lun_hui_cs = 0       # 轮回次数
        self.diao_luo_bl = 1      # 掉落倍率
        self.lun_hui_jc = 1.0     # 轮回加成乘数

        # 玩家位置
        self.wan_jia_x = DAN_YAO_KS
        self.wan_jia_y = DI_MIAN_Y - 50

        # ==================== 场景状态 ====================
        self.dang_qian_dt = 1
        self.dang_qian_cj = "map"
        self.you_xi_zt = "youxi"

        # 摄像机偏移
        self.she_xiang_x = 0

        # ==================== 丹药存储 ====================
        self.di_tu_dan_yao = [[] for _ in range(10)]
        self.bei_lv_dan_lb = []
        self.wu_ji_dan_lb = []

        # ==================== 计时器 ====================
        self.bei_lv_dan_jss = 0
        self.gua_ji_jss = 0

        # ==================== 空格键状态 ====================
        self.kong_ge_an_x = False
        self.kong_ge_an_sj = 0
        self.lun_hui_yc = False

        # ==================== 字幕系统 ====================
        self.zi_mu_wb = ""
        self.zi_mu_djs = 0

        # ==================== 输入检测（彩蛋） ====================
        self.shu_ru_hc = ""
        self.shu_ru_djs = 0

        # ==================== 区域检测 ====================
        self.shang_ci_qy = ""

        # ==================== Kivy专用新增变量 ====================
        self.an_jian_zt = {}          # 按键按下状态字典（用于左右移动）
        self._wen_ben_huan_cun = {}   # 文字纹理缓存
        self._ding_shi_qi = None      # 帧循环定时器
        # ---- 新增：当前按下的底部大按钮名称（避免手指滑出后抬起状态残留）----
        self.an_xia_de_di_bu_an = None
        # ---- 新增：虚拟键盘弹窗引用（防止被垃圾回收）----
        self.jian_pan_tan_chuang = None

        # 尝试加载存档
        self.jia_zai_cun_dang()

        # 当前地图的丹药生成点信息
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(self.dang_qian_dt)

    # ==================== 绘制辅助函数 ====================
    def _huo_qu_wen_ben_wen_li(self, wen_ben, zi_ti, yan_se):
        """获取（并缓存）文字纹理"""
        guan_jian = (wen_ben, zi_ti, yan_se)
        if guan_jian not in self._wen_ben_huan_cun:
            cl = CoreLabel(text=wen_ben, font_size=zi_ti,
                           font_name=ZI_TI_MING,
                           color=zhuan_yan_se(yan_se))
            cl.refresh()
            self._wen_ben_huan_cun[guan_jian] = cl
        return self._wen_ben_huan_cun[guan_jian].texture

    def _hua_wen_ben(self, wen_ben, x, y, zi_ti, yan_se, ju_zhong=False):
        """在画布上绘制文字（y为文字顶部，pygame风格坐标）"""
        tex = self._huo_qu_wen_ben_wen_li(wen_ben, zi_ti, yan_se)
        kuan = tex.width
        if ju_zhong:
            x = x - kuan // 2
        ky = PING_MU_GD - y - tex.height
        Color(1, 1, 1, 1)
        Rectangle(texture=tex, pos=(x, ky), size=tex.size)
        return kuan

    def _hua_ju_xing(self, yan_se, x, y, kuan, gao, bian_kuan=0, bian_yan_se=None):
        """绘制矩形（x,y为左上角，pygame风格坐标）"""
        ky = PING_MU_GD - y - gao
        Color(*zhuan_yan_se(yan_se))
        Rectangle(pos=(x, ky), size=(kuan, gao))
        if bian_kuan > 0:
            Color(*zhuan_yan_se(bian_yan_se if bian_yan_se else YS_BAI))
            Line(rectangle=(x, ky, kuan, gao), width=bian_kuan)

    def _hua_yuan(self, yan_se, cx, cy, ban_jing):
        """绘制实心圆"""
        Color(*zhuan_yan_se(yan_se))
        Ellipse(pos=(cx - ban_jing, PING_MU_GD - cy - ban_jing),
                size=(ban_jing * 2, ban_jing * 2))

    def _hua_xian(self, yan_se, x1, y1, x2, y2, kuan=1):
        """绘制线段"""
        Color(*zhuan_yan_se(yan_se))
        Line(points=[x1, PING_MU_GD - y1, x2, PING_MU_GD - y2], width=kuan)

    # ==================== 原有逻辑函数 ====================
    def sheng_cheng_dy_dian(self, di_tu_bian_hao):
        """生成指定地图的10个丹药生成点信息"""
        dy_dian = []
        for jie_shu in range(1, 11):
            x = DAN_YAO_KS + (jie_shu - 1) * DAN_YAO_JG
            jia_cheng = ji_suan_dan_yao_jc(di_tu_bian_hao, jie_shu)
            ming_cheng = f"地图{di_tu_bian_hao}的{jie_shu}阶丹"
            dy_dian.append({
                "x": x,
                "jie_shu": jie_shu,
                "jia_cheng": jia_cheng,
                "ming_cheng": ming_cheng
            })
        return dy_dian

    def xian_shi_zi_mu(self, wen_ben):
        """显示字幕3秒"""
        self.zi_mu_wb = wen_ben
        self.zi_mu_djs = 3.0

    def jian_ce_an_niu(self, shu_biao_x, shu_biao_y):
        """检测左侧按钮点击（新增“键盘”按钮）"""
        an_niu_wz = [
            ("ditu", 10, 100, 80, 35),
            ("fuben", 10, 145, 80, 35),
            ("guaji", 10, 190, 80, 35),
            ("huicheng", 10, 235, 80, 35),
            ("jiaocheng", 10, 280, 80, 35),
            ("cundang", 10, 325, 80, 35),
            ("jianpan", 10, 370, 80, 35),   # 新增：键盘按钮
        ]
        for ming, ax, ay, ak, ag in an_niu_wz:
            if ax <= shu_biao_x <= ax + ak and ay <= shu_biao_y <= ay + ag:
                return ming
        return None

    # -------------------- 新增：底部大按钮相关 --------------------
    def _di_bu_an_niu_wz_lb(self):
        """
        返回底部大按钮的位置列表
        格式：(按钮名, x, y, 宽, 高, 颜色)
        说明：左/右在左下角，空格/z/x在右下角
        """
        return [
            ("zuo",    20, 510, 160, 70, YS_LAN),      # 左
            ("you",   200, 510, 160, 70, YS_LAN),      # 右
            ("kongge", 700, 510, 200, 70, YS_LV),      # 空格
            ("z",      910, 510, 130, 70, YS_CHENG),   # z
            ("x",     1050, 510, 130, 70, YS_CHENG),   # x
        ]

    def _jian_ce_di_bu_an_niu(self, x, y):
        """检测是否点在底部大按钮上，返回按钮名或None"""
        if self.you_xi_zt != "youxi":
            return None
        for ming, ax, ay, ak, ag, ys in self._di_bu_an_niu_wz_lb():
            if ax <= x <= ax + ak and ay <= y <= ay + ag:
                return ming
        return None

    def _di_bu_an_niu_an_x(self, ming):
        """底部大按钮：按下处理"""
        if ming == "zuo":
            self.an_jian_zt[JIAN_LEFT] = True
        elif ming == "you":
            self.an_jian_zt[JIAN_RIGHT] = True
        elif ming == "kongge":
            # 空格按下：复用键盘按下逻辑（含长按轮回计时）
            self.chu_li_an_jian_an_x(JIAN_KONG_GE)
        elif ming == "z":
            self.an_jian_zt[JIAN_Z] = True
        elif ming == "x":
            self.an_jian_zt[JIAN_X] = True

    def _di_bu_an_niu_tai_qi(self, ming):
        """底部大按钮：抬起处理"""
        if ming == "zuo":
            self.an_jian_zt[JIAN_LEFT] = False
        elif ming == "you":
            self.an_jian_zt[JIAN_RIGHT] = False
        elif ming == "kongge":
            # 空格抬起：复用键盘抬起逻辑（生成丹药 / 无极魔丹）
            self.chu_li_an_jian_tai_qi(JIAN_KONG_GE)
        elif ming == "z":
            self.an_jian_zt[JIAN_Z] = False
            self.chu_li_an_jian_tai_qi(JIAN_Z)
        elif ming == "x":
            self.an_jian_zt[JIAN_X] = False
            self.chu_li_an_jian_tai_qi(JIAN_X)

    def hui_hua_di_bu_an_niu(self):
        """绘制底部大按钮（左/右/空格/z/x）"""
        ming_zi_lb = {
            "zuo": "左",
            "you": "右",
            "kongge": "空格",
            "z": "z",
            "x": "x",
        }
        for ming, ax, ay, ak, ag, ys in self._di_bu_an_niu_wz_lb():
            # 按下时颜色更亮，做简单的视觉反馈
            an_xia = False
            if ming == "zuo" and self.an_jian_zt.get(JIAN_LEFT):
                an_xia = True
            elif ming == "you" and self.an_jian_zt.get(JIAN_RIGHT):
                an_xia = True
            elif ming == "kongge" and self.kong_ge_an_x:
                an_xia = True
            elif ming == "z" and self.an_jian_zt.get(JIAN_Z):
                an_xia = True
            elif ming == "x" and self.an_jian_zt.get(JIAN_X):
                an_xia = True

            hua_ys = YS_JIN if an_xia else ys
            self._hua_ju_xing(hua_ys, ax, ay, ak, ag, 3, YS_BAI)
            self._hua_wen_ben(ming_zi_lb[ming],
                              ax + ak // 2, ay + (ag - 30) // 2,
                              self.zi_ti_da, YS_BAI, ju_zhong=True)

    #虚拟键盘弹窗
    def diao_chu_jian_pan(self):
        """
        弹出虚拟键盘输入框
        用于在游戏内输入字母（触发彩蛋）；点击确定后把输入的字母逐个
        送入原有的 chu_li_an_jian_an_x，逻辑与键盘输入完全一致。

        【修复说明】
        - Kivy 默认 Roboto 字体不含中文，会显示成方框
        - 给 TextInput / Button / Popup 标题都显式指定中文字体 ZI_TI_MING
        """
        # 布局容器
        bu_ju = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # 输入框：设置中文字体，避免出现豆腐块
        shu_ru_kuang = TextInput(
            text='',
            multiline=False,
            font_size=24,
            font_name=ZI_TI_MING,     # ★ 关键：使用中文字体
        )
        bu_ju.add_widget(shu_ru_kuang)

        # 按钮行
        an_niu_bu_ju = BoxLayout(size_hint_y=None, height=60, spacing=10)

        que_ding_an = Button(
            text='确定',
            font_size=24,
            font_name=ZI_TI_MING,     # ★ 关键：使用中文字体
        )
        qu_xiao_an = Button(
            text='取消',
            font_size=24,
            font_name=ZI_TI_MING,     # ★ 关键：使用中文字体
        )
        an_niu_bu_ju.add_widget(que_ding_an)
        an_niu_bu_ju.add_widget(qu_xiao_an)
        bu_ju.add_widget(an_niu_bu_ju)

        # 弹窗
        tan_chuang = Popup(
            title='键盘输入（用于触发彩蛋）',
            content=bu_ju,
            size_hint=(0.45, 0.35),
            title_size=20,            # 标题字号
        )
        # ★ 关键：设置弹窗标题的中文字体，否则标题也会显示成方框
        try:
            tan_chuang.title_font = ZI_TI_MING
        except Exception:
            # 某些 Kivy 版本属性名为 title_font，若不存在则忽略
            pass

        self.jian_pan_tan_chuang = tan_chuang

        def _que_ding(*args):
            """确定：把输入内容当作按键依次处理"""
            wen_ben = shu_ru_kuang.text
            for zi_fu in wen_ben:
                if zi_fu.isalpha():
                    # 统一转为小写字母，送入原有按键处理
                    self.chu_li_an_jian_an_x(ord(zi_fu.lower()))
            tan_chuang.dismiss()

        que_ding_an.bind(on_release=_que_ding)
        qu_xiao_an.bind(on_release=lambda *a: tan_chuang.dismiss())
        tan_chuang.bind(on_dismiss=lambda *a: setattr(
            self, 'jian_pan_tan_chuang', None))

        tan_chuang.open()
        shu_ru_kuang.focus = True

    # -------------------- 绘制相关函数 --------------------
    def hui_hua_an_niu(self):
        """绘制左侧按钮（新增“键盘”）"""
        an_niu_lb = [
            ("地图", 10, 100, 80, 35, YS_LAN),
            ("副本", 10, 145, 80, 35, YS_ZI),
            ("挂机", 10, 190, 80, 35, YS_LV),
            ("回城", 10, 235, 80, 35, YS_CHENG),
            ("教程", 10, 280, 80, 35, YS_HUI),
            ("存档", 10, 325, 80, 35, YS_JIN),
            ("键盘", 10, 370, 80, 35, YS_QIAN_LAN),   # 新增
        ]
        for ming, ax, ay, ak, ag, ys in an_niu_lb:
            self._hua_ju_xing(ys, ax, ay, ak, ag, 2, YS_BAI)
            self._hua_wen_ben(ming, ax + 15, ay + 8, self.zi_ti_xiao, YS_BAI)

    def hui_hua_zhuang_tai_lan(self):
        """绘制左上角状态栏"""
        self._hua_wen_ben(f"战力: {shu_zi_zhuan_huan(self.zhan_li)}",
                          100, 10, self.zi_ti_zhong, YS_JIN)
        self._hua_wen_ben(f"轮回数: {self.lun_hui_cs}",
                          100, 40, self.zi_ti_zhong, YS_BAI)
        self._hua_wen_ben(f"掉落倍率: {self.diao_luo_bl}",
                          100, 70, self.zi_ti_zhong, YS_BAI)

    def hui_hua_zi_mu(self):
        """绘制字幕"""
        if self.zi_mu_djs > 0 and self.zi_mu_wb:
            self._hua_wen_ben(self.zi_mu_wb,
                              PING_MU_KD // 2, 120,
                              self.zi_ti_da, YS_HUANG, ju_zhong=True)

    def hui_hua_di_mian(self):
        """绘制地面横线"""
        self._hua_xian(YS_TU, 0, DI_MIAN_Y, PING_MU_KD, DI_MIAN_Y, 3)

    def hui_hua_dan_yao_dian(self):
        """绘制当前地图的丹药生成点"""
        if self.dang_qian_cj != "map":
            return
        for dy in self.dang_qian_dy_dian:
            sx = dy["x"] - self.she_xiang_x
            if -100 <= sx <= PING_MU_KD + 100:
                self._hua_yuan(YS_HONG, sx, DI_MIAN_Y - 5, 8)
                self._hua_wen_ben(dy["ming_cheng"], sx, DI_MIAN_Y - 40,
                                  self.zi_ti_xiao, YS_BAI, ju_zhong=True)

    def hui_hua_yi_sheng_dan(self):
        """绘制已生成的丹药"""
        if self.dang_qian_cj == "map":
            dy_lb = self.di_tu_dan_yao[self.dang_qian_dt - 1]
            for i, dy in enumerate(dy_lb):
                sx = dy["x"] + (i % 5) * 8 - 16 - self.she_xiang_x
                sy = DI_MIAN_Y - 15 - (i // 5) * 10
                if -50 <= sx <= PING_MU_KD + 50:
                    if "无极" in dy["ming_cheng"]:
                        self._hua_yuan(YS_ZI, sx, sy, 6)
                    else:
                        self._hua_yuan(YS_LV, sx, sy, 6)

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
        """绘制玩家"""
        sx = self.wan_jia_x - self.she_xiang_x
        if self.wan_jia_tp is not None:
            Color(1, 1, 1, 1)
            Rectangle(texture=self.wan_jia_tp,
                      pos=(sx, PING_MU_GD - self.wan_jia_y - 50),
                      size=(40, 50))
        else:
            self._hua_ju_xing(YS_LAN, sx, self.wan_jia_y, 40, 50)

    def hui_hua_gua_ji_chi(self):
        """绘制挂机池标识"""
        if self.dang_qian_cj == "map" and self.dang_qian_dt == 1:
            for x in range(-400, GUA_JI_CHI_ZD, 50):
                sx = x - self.she_xiang_x
                if -50 <= sx <= PING_MU_KD + 50:
                    self._hua_ju_xing(YS_QIAN_LAN, sx, DI_MIAN_Y - 20, 40, 20)
            sx = 0 - self.she_xiang_x
            if -100 <= sx <= PING_MU_KD + 100:
                self._hua_wen_ben("挂机池", sx, DI_MIAN_Y - 50,
                                  self.zi_ti_xiao, YS_QIAN_LAN, ju_zhong=True)

    def hui_hua_di_tu_xz(self):
        """绘制地图选择界面"""
        self._hua_ju_xing((0, 0, 0, 200), 0, 0, PING_MU_KD, PING_MU_GD)

        self._hua_wen_ben("选择地图", PING_MU_KD // 2, 50,
                          self.zi_ti_da, YS_BAI, ju_zhong=True)

        for i in range(10):
            hang = i // 5
            lie = i % 5
            ax = 200 + lie * 160
            ay = 150 + hang * 150
            self._hua_ju_xing(YS_LAN, ax, ay, 140, 80, 2, YS_BAI)
            self._hua_wen_ben(f"地图{i + 1}", ax + 70, ay + 25,
                              self.zi_ti_zhong, YS_BAI, ju_zhong=True)

        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 500, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 510,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_fu_ben_xz(self):
        """绘制副本选择界面"""
        self._hua_ju_xing((0, 0, 0, 200), 0, 0, PING_MU_KD, PING_MU_GD)

        self._hua_wen_ben("选择副本", PING_MU_KD // 2, 50,
                          self.zi_ti_da, YS_BAI, ju_zhong=True)

        self._hua_ju_xing(YS_ZI, 300, 150, 250, 100, 2, YS_BAI)
        self._hua_wen_ben("副本1（倍率丹）", 425, 185,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

        self._hua_ju_xing(YS_ZI, 650, 150, 250, 100, 2, YS_BAI)
        self._hua_wen_ben("副本2（无极魔丹）", 775, 185,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 500, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 510,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_jiao_cheng(self):
        """绘制教程界面（内容已更新）"""
        self._hua_ju_xing((0, 0, 0, 220), 0, 0, PING_MU_KD, PING_MU_GD)

        self._hua_wen_ben("游戏教程", PING_MU_KD // 2, 15,
                          self.zi_ti_da, YS_HUANG, ju_zhong=True)

        # ---- 教程内容（本次修改：更新轮回战力，新增界面按钮说明）----
        jiao_cheng_wb = [
            "【基本规则】",
            "1. 10个主地图，每个地图有10种常规丹药生成点",
            "2. 空格键生成丹药（松开时），数量=掉落倍率",
            "3. Z键吃掉所有常规丹药加战力（松开时）",
            "4. 地图1一阶丹+10战力，每阶×5，跨地图×20",
            "5. 生成丹药需战力≥丹药加成×300",
            "6. 挂机池在地图1一阶丹左侧，每秒+0.03%战力",
            "",
            "【副本】",
            "7. 副本1：每3秒生成倍率丹，X键吃，掉落倍率+1",
            "8. 副本2：空格生成无极魔丹，加战力0.01%/颗",
            "",
            "【轮回】",
            "9. 长按空格10秒触发轮回询问",
            "10. 轮回后战力变5000，加成×1.5，最多20次",
            "",
            "【界面按钮】",
            "左下角：“左”“右”与键盘左右箭头相同（按住持续移动）",
            "右下角：“空格”“z”“x”与键盘对应按键相同",
            "左侧“键盘”按钮：弹出输入框，用于输入文字触发彩蛋",
            "",
            "【单位】",
            "万=10^4, 亿=10^8, 兆=10^12...无敌=10^76",
            "",
            "【彩蛋】",
            "地图6六阶丹区输入under，地图7八阶丹区输入lisan",
            "",
            "【存档】",
            "游戏退出时自动保存，也可点击左侧“存档”按钮手动保存"
        ]

        for i, hang in enumerate(jiao_cheng_wb):
            y = 55 + i * 22
            self._hua_wen_ben(hang, 50, y, self.zi_ti_jiao_cheng, YS_BAI)

        self._hua_ju_xing(YS_HUI, PING_MU_KD // 2 - 50, 555, 100, 40, 2, YS_BAI)
        self._hua_wen_ben("返回", PING_MU_KD // 2, 563,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    def hui_hua_lun_hui_que_ren(self):
        """绘制轮回确认对话框"""
        self._hua_ju_xing((0, 0, 0, 180), 0, 0, PING_MU_KD, PING_MU_GD)

        self._hua_ju_xing(YS_HUI, 250, 180, 700, 240, 3, YS_JIN)

        suo_xu = LUN_HUI_SL_ZS[self.lun_hui_cs] if self.lun_hui_cs < 20 else 0
        self._hua_wen_ben("是否轮回？", PING_MU_KD // 2, 200,
                          self.zi_ti_da, YS_HONG, ju_zhong=True)

        self._hua_wen_ben(f"当前轮回数: {self.lun_hui_cs}",
                          300, 250, self.zi_ti_zhong, YS_BAI)

        self._hua_wen_ben(f"所需战力: {shu_zi_zhuan_huan(suo_xu)}",
                          300, 280, self.zi_ti_zhong, YS_BAI)

        self._hua_wen_ben(f"当前战力: {shu_zi_zhuan_huan(self.zhan_li)}",
                          300, 310, self.zi_ti_zhong, YS_BAI)

        if self.zhan_li >= suo_xu:
            self._hua_wen_ben("√ 战力充足，可以轮回！",
                              300, 340, self.zi_ti_zhong, YS_LV)
        else:
            self._hua_wen_ben("× 战力不足，无法轮回！",
                              300, 340, self.zi_ti_zhong, YS_HONG)

        self._hua_ju_xing(YS_LV, 350, 380, 120, 40, 2, YS_BAI)
        self._hua_wen_ben("确认(Y)", 410, 390,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

        self._hua_ju_xing(YS_HONG, 730, 380, 120, 40, 2, YS_BAI)
        self._hua_wen_ben("取消(N)", 790, 390,
                          self.zi_ti_zhong, YS_BAI, ju_zhong=True)

    # ==================== 场景切换 ====================
    def jin_ru_di_tu(self, di_tu_bian_hao):
        """进入指定地图"""
        self.dang_qian_dt = di_tu_bian_hao
        self.dang_qian_cj = "map"
        self.wan_jia_x = DAN_YAO_KS
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(di_tu_bian_hao)
        self.shang_ci_qy = ""
        self.xian_shi_zi_mu(f"进入地图{di_tu_bian_hao}")

    def jin_ru_fu_ben(self, fu_ben_bian_hao):
        """进入指定副本"""
        if fu_ben_bian_hao == 1:
            self.dang_qian_cj = "fuben1"
            self.wan_jia_x = 200
            self.xian_shi_zi_mu("进入副本1（倍率丹）")
        elif fu_ben_bian_hao == 2:
            self.dang_qian_cj = "fuben2"
            self.wan_jia_x = 200
            self.xian_shi_zi_mu("进入副本2（无极魔丹）")
        self.shang_ci_qy = ""

    def gua_ji(self):
        """进入挂机池"""
        self.dang_qian_dt = 1
        self.dang_qian_cj = "map"
        self.wan_jia_x = 100
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(1)
        self.shang_ci_qy = ""
        self.xian_shi_zi_mu("进入挂机池")

    def hui_cheng(self):
        """回城（地图1一阶丹处）"""
        self.dang_qian_dt = 1
        self.dang_qian_cj = "map"
        self.wan_jia_x = DAN_YAO_KS
        self.dang_qian_dy_dian = self.sheng_cheng_dy_dian(1)
        self.shang_ci_qy = ""
        self.xian_shi_zi_mu("回城")

    # ==================== 丹药生成/食用 ====================
    def sheng_cheng_dan_yao(self):
        """在地图丹药生成点生成丹药"""
        if self.dang_qian_cj != "map":
            return

        for dy in self.dang_qian_dy_dian:
            if abs(self.wan_jia_x - dy["x"]) < 40:
                suo_xu = dy["jia_cheng"] * 300
                if self.zhan_li >= suo_xu:
                    for i in range(self.diao_luo_bl):
                        self.di_tu_dan_yao[self.dang_qian_dt - 1].append({
                            "x": dy["x"] + random.randint(-20, 20),
                            "y": DI_MIAN_Y - 15,
                            "ming_cheng": dy["ming_cheng"],
                            "jia_cheng": dy["jia_cheng"],
                            "lei_xing": "chang_gui"
                        })
                    self.xian_shi_zi_mu(f"生成{self.diao_luo_bl}个{dy['ming_cheng']}")
                else:
                    self.xian_shi_zi_mu(
                        f"战力不足！需要{shu_zi_zhuan_huan(suo_xu)}战力")
                return

        self.xian_shi_zi_mu("不在丹药生成点附近")

    def sheng_cheng_wu_ji_dan(self):
        """在副本2生成无极魔丹"""
        if self.dang_qian_cj != "fuben2":
            return

        gai_lv = random.random()
        if gai_lv < 0.60:
            shu_liang = 1
        elif gai_lv < 0.90:
            shu_liang = 3
        elif gai_lv < 0.9999:
            shu_liang = 5
        else:
            shu_liang = 20

        for i in range(shu_liang):
            self.wu_ji_dan_lb.append({
                "x": self.wan_jia_x + random.randint(-30, 30),
                "y": DI_MIAN_Y - 15,
                "ming_cheng": "无极魔丹",
                "jia_cheng": 0,
                "lei_xing": "wu_ji"
            })
        self.xian_shi_zi_mu(f"生成{shu_liang}颗无极魔丹！")

    def chi_suo_you_dan(self):
        """吃掉所有常规丹药"""
        chi_le = 0
        zong_jia = 0

        if self.dang_qian_cj == "map":
            dy_lb = self.di_tu_dan_yao[self.dang_qian_dt - 1]
            for dy in dy_lb:
                jia_cheng = int(dy["jia_cheng"] * self.lun_hui_jc)
                self.zhan_li += jia_cheng
                zong_jia += jia_cheng
                chi_le += 1
            dy_lb.clear()

        elif self.dang_qian_cj == "fuben2":
            for dy in self.wu_ji_dan_lb:
                jia_cheng = int(self.zhan_li * 0.0001 * self.lun_hui_jc)
                if jia_cheng < 1:
                    jia_cheng = 1
                self.zhan_li += jia_cheng
                zong_jia += jia_cheng
                chi_le += 1
            self.wu_ji_dan_lb.clear()

        if chi_le > 0:
            self.xian_shi_zi_mu(f"吃掉{chi_le}颗丹药，战力+{shu_zi_zhuan_huan(zong_jia)}")
        else:
            self.xian_shi_zi_mu("没有可吃的丹药")

    def chi_bei_lv_dan(self):
        """在副本1吃一个倍率丹"""
        if self.dang_qian_cj != "fuben1":
            return
        if len(self.bei_lv_dan_lb) > 0:
            self.bei_lv_dan_lb.pop(0)
            self.diao_luo_bl += 1
            self.xian_shi_zi_mu(f"吃倍率丹！掉落倍率+1，当前{self.diao_luo_bl}")
        else:
            self.xian_shi_zi_mu("没有倍率丹可吃")

    def lun_hui(self):
        """执行轮回（本次修改：轮回后基础战力改为 5000）"""
        suo_xu = LUN_HUI_SL_ZS[self.lun_hui_cs] if self.lun_hui_cs < 20 else 0
        if self.zhan_li >= suo_xu and self.lun_hui_cs < 20:
            # ---- 修改：基础战力从 1000 改为 5000 ----
            self.zhan_li = LUN_HUI_JI_CHU_ZL
            self.lun_hui_cs += 1
            self.lun_hui_jc *= 1.5
            self.xian_shi_zi_mu(f"轮回成功！第{self.lun_hui_cs}次轮回，加成×1.5")
            self.you_xi_zt = "youxi"
        else:
            self.xian_shi_zi_mu("战力不足或已达最大轮回次数！")
            self.you_xi_zt = "youxi"

    # ==================== 区域/彩蛋检测 ====================
    def jian_ce_qu_yu(self):
        """检测玩家所在区域并显示字幕"""
        if self.dang_qian_cj == "map":
            if self.dang_qian_dt == 1 and self.wan_jia_x < GUA_JI_CHI_ZD:
                qy = "挂机池"
            else:
                qy = ""
                for dy in self.dang_qian_dy_dian:
                    if abs(self.wan_jia_x - dy["x"]) < 40:
                        qy = dy["ming_cheng"]
                        break

            if qy and qy != self.shang_ci_qy:
                self.shang_ci_qy = qy
                self.xian_shi_zi_mu(qy)
            elif not qy:
                self.shang_ci_qy = ""
        elif self.dang_qian_cj == "fuben1":
            qy = "副本1"
            if qy != self.shang_ci_qy:
                self.shang_ci_qy = qy
                self.xian_shi_zi_mu(qy)
        elif self.dang_qian_cj == "fuben2":
            qy = "副本2"
            if qy != self.shang_ci_qy:
                self.shang_ci_qy = qy
                self.xian_shi_zi_mu(qy)

    def jian_ce_cai_dan(self):
        """检测彩蛋输入"""
        # 地图6六阶丹生成区输入under
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 6 and
                abs(self.wan_jia_x - 1200) < 40):
            if "under" in self.shu_ru_hc.lower():
                if self.yin_xiao_niu:
                    self.yin_xiao_niu.play()
                self.xian_shi_zi_mu("彩蛋触发：牛逼！")
                self.shu_ru_hc = ""

        # 地图7八阶丹生成区输入lisan
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 7 and
                abs(self.wan_jia_x - 1600) < 40):
            if "lisan" in self.shu_ru_hc.lower():
                if self.yin_xiao_sha:
                    self.yin_xiao_sha.play()
                self.xian_shi_zi_mu("彩蛋触发：傻逼！")
                self.shu_ru_hc = ""

    # ==================== 游戏更新 ====================
    def geng_xin(self, shi_jian_dt):
        """更新游戏状态"""
        # 更新摄像机
        self.she_xiang_x = self.wan_jia_x - PING_MU_KD // 2
        if self.she_xiang_x < -500:
            self.she_xiang_x = -500
        if self.she_xiang_x > 2500:
            self.she_xiang_x = 2500

        # 更新字幕倒计时
        if self.zi_mu_djs > 0:
            self.zi_mu_djs -= shi_jian_dt
            if self.zi_mu_djs <= 0:
                self.zi_mu_wb = ""

        # 更新输入缓冲区倒计时
        if self.shu_ru_djs > 0:
            self.shu_ru_djs -= shi_jian_dt
            if self.shu_ru_djs <= 0:
                self.shu_ru_hc = ""

        # 挂机池加成
        if (self.dang_qian_cj == "map" and self.dang_qian_dt == 1 and
                self.wan_jia_x < GUA_JI_CHI_ZD):
            self.gua_ji_jss += shi_jian_dt
            if self.gua_ji_jss >= 1.0:
                self.gua_ji_jss -= 1.0
                jia_cheng = int(self.zhan_li * 0.0003 * self.lun_hui_jc)
                if jia_cheng < 1:
                    jia_cheng = 1
                self.zhan_li += jia_cheng

        # 副本1倍率丹自动生成
        if self.dang_qian_cj == "fuben1":
            self.bei_lv_dan_jss += shi_jian_dt
            if self.bei_lv_dan_jss >= 3.0:
                self.bei_lv_dan_jss -= 3.0
                self.bei_lv_dan_lb.append({
                    "x": 300 + random.randint(-50, 50),
                    "y": DI_MIAN_Y - 15,
                    "ming_cheng": "倍率丹",
                    "lei_xing": "bei_lv"
                })

        # 检测区域
        self.jian_ce_qu_yu()
        # 检测彩蛋
        self.jian_ce_cai_dan()

        # 检测长按空格
        if self.kong_ge_an_x and not self.lun_hui_yc:
            if time.time() - self.kong_ge_an_sj >= LUN_HUI_AN_MS:
                self.lun_hui_yc = True
                self.you_xi_zt = "lunhuixr"

    # ==================== 绘制主入口 ====================
    def hui_hua(self):
        """绘制游戏"""
        self.canvas.clear()

        with self.canvas:
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(PING_MU_KD, PING_MU_GD))

            if self.you_xi_zt == "youxi":
                self.hui_hua_di_mian()
                self.hui_hua_dan_yao_dian()
                self.hui_hua_gua_ji_chi()
                self.hui_hua_yi_sheng_dan()
                self.hui_hua_wan_jia()
                self.hui_hua_zhuang_tai_lan()
                self.hui_hua_an_niu()
                self.hui_hua_di_bu_an_niu()   # 新增：底部大按钮
                self.hui_hua_zi_mu()

            elif self.you_xi_zt == "dituxz":
                self.hui_hua_di_tu_xz()

            elif self.you_xi_zt == "fubenxz":
                self.hui_hua_fu_ben_xz()

            elif self.you_xi_zt == "jiaocheng":
                self.hui_hua_jiao_cheng()

            elif self.you_xi_zt == "lunhuixr":
                self.hui_hua_lun_hui_que_ren()

    # ==================== 事件处理 ====================
    def chu_li_shu_biao_dian_ji(self, x, y):
        """处理鼠标点击（非底部大按钮的其它点击）"""
        if self.you_xi_zt == "youxi":
            an_niu = self.jian_ce_an_niu(x, y)
            if an_niu == "ditu":
                self.you_xi_zt = "dituxz"
            elif an_niu == "fuben":
                self.you_xi_zt = "fubenxz"
            elif an_niu == "guaji":
                self.gua_ji()
            elif an_niu == "huicheng":
                self.hui_cheng()
            elif an_niu == "jiaocheng":
                self.you_xi_zt = "jiaocheng"
            elif an_niu == "cundang":
                self.baocun()
                self.xian_shi_zi_mu("游戏已保存！")
            elif an_niu == "jianpan":       # 新增：键盘按钮
                self.diao_chu_jian_pan()

        elif self.you_xi_zt == "dituxz":
            for i in range(10):
                hang = i // 5
                lie = i % 5
                ax = 200 + lie * 160
                ay = 150 + hang * 150
                if ax <= x <= ax + 140 and ay <= y <= ay + 80:
                    self.jin_ru_di_tu(i + 1)
                    self.you_xi_zt = "youxi"
                    return
            if PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 500 <= y <= 540:
                self.you_xi_zt = "youxi"

        elif self.you_xi_zt == "fubenxz":
            if 300 <= x <= 550 and 150 <= y <= 250:
                self.jin_ru_fu_ben(1)
                self.you_xi_zt = "youxi"
            elif 650 <= x <= 900 and 150 <= y <= 250:
                self.jin_ru_fu_ben(2)
                self.you_xi_zt = "youxi"
            elif PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 500 <= y <= 540:
                self.you_xi_zt = "youxi"

        elif self.you_xi_zt == "jiaocheng":
            if PING_MU_KD // 2 - 50 <= x <= PING_MU_KD // 2 + 50 and 540 <= y <= 580:
                self.you_xi_zt = "youxi"

        elif self.you_xi_zt == "lunhuixr":
            if 350 <= x <= 470 and 380 <= y <= 420:
                self.lun_hui()
            elif 730 <= x <= 850 and 380 <= y <= 420:
                self.you_xi_zt = "youxi"
                self.lun_hui_yc = False
                self.kong_ge_an_x = False

    def chu_li_an_jian_an_x(self, jian):
        """处理按键按下"""
        if jian == JIAN_KONG_GE:
            if not self.kong_ge_an_x:
                self.kong_ge_an_x = True
                self.kong_ge_an_sj = time.time()
                self.lun_hui_yc = False

        if self.you_xi_zt == "youxi":
            # 字母键（用于彩蛋输入）
            if 97 <= jian <= 122 or 65 <= jian <= 90:
                self.shu_ru_hc += chr(jian)
                self.shu_ru_djs = 3.0
                if len(self.shu_ru_hc) > 20:
                    self.shu_ru_hc = self.shu_ru_hc[-20:]

    def chu_li_an_jian_tai_qi(self, jian):
        """处理按键抬起"""
        if self.you_xi_zt != "youxi":
            return

        if jian == JIAN_KONG_GE:
            an_shi_duan = time.time() - self.kong_ge_an_sj
            self.kong_ge_an_x = False

            if an_shi_duan < LUN_HUI_AN_MS:
                if self.dang_qian_cj == "map":
                    self.sheng_cheng_dan_yao()
                elif self.dang_qian_cj == "fuben2":
                    self.sheng_cheng_wu_ji_dan()

        elif jian == JIAN_Z:
            self.chi_suo_you_dan()

        elif jian == JIAN_X:
            self.chi_bei_lv_dan()

        elif jian == JIAN_Y:
            if self.you_xi_zt == "lunhuixr":
                self.lun_hui()

        elif jian == JIAN_N:
            if self.you_xi_zt == "lunhuixr":
                self.you_xi_zt = "youxi"
                self.lun_hui_yc = False
                self.kong_ge_an_x = False

    # ==================== Kivy事件桥接 ====================
    def _kivy_an_jian_an_x(self, *args):
        """Kivy按键按下回调"""
        if len(args) < 2:
            return
        jian = args[1]
        self.an_jian_zt[jian] = True
        self.chu_li_an_jian_an_x(jian)

    def _kivy_an_jian_tai_qi(self, *args):
        """Kivy按键抬起回调"""
        if len(args) < 2:
            return
        jian = args[1]
        self.an_jian_zt[jian] = False
        self.chu_li_an_jian_tai_qi(jian)

    def _kivy_guan_bi(self, *args):
        """Kivy窗口关闭回调：退出前自动保存"""
        self.baocun()
        return False

    def on_touch_down(self, touch):
        """Kivy触摸/鼠标按下回调"""
        if self.collide_point(*touch.pos):
            you_xi_x = touch.x - self.x
            you_xi_y = PING_MU_GD - (touch.y - self.y)

            # ---- 先检测底部大按钮（左/右/空格/z/x）----
            an_ming = self._jian_ce_di_bu_an_niu(you_xi_x, you_xi_y)
            if an_ming is not None:
                touch.grab(self)
                self.an_xia_de_di_bu_an = an_ming
                self._di_bu_an_niu_an_x(an_ming)
                return True

            # ---- 其它点击走原有逻辑 ----
            self.chu_li_shu_biao_dian_ji(you_xi_x, you_xi_y)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """Kivy触摸/鼠标抬起回调（处理底部大按钮抬起）"""
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.an_xia_de_di_bu_an is not None:
                an_ming = self.an_xia_de_di_bu_an
                self.an_xia_de_di_bu_an = None
                self._di_bu_an_niu_tai_qi(an_ming)
            return True
        return super().on_touch_up(touch)

    # ==================== 存档/读档 ====================
    def baocun(self):
        """保存游戏到本地文件（静默失败，不打印日志）"""
        cundang_data = {
            'zhan_li': self.zhan_li,
            'lun_hui_cs': self.lun_hui_cs,
            'diao_luo_bl': self.diao_luo_bl,
            'lun_hui_jc': self.lun_hui_jc,
            'wan_jia_x': self.wan_jia_x,
            'dang_qian_dt': self.dang_qian_dt,
            'dang_qian_cj': self.dang_qian_cj,
            'di_tu_dan_yao': self.di_tu_dan_yao,
            'bei_lv_dan_lb': self.bei_lv_dan_lb,
            'wu_ji_dan_lb': self.wu_ji_dan_lb,
            'bei_lv_dan_jss': self.bei_lv_dan_jss,
            'gua_ji_jss': self.gua_ji_jss
        }
        try:
            with open(CUN_DANG_WJ, 'wb') as f:
                pickle.dump(cundang_data, f)
        except Exception:
            pass

    def jia_zai_cun_dang(self):
        """从本地文件加载存档（静默失败，不打印日志）"""
        if not os.path.exists(CUN_DANG_WJ):
            return

        try:
            with open(CUN_DANG_WJ, 'rb') as f:
                data = pickle.load(f)
            self.zhan_li = data.get('zhan_li', 3000)
            self.lun_hui_cs = data.get('lun_hui_cs', 0)
            self.diao_luo_bl = data.get('diao_luo_bl', 1)
            self.lun_hui_jc = data.get('lun_hui_jc', 1.0)
            self.wan_jia_x = data.get('wan_jia_x', DAN_YAO_KS)
            self.dang_qian_dt = data.get('dang_qian_dt', 1)
            self.dang_qian_cj = data.get('dang_qian_cj', 'map')
            self.di_tu_dan_yao = data.get('di_tu_dan_yao', [[] for _ in range(10)])
            self.bei_lv_dan_lb = data.get('bei_lv_dan_lb', [])
            self.wu_ji_dan_lb = data.get('wu_ji_dan_lb', [])
            self.bei_lv_dan_jss = data.get('bei_lv_dan_jss', 0)
            self.gua_ji_jss = data.get('gua_ji_jss', 0)
            self.shang_ci_qy = ""
            self.zi_mu_wb = ""
            self.zi_mu_djs = 0
            self.shu_ru_hc = ""
            self.shu_ru_djs = 0
        except Exception:
            pass

    # ==================== 主循环 ====================
    def yun_xing(self):
        """启动主循环（Kivy版）"""
        Window.bind(on_key_down=self._kivy_an_jian_an_x)
        Window.bind(on_key_up=self._kivy_an_jian_tai_qi)
        Window.bind(on_request_close=self._kivy_guan_bi)

        self._ding_shi_qi = Clock.schedule_interval(
            self.mei_zhen_geng_xin, 1.0 / ZHEN_LV)

    def mei_zhen_geng_xin(self, shi_jian_dt):
        """每一帧的更新与绘制"""
        # 左右移动（键盘 + 左下角按钮共用同一状态字典）
        if self.you_xi_zt == "youxi":
            if self.an_jian_zt.get(JIAN_LEFT):
                self.wan_jia_x -= YD_SU_DU
            if self.an_jian_zt.get(JIAN_RIGHT):
                self.wan_jia_x += YD_SU_DU

            if self.dang_qian_cj == "map":
                if self.wan_jia_x < -450:
                    self.wan_jia_x = -450
                if self.wan_jia_x > 2450:
                    self.wan_jia_x = 2450
            else:
                if self.wan_jia_x < -450:
                    self.wan_jia_x = -450
                if self.wan_jia_x > 1450:
                    self.wan_jia_x = 1450

        self.geng_xin(shi_jian_dt)
        self.hui_hua()


# ==================== Kivy应用主类 ====================
class ChiDanXiuXianApp(App):
    """Kivy应用入口"""

    def build(self):
        self.title = "吃丹修仙-under"
        Window.size = (PING_MU_KD, PING_MU_GD)

        root = FloatLayout()
        self.you_xi = YouXi()
        self.you_xi.pos = (0, 0)
        root.add_widget(self.you_xi)

        self.you_xi.yun_xing()
        return root


# ==================== 程序入口 ====================
if __name__ == "__main__":
    ChiDanXiuXianApp().run()
