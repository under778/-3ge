[app]
title = 吃丹修仙
package.name = chidan
package.domain = org.under
source.dir = .
source.include_exts = py,png,jpg,mp3,wav,ttf
version = 1.0

requirements = python3,kivy,ffpyplayer

orientation = landscape
fullscreen = 1

# 使用 31 和 25b，这是 CI 环境兼容性最好的组合
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# 删掉 p4a.branch，让 Buildozer 使用它默认的稳定版本
