import requests
import json
from maix import image,display,app

icon_up = image.load("/root/up.png",image.Format.FMT_RGBA8888)
icon_down = image.load("/root/down.png",image.Format.FMT_RGBA8888)
icon_ram = image.load("/root/ram.png",image.Format.FMT_RGBA8888)

W = 320
H = 240
color = image.Color.from_rgb(0,0,0)
progress_bg = image.Color.from_rgb(179,195,236)
bar_h = 6
padding_x = 16
padding_y = 8

def bytes_format(bytes_int):
    # 定义单位
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    # 计算字节数和单位的对应关系
    if bytes_int == 1:
        return "1 Byte"
    unit_index = 0
    while bytes_int >= 1024:
        bytes_int /= 1024.0
        unit_index += 1
    # 格式化输出
    return f"{bytes_int:.1f} {units[unit_index]}"


def drawRoundRect(img,x:int,y:int,w:int,h:int,color):
    r = int(h/2)
    img.draw_rect(x, y, w, h, color, r)

def draw_item(img,y,icon,text,color,scale,progress:float):
    w, h = image.string_size(text, scale=scale)
    img.draw_string(W-w-padding_x,y,text,color=color,scale=scale)
    img.draw_image(padding_x, y, icon)
    y = y + h + padding_y
    drawRoundRect(img, padding_x, y, W - 2 * padding_x, bar_h, progress_bg)
    progress_w = int((W - 2 * padding_x) * progress)
    drawRoundRect(img,padding_x,y,progress_w,bar_h,color)
    return h + padding_y + bar_h
    
url = 'http://10.0.0.1:9999'
disp = display.Display()
while not app.need_exit():
    response = requests.get(url)
    text = json.loads(response.content)
    mem = bytes_format(text['mem']['used']) + "/" + bytes_format(text['mem']['total'])
    upload = bytes_format(text['net']['enp1s0']['speed_rx']) + "/s"
    download = bytes_format(text['net']['enp1s0']['speed_tx']) + "/s"
    img = image.load("/root/bg.png",image.Format.FMT_RGBA8888)
    # img = image.Image(320,240)
    img.draw_string(padding_x, 2 * padding_y, "Monitor", color=color, scale=2)
    _, top_h = image.string_size("Monitor", scale=2)
    top_h += 2 * padding_y
    h = draw_item(img, top_h, icon_ram, mem, color, 1, text['mem']['used'] / text['mem']['total'])
    h = draw_item(img, top_h + padding_y + h, icon_up, upload, color, 1, text['net']['enp1s0']['speed_rx'] / (125 * 1024 * 1024))
    draw_item(img, top_h + 2 * (padding_y + h), icon_down, download, color, 1, text['net']['enp1s0']['speed_tx'] / (125 * 1024 * 1024))
    img = img.rotate(90).rotate(90)
    disp.show(img)
