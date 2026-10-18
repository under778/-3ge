[app]
title = 吃丹修仙
package.name = chidan
package.domain = org.under
source.dir = .
# 必须包含 wav 和 ttf，否则字体和声音文件根本进不去 APK
source.include_exts = py,png,jpg,kv,atlas,ttf,wav
version = 1.0

# 坚决不加 ffpyplayer，加了必打包失败。先用纯 Kivy 跑通画面
requirements = python3,kivy

# 绝对必须锁死横屏，否则你的按钮坐标全部失效
orientation = landscape
fullscreen = 1

android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = v2023.01.28
