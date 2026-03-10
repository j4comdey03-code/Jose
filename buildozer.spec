[app]

title = Joseph LBW App
package.name = josephlbw
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0

requirements = python3,kivy,opencv, numpy

orientation = portrait

fullscreen = 0

android.permissions = CAMERA

android.api = 31
android.minapi = 21

[buildozer]

log_level = 2
warn_on_root = 1
