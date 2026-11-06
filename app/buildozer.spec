[app]

title = GreenGadget

package.name = greengadget
package.domain = org.greengadget

source.dir = .

source.include_exts = py,kv,png,jpg,jpeg,ttf,mp4,json

requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,Pillow

orientation = portrait

version = 1.0

# icon.filename = %(source.dir)s/extras/LogoFinal.png


[buildozer]

log_level = 2
warn_on_root = 1


[android]

android.archs = arm64-v8a
android.minapi = 23
android.api = 35
android.accept_sdk_license = True
android.permissions = INTERNET
android.orientation = portrait
