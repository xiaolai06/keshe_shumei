#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智居物语 — 硬件独立测试脚本
在树莓派上运行，逐个测试所有硬件模块。

用法：
  python hardware_test.py          # 测试所有模块
  python hardware_test.py ds18b20  # 只测试温度传感器
  python hardware_test.py oled     # 只测试 OLED 显示屏

支持的模块名：
  ds18b20, dht22, light, oled, buzzer, camera, speaker, mic
"""
import sys
import time
import subprocess

# ══════════════════════════════════════════════
# 引脚定义（BCM 编号，与 config.py 一致）
# ══════════════════════════════════════════════
PIN_DS18B20 = 4
PIN_DHT22 = 17
PIN_LIGHT = 27
PIN_BUZZER = 12
# SPI (SSD1351 OLED)
OLED_CS = 8
OLED_DC = 13
OLED_RST = 24
# I2S (INMP441 麦克风)
I2S_BCLK = 18
I2S_LRCK = 19
I2S_DIN = 20


def header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def ok(msg: str):
    print(f"  ✅ {msg}")


def fail(msg: str):
    print(f"  ❌ {msg}")


def info(msg: str):
    print(f"  ℹ️  {msg}")


# ══════════════════════════════════════════════
# 1. DS18B20 温度传感器
# ══════════════════════════════════════════════
def test_ds18b20():
    header("DS18B20 温度传感器 (GPIO 4, 1-Wire)")

    import glob
    base_dir = "/sys/bus/w1/devices/"
    devices = glob.glob(base_dir + "28-*")
    if not devices:
        fail("未检测到 DS18B20 设备")
        info("检查: 1) 接线是否正确  2) 是否启用了 1-Wire (dtoverlay=w1-gpio)")
        info("在 /boot/config.txt 加入: dtoverlay=w1-gpio，然后重启")
        info("接线: VCC→3.3V(物理1), GND→GND(物理6), DQ→GPIO4(物理7)")
        info("注意: DQ 与 3.3V 之间必须接 10KΩ 上拉电阻")
        return False

    device_file = devices[0] + "/temperature"
    ok(f"找到设备: {devices[0]}")

    for i in range(3):
        try:
            with open(device_file) as f:
                temp = float(f.read().strip()) / 1000.0
            ok(f"温度读数: {temp:.1f}°C")
            if 10 < temp < 50:
                ok("温度范围正常")
            else:
                info(f"温度 {temp:.1f}°C 偏离正常范围，请检查传感器")
            time.sleep(1)
        except Exception as e:
            fail(f"读取失败: {e}")
            return False

    return True


# ══════════════════════════════════════════════
# 2. DHT22 温湿度传感器
# ══════════════════════════════════════════════
def test_dht22():
    header("DHT22 温湿度传感器 (GPIO 17)")

    try:
        import board
        import adafruit_dht
        dht = adafruit_dht.DHT22(board.D17)
    except ImportError:
        info("adafruit-circuitpython-dht 未安装，尝试用旧版 dht 库...")
        try:
            import Adafruit_DHT
            humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, PIN_DHT22)
            if humidity is not None and temp is not None:
                ok(f"温度: {temp:.1f}°C  湿度: {humidity:.1f}%")
                return True
            fail("读取失败，请检查接线")
            return False
        except ImportError:
            fail("无可用 DHT 库，请安装: pip install adafruit-circuitpython-dht")
            return False

    for i in range(3):
        try:
            temp = dht.temperature
            humidity = dht.humidity
            if temp is not None and humidity is not None:
                ok(f"温度: {temp:.1f}°C  湿度: {humidity:.1f}%")
                if 10 < temp < 50 and 10 < humidity < 95:
                    ok("数据范围正常")
                return True
        except RuntimeError as e:
            info(f"读取失败（第 {i+1} 次）: {e}，等待重试...")
            time.sleep(2.5)
        except Exception as e:
            fail(f"异常: {e}")
            return False

    fail("3 次读取均失败，请检查接线和上拉电阻")
    info("接线: VCC→3.3V(物理1), DATA→GPIO17(物理11), GND→GND(物理6)")
    info("注意: DATA 与 3.3V 之间需要 10KΩ 上拉电阻（部分模块已集成）")
    return False


# ══════════════════════════════════════════════
# 3. 光照传感器（数字输出）
# ══════════════════════════════════════════════
def test_light():
    header("光照传感器 (GPIO 27, 数字输出)")

    try:
        import RPi.GPIO as GPIO
    except ImportError:
        fail("RPi.GPIO 未安装（树莓派自带，非树莓派环境无法测试）")
        return False

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_LIGHT, GPIO.IN)

    try:
        info("读取 5 次光照状态...")
        for i in range(5):
            value = GPIO.input(PIN_LIGHT)
            status = "光照充足 (HIGH)" if value else "光照不足 (LOW)"
            ok(f"第 {i+1} 次: {status}")
            time.sleep(0.5)

        info("提示: 可用手遮挡传感器观察输出变化")
        info("如果状态不变化，请调节模块上的电位器校准阈值")

    except Exception as e:
        fail(f"读取失败: {e}")
        info("接线: VCC→3.3V(物理1), GND→GND(物理6), SIG→GPIO27(物理13)")
        GPIO.cleanup()
        return False

    GPIO.cleanup()
    return True


# ══════════════════════════════════════════════
# 4. SSD1351 RGB OLED 显示屏 (SPI)
# ══════════════════════════════════════════════
def test_oled():
    header("SSD1351 RGB OLED 显示屏 (SPI, 128×128)")

    try:
        from luma.core.interface.serial import spi
        from luma.oled.device import ssd1351
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        fail("依赖未安装: pip install luma.oled pillow")
        return False

    try:
        serial = spi(port=0, device=0, gpio_DC=OLED_DC, gpio_RST=OLED_RST, gpio_CS=OLED_CS)
        device = ssd1351(serial, width=128, height=128)
        ok("OLED 初始化成功 (128×128 RGB SSD1351)")

        # 测试 1: 清屏
        device.hide()
        time.sleep(0.3)
        device.show()
        ok("显示/隐藏 测试通过")

        # 测试 2: 彩色文字
        img = Image.new("RGB", (128, 128), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Hello Pi!", fill=(255, 255, 255))
        draw.text((10, 30), "Smart Home", fill=(255, 200, 50))
        draw.text((10, 50), "SSD1351 RGB", fill=(0, 200, 255))
        draw.text((10, 70), "Test OK!", fill=(50, 255, 100))
        device.display(img)
        ok("彩色文字显示测试（屏幕上应看到 4 行不同颜色的文字）")

        time.sleep(2)

        # 测试 3: 彩色图形
        img = Image.new("RGB", (128, 128), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((20, 20, 108, 108), outline=(255, 200, 50), width=2)
        draw.ellipse((40, 40, 88, 88), fill=(0, 200, 255))
        device.display(img)
        ok("彩色图形测试（屏幕上应看到彩色圆环）")

        time.sleep(2)

        # 测试 4: 清屏
        device.cleanup()
        ok("OLED 清屏，测试完成")

    except Exception as e:
        fail(f"OLED 测试失败: {e}")
        info("检查: VCC/GND/DIN/CLK/CS/DC/RST 接线是否正确")
        info("接线: VCC→3.3V(物理1), GND→GND(物理6)")
        info("      DIN→GPIO10(物理19), CLK→GPIO11(物理23)")
        info("      CS→GPIO8(物理24), DC→GPIO13(物理33), RST→GPIO24(物理18)")
        return False

    return True


# ══════════════════════════════════════════════
# 5. 有源蜂鸣器模块
# ══════════════════════════════════════════════
def test_buzzer():
    header("有源蜂鸣器模块 (GPIO 12)")

    try:
        import RPi.GPIO as GPIO
    except ImportError:
        fail("RPi.GPIO 未安装")
        return False

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_BUZZER, GPIO.OUT)

    try:
        # 有源蜂鸣器：高电平响，低电平停
        info("短响 3 次...")
        for i in range(3):
            GPIO.output(PIN_BUZZER, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(PIN_BUZZER, GPIO.LOW)
            time.sleep(0.15)
        ok("短响测试完成")

        info("长响 1 次...")
        GPIO.output(PIN_BUZZER, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(PIN_BUZZER, GPIO.LOW)
        ok("长响测试完成")

        info("节奏响（提醒音效）...")
        for _ in range(3):
            GPIO.output(PIN_BUZZER, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(PIN_BUZZER, GPIO.LOW)
            time.sleep(0.1)
        ok("提醒音效测试完成")

    except Exception as e:
        fail(f"蜂鸣器测试失败: {e}")
    finally:
        GPIO.output(PIN_BUZZER, GPIO.LOW)
        GPIO.cleanup()

    return True


# ══════════════════════════════════════════════
# 6. USB 摄像头
# ══════════════════════════════════════════════
def test_camera():
    header("USB 摄像头")

    try:
        import cv2
    except ImportError:
        fail("opencv-python 未安装: pip install opencv-python")
        return False

    # 检查设备
    import os
    video_devices = [f for f in os.listdir("/dev") if f.startswith("video")]
    if not video_devices:
        fail("未检测到摄像头设备 (/dev/video*)")
        info("检查: USB 摄像头是否插好")
        return False
    ok(f"检测到视频设备: {', '.join(video_devices)}")

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            fail("无法打开摄像头 (VideoCapture(0))")
            return False

        ok("摄像头已打开")

        # 读取几帧
        for i in range(3):
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                ok(f"帧 {i+1}: {w}×{h} 像素")
            else:
                fail(f"帧 {i+1} 读取失败")
            time.sleep(0.5)

        # 保存一张照片
        ret, frame = cap.read()
        if ret:
            path = "/tmp/hardware_test_photo.jpg"
            cv2.imwrite(path, frame)
            ok(f"照片已保存: {path}")

        cap.release()
        ok("摄像头测试完成")

    except Exception as e:
        fail(f"摄像头测试失败: {e}")
        return False

    return True


# ══════════════════════════════════════════════
# 7. USB 音响 (Waveshare USB TO AUDIO)
# ══════════════════════════════════════════════
def test_speaker():
    header("USB 音响 (Waveshare USB TO AUDIO)")

    # 检查音频设备
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, timeout=5)
        if "USB" in result.stdout or "card" in result.stdout:
            ok("检测到音频设备:")
            for line in result.stdout.strip().split("\n"):
                if "card" in line:
                    info(f"  {line.strip()}")
        else:
            fail("未检测到 USB 音频设备")
            info("检查: Waveshare USB TO AUDIO 是否插好")
            return False
    except FileNotFoundError:
        fail("aplay 命令不可用（非 Linux 环境？）")
        return False

    # 播放测试音
    try:
        info("生成测试音（1 秒 440Hz 正弦波）...")
        subprocess.run([
            "python3", "-c",
            "import struct,math,sys;"
            "rate=44100;dur=1;freq=440;"
            "data=struct.pack('<'+'h'*int(rate*dur),"
            "*(int(32767*math.sin(2*math.pi*freq*i/rate)*0.5) for i in range(int(rate*dur))));"
            "sys.stdout.buffer.write(b'RIFF'+struct.pack('<I',36+len(data))+b'WAVEfmt ')"
            "+struct.pack('<IHHIIHH',16,1,1,rate,rate,2,16)+b'data'"
            "+struct.pack('<I',len(data))+data)"
        ], stdout=open("/tmp/test_tone.wav", "wb"), timeout=5)

        info("播放测试音...")
        subprocess.run(["aplay", "/tmp/test_tone.wav"], timeout=5, capture_output=True)
        ok("播放完成 — 如果听到了声音，说明音响正常")

    except Exception as e:
        info(f"播放测试音失败: {e}")
        info("尝试用 speaker-test...")
        try:
            subprocess.run(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"],
                           timeout=5, capture_output=True)
            ok("speaker-test 完成")
        except Exception:
            info("speaker-test 也不可用，请手动测试音响")

    return True


# ══════════════════════════════════════════════
# 8. INMP441 I2S 麦克风
# ══════════════════════════════════════════════
def test_mic():
    header("INMP441 I2S 麦克风")

    # 检查 I2S 设备
    try:
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        if "I2S" in result.stdout or "mic" in result.stdout.lower() or "card" in result.stdout:
            ok("检测到录音设备:")
            for line in result.stdout.strip().split("\n"):
                if "card" in line:
                    info(f"  {line.strip()}")
        else:
            fail("未检测到 I2S 录音设备")
            info("检查: 1) /boot/config.txt 是否有 dtoverlay=i2s-mmic")
            info("       2) INMP441 VDD/GND/SCK/WS/SD 接线是否正确")
            info("接线: VDD→3.3V(物理1), GND→GND(物理6)")
            info("      SCK→GPIO18(物理12), WS→GPIO19(物理35), SD→GPIO20(物理38)")
            info("      L/R→GND (选择左声道)")
            return False
    except FileNotFoundError:
        fail("arecord 命令不可用")
        return False

    # 录音测试
    try:
        info("录音 2 秒...")
        subprocess.run([
            "arecord", "-D", "default", "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", "2", "/tmp/hardware_test_mic.wav"
        ], timeout=10, capture_output=True)

        import os
        if os.path.exists("/tmp/hardware_test_mic.wav"):
            size = os.path.getsize("/tmp/hardware_test_mic.wav")
            ok(f"录音文件: /tmp/hardware_test_mic.wav ({size} 字节)")
            if size > 1000:
                ok("录音成功（可以用 aplay 播放验证）")
            else:
                info("录音文件过小，可能麦克风没有信号")
        else:
            fail("录音文件未生成")

    except Exception as e:
        fail(f"录音测试失败: {e}")
        return False

    return True


# ══════════════════════════════════════════════
# 9. 语音识别 (麦克风 → STT → 文字)
# ══════════════════════════════════════════════
def test_voice():
    header("语音识别 (麦克风 → STT API)")

    # 检查 STT 配置
    import config
    config.load_stt_config()

    if not config.STT_API_KEY:
        fail("STT API Key 未配置")
        info("请在 Web 设置页面配置 STT，或编辑 data/config.json")
        info("支持: 硅基流动 SenseVoice / OpenAI Whisper / 自定义")
        return False

    ok(f"STT 服务商: {config.STT_BASE_URL}")
    ok(f"STT 模型:   {config.STT_MODEL}")
    ok(f"识别语言:   {config.STT_LANGUAGE}")

    # 测试 STT API 连通性
    info("测试 STT API 连通性...")
    try:
        from perception.speech import test_stt_connection
        result = test_stt_connection()
        if result["success"]:
            ok(f"API 连接成功 ({result.get('latency_ms', '?')}ms)")
        else:
            fail(f"API 连接失败: {result['message']}")
            return False
    except Exception as e:
        fail(f"STT 测试异常: {e}")
        return False

    # 检查麦克风
    try:
        r = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        if "card" not in r.stdout:
            fail("未检测到录音设备，请先运行: python3 hardware_test.py mic")
            return False
    except Exception:
        fail("arecord 不可用")
        return False

    # 录音 → STT 识别
    wav_path = "/tmp/hardware_test_voice.wav"
    info("")
    info("🎤 请对麦克风说话（3 秒）...")
    info("   建议说: 你好 / 今天天气怎么样 / 打个招呼")
    info("")

    try:
        subprocess.run([
            "arecord", "-D", "default", "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", "3", wav_path, "-q"
        ], timeout=10)

        import os
        if not os.path.exists(wav_path):
            fail("录音文件未生成")
            return False

        size = os.path.getsize(wav_path)
        if size < 3200:
            fail(f"录音文件太小 ({size} 字节)，可能麦克风没有信号")
            return False

        ok(f"录音完成: {size} 字节")

        # 读取音频 → 调用 STT
        info("发送到 STT API 识别中...")
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()

        from perception.speech import recognize_audio
        text = recognize_audio(audio_bytes, filename="speech.wav")

        if text:
            ok(f"识别结果: 「{text}」")
            info("")
            info("✅ 语音识别链路正常！")
            info("   麦克风录音 → 云端 STT → 文字输出")
            info("   项目启动后会自动进入 VAD 持续监听模式")
            return True
        else:
            fail("STT 返回空结果")
            info("可能原因: 1) 说话声音太小  2) 录音环境太吵  3) API 配额用完")
            return False

    except subprocess.TimeoutExpired:
        fail("录音超时")
        return False
    except Exception as e:
        fail(f"语音识别测试失败: {e}")
        return False


# ══════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════
ALL_TESTS = {
    "ds18b20":  ("DS18B20 温度传感器", test_ds18b20),
    "dht22":    ("DHT22 温湿度传感器", test_dht22),
    "light":    ("光照传感器 (数字输出)", test_light),
    "oled":     ("SSD1351 RGB OLED 显示屏", test_oled),
    "buzzer":   ("有源蜂鸣器模块", test_buzzer),
    "camera":   ("USB 摄像头", test_camera),
    "speaker":  ("USB 音响", test_speaker),
    "mic":      ("INMP441 I2S 麦克风", test_mic),
    "voice":    ("语音识别 (麦克风→STT→文字)", test_voice),
}


def main():
    print("╔══════════════════════════════════════════════╗")
    print("║     智居物语 — 硬件测试脚本                   ║")
    print("║     Raspberry Pi 4B · BCM 引脚编号            ║")
    print("╚══════════════════════════════════════════════╝")

    # 解析命令行参数
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        targets = list(ALL_TESTS.keys())

    results = {}
    for name in targets:
        if name not in ALL_TESTS:
            print(f"\n⚠️  未知模块: {name}")
            print(f"   支持: {', '.join(ALL_TESTS.keys())}")
            continue

        title, func = ALL_TESTS[name]
        try:
            results[name] = func()
        except KeyboardInterrupt:
            print("\n\n⛔ 用户中断测试")
            break
        except Exception as e:
            fail(f"测试异常: {e}")
            results[name] = False

        time.sleep(0.5)

    # 汇总
    header("测试结果汇总")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        title = ALL_TESTS[name][0]
        print(f"  {status}  {title}")

    print(f"\n  总计: {passed}/{total} 通过")
    if passed == total:
        print("  🎉 所有测试通过！")
    else:
        print("  ⚠️  部分测试失败，请检查接线和依赖")


if __name__ == "__main__":
    main()
