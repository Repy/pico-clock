import time
import writer
import fontimage
import machine
import network
import ntptime
import json
import uasyncio
import gc

### 起動時の処理

rtc = machine.RTC()
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("system", "systemken")

while True:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    time.sleep(1)

if wlan.status() != 3:
    print('Wi-Fi Error:', wlan.status())

ntptime.host = "time.cloudflare.com"
try:
    ntptime.settime()
except:
    print('NTP Error')

w = writer.Writer(machine.Pin(28), 32, 8)


### 時刻取得
def now():
    current_time = time.localtime(time.time() + 9 * 60 * 60)
    hour = current_time[3]
    mini = current_time[4]
    return hour * 60 + mini

BOUND_UP = "up"
BOUND_DOWN = "down"

### ダイヤ時刻取得
async def diatime(bound):
    nowtime = now()
    print("diatime")
    reader, writer = await uasyncio.open_connection("doko-train.jp", 443, ssl=True, server_hostname="doko-train.jp")
    writer.write(f"GET /json/departure_info/202/2241215130_{bound}.json HTTP/1.1\r\nHost: doko-train.jp\r\n\r\n".encode())
    await writer.drain()
    
    data = await reader.read(5000)
    writer.close()
    reader.close()
    data = data.decode()
    datasp = data.split("\r\n\r\n", 1)
    statussp = datasp[0].split(" ", 2)
    print("datasp", datasp)
    print("statussp", statussp)
    if len(datasp) == 2:
        if len(statussp) == 3:
            status_code = statussp[1]
            response_text = datasp[1]
            print("HTTP ",status_code,response_text)

            if status_code == "200":
                parsed_data = json.loads(response_text)
                dia = parsed_data["ST_DIAGRAM"]
                for d in dia:
                    std = d["STD"]
                    hour, mini = std.split(":")
                    ad = d["ad_latency"]
                    print(hour, mini, ad)
                    hour = int(hour)
                    mini = int(mini)
                    ad = int(ad)
                    dtime = hour * 60 + mini + ad
                    if nowtime + 5 < dtime:
                        return dtime
            else:
                print("Status:", status_code)
                print("Response:", response_text)
    return -1

dtime_up = 0
dtime_down = 0

### 1スレッド目
async def doko():
    while True:
        global dtime_up
        try:
            dtime_up = await diatime(BOUND_UP)
        except:
            pass
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        global dtime_down
        try:
            dtime_down = await diatime(BOUND_DOWN)
        except:
            pass
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        await uasyncio.sleep_ms(120000)

### 2スレッド目
async def clock():
    count = 0
    while True:
        count = count + 1
        
        nowtime = now()
        print("nowtime:", nowtime, ", dtime_down:", dtime_down, ", dtime_up:", dtime_up)
        
        difftime_down = dtime_down - nowtime
        difftime_up = dtime_up - nowtime
        
        
        if difftime_down > 0 and (count//5) % 3 == 1:
            w.reset()
            w.draw(0,0,fontimage.image(fontimage.kanji_ue,(8,0,0)))
            w.draw(7,0,fontimage.image(fontimage.hiragana_ri,(8,0,0)))
            w.draw(13,0,fontimage.image(fontimage.number[(difftime_down//10) % 10],(8,0,0)))
            w.draw(19,0,fontimage.image(fontimage.number[difftime_down % 10],(8,0,0)))
            w.draw(25,0,fontimage.image(fontimage.kanji_hun,(8,0,0)))
            w.write()
            w.print()

        if difftime_up > 0 and (count//5) % 3 == 2:
            w.reset()
            w.draw(0,0,fontimage.image(fontimage.kanji_shita,(8,0,0)))
            w.draw(7,0,fontimage.image(fontimage.hiragana_ri,(8,0,0)))
            w.draw(13,0,fontimage.image(fontimage.number[(difftime_up//10) % 10],(8,0,0)))
            w.draw(19,0,fontimage.image(fontimage.number[difftime_up % 10],(8,0,0)))
            w.draw(25,0,fontimage.image(fontimage.kanji_hun,(8,0,0)))
            w.write()
            w.print()

        else:
            w.reset()
            w.draw(0,0,fontimage.image(fontimage.number[(nowtime // 60) // 10],(8,8,8)))
            w.draw(6,0,fontimage.image(fontimage.number[(nowtime // 60) % 10],(8,8,8)))
            w.draw(12,2,[[(8,8,8)]])
            w.draw(12,5,[[(8,8,8)]])
            w.draw(14,0,fontimage.image(fontimage.number[(nowtime % 60) // 10],(8,8,8)))
            w.draw(20,0,fontimage.image(fontimage.number[(nowtime % 60) % 10],(8,8,8)))
            w.write()
            w.print()
            
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        await uasyncio.sleep_ms(1000)

async def main():
    await uasyncio.gather(doko(), clock())

uasyncio.run(main())



