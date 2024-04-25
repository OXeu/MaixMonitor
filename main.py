import requests
import json
from maix import image,display,app,thread
from maix.touchscreen import TouchScreen
import time

ts = TouchScreen()
icon_up = image.load("up.png",image.Format.FMT_RGBA8888)
icon_down = image.load("down.png",image.Format.FMT_RGBA8888)
icon_ram = image.load("ram.png",image.Format.FMT_RGBA8888)
icon_temp = image.load("temp.png",image.Format.FMT_RGBA8888)

W = 320
H = 240
color = image.Color.from_rgb(0,0,0)
progress_bg = image.Color.from_rgb(179,195,236)
bar_h = 6
padding_x = 16
padding_y = 12

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
    progress = progress if progress < 1.0 else 1
    progress_w = int((W - 2 * padding_x) * progress)
    drawRoundRect(img,padding_x,y,progress_w,bar_h,color)
    return h + padding_y + bar_h

    
url = 'http://10.0.0.1:9999'
disp = display.Display()
disp.set_vflip(True)
disp.set_hmirror(True)
_, top_font_h = image.string_size("Monitor", scale=2)
image.load_font("misans", "MiSans.ttf", size = 12)
image.set_default_font("misans")


alwaysOn = False  # 常亮模式
lastTouchTime = time.time()

def sched_ui():
    global alwaysOn
    global lastTouchTime
    temp_str = ''
    temperature = 0
    try:
        # 打开文件并读取内容
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as file:
            while not app.need_exit():
                now = time.time()
                if now - lastTouchTime < 20 or alwaysOn:
                    file.seek(0)
                    temp = file.read()
                    if temp != '':
                        temperature = int(temp) / 1000
                        temp_str = str(temperature) + " °C"
                    response = requests.get(url)
                    text = json.loads(response.content)
                    mem = bytes_format(text['mem']['used']) + "/" + bytes_format(text['mem']['total'])
                    upload = bytes_format(text['net']['enp1s0']['speed_rx']) + "/s"
                    download = bytes_format(text['net']['enp1s0']['speed_tx']) + "/s"
                    img = image.load("bg.png",image.Format.FMT_RGBA8888)
                    # img = image.Image(320,240)
                    img.draw_string(padding_x, padding_y, "监视器" + ("(常亮)" if alwaysOn else ""), color=color, scale=1.8)
                    top_h = top_font_h + 1 * padding_y
                    h = draw_item(img, top_h, icon_ram, mem, color, 1, text['mem']['used'] / text['mem']['total'])
                    h = draw_item(img, top_h + padding_y + h, icon_up, upload, color, 1, text['net']['enp1s0']['speed_rx'] / (125 * 1024 * 1024))
                    h = draw_item(img, top_h + 2 * (padding_y + h), icon_down, download, color, 1, text['net']['enp1s0']['speed_tx'] / (125 * 1024 * 1024))
                    h = draw_item(img, top_h + 3 * (padding_y + h), icon_temp, temp_str, color, 1, temperature / 100)
                    disp.show(img)
                time.sleep(0.5)
    except FileNotFoundError:
        print("无法找到CPU温度文件，请检查路径是否正确。")

def event_loop(self):
    global disp
    global lastTouchTime
    global alwaysOn
    while not app.need_exit():
        now = time.time()
        if now - lastTouchTime > 20 and not alwaysOn:
            if not disp.is_closed():
                disp.close()
            time.sleep(2)
        else:
            if disp.is_closed():
                disp.open()
        t = ts.read()
        if t[2]:
            if now - lastTouchTime < 3:
                alwaysOn = not alwaysOn
            lastTouchTime = now
        time.sleep(0.1)

t = thread.Thread(event_loop)
t.detach()
sched_ui()