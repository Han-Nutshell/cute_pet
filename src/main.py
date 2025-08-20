import tkinter as tk
from tkinter import messagebox
import random
import time
import threading
import math
from PIL import Image, ImageTk, ImageDraw, ImageFont
import subprocess
import sys
import os
import pystray
from pystray import MenuItem as item
import json

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面宠物")
        self.root.overrideredirect(True)  # 移除窗口边框
        self.root.attributes('-topmost', True)  # 始终置顶
        self.root.attributes('-transparentcolor', 'white')  # 设置透明色
        
        # 窗口大小（需要增加高度来容纳对话框）
        self.pet_size = 100
        self.total_height = 150  # 增加高度来容纳对话框
        self.root.geometry(f"{self.pet_size}x{self.total_height}")
        
        # 获取屏幕尺寸并设置初始位置（右下角）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.pet_size - 50
        y = screen_height - self.total_height - 100
        self.root.geometry(f"+{x}+{y}")
        
        # 宠物状态
        self.emotions = ['normal', 'happy', 'sleepy', 'excited', 'thinking', 'curious']
        self.current_emotion = 'normal'  # 初始状态为正常
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # 时间相关状态
        self.last_interaction_time = time.time()
        self.idle_time_threshold = 300  # 300秒后进入困倦状态
        self.thinking_time_threshold = 60  # 60秒后进入思考状态
        
        # 鼠标状态追踪
        self.mouse_over = False  # 追踪鼠标是否在宠物上方
        self.mouse_x = 0  # 鼠标相对于宠物的X坐标
        self.mouse_y = 0  # 鼠标相对于宠物的Y坐标

        # 说话相关
        self.is_speaking = False
        self.speech_bubble = None
        self.speech_text = None
        try:
            self.hello_messages = self.load_hello_messages()
        except Exception as e:
            print(f"Error loading hello messages: {e}")
        self.hello_messages = {
            'greeting': [
                "你好呀！我是你的桌面宠物~",
                "主人好！今天过得怎么样？",
                "嗨！很高兴见到你~",
                "你好！我在这里陪着你哦！",
                "主人，你来找我玩了吗？"
            ],
            'happy': [
                "我今天心情特别好！",
                "和你在一起真开心~",
                "哈哈哈，好开心啊！",
                "今天是美好的一天呢！",
                "我超级开心的！"
            ],
            'sleepy': [
                "好困啊...想睡觉了",
                "主人也要注意休息哦",
                "工作累了就休息一下吧",
                "呼~好想睡个午觉",
                "记得劳逸结合哦~"
            ],
            'excited': [
                "哇！好兴奋啊！",
                "发生什么好事了吗？",
                "我充满了能量！",
                "太棒了！",
                "让我们一起加油吧！"
            ],
            'thinking': [
                "让我想想...",
                "这个问题很有趣呢",
                "嗯...该怎么办呢？",
                "我在思考中...",
                "有什么好主意吗？"
            ],
            'curious': [
                "咦？这是什么？",
                "好奇怪啊，发生什么了？",
                "哇，这很有趣呢！",
                "我想探索一下~",
                "有什么新发现吗？"
            ],
            'work': [
                "工作要加油哦！",
                "别忘了适当休息~",
                "你今天很努力呢！",
                "加油！我相信你！",
                "工作虽累，但要保持好心情！"
            ],
            'random': [
                "你知道吗？我会变很多表情哦！",
                "试试右键菜单，有很多功能呢~",
                "我可以提醒你摸鱼哦！",
                "拖动我可以换位置呢！",
                "双击我会有惊喜哦！",
                "我会一直陪着你的~",
                "记得要好好照顾自己！",
                "今天的天气不错呢！",
                "你有什么烦恼吗？可以告诉我哦~",
                "我虽然是虚拟的，但关心是真的！"
            ]
        }
        
        # 动画相关
        self.animation_frame = 0
        self.animation_speed = 500  # 毫秒
        
        # 摸鱼提醒器进程
        self.fish_reminder_process = None
        
        # 托盘相关
        self.tray_icon = None
        self.tray_thread = None
        self.is_hidden = False
        
        # 初始化顺序很重要
        self.create_pet_images()
        self.create_tray_icon()  # 在界面创建前先创建托盘图标
        self.create_widgets()
        self.bind_events()
        self.start_tray_icon()  # 启动托盘图标
        self.start_animation()
        self.start_behavior_monitoring()  # 启动行为监控
        self.start_eye_tracking()  # 启动眼球追踪
        
        # 启动后说一句问候语
        self.root.after(1000, lambda: self.say_random_message('greeting'))

    def load_hello_messages(self):
        data_path = os.path.join('..', 'data', 'pet_hello.json')
        with open(data_path, 'r', encoding='utf-8') as file:
            self.hello_messages = json.load(file)

    def calculate_eye_position(self, eye_center_x, eye_center_y, mouse_x, mouse_y):
        """计算眼球位置"""
        # 眼球移动的最大半径
        max_radius = 3
        
        # 计算鼠标相对于眼睛中心的位置
        dx = mouse_x - eye_center_x
        dy = mouse_y - eye_center_y
        
        # 计算距离
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return eye_center_x, eye_center_y
        
        # 限制眼球移动范围
        if distance > max_radius:
            # 按比例缩放到最大半径
            dx = dx * max_radius / distance
            dy = dy * max_radius / distance
        
        return eye_center_x + dx, eye_center_y + dy

    def create_pet_images(self):
        """创建不同表情的宠物图像"""
        self.pet_images = {}
        
        for emotion in self.emotions:
            # 创建图像
            img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            if emotion == 'normal':
                # 普通表情 - 绿色圆形身体
                draw.ellipse([10, 20, 70, 70], fill='#4CAF50', outline='#2E7D32', width=2)
                # 眼睛白色部分
                draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                # 嘴巴
                draw.arc([35, 45, 45, 55], 0, 180, fill='black', width=2)

            elif emotion == 'happy':
                # 开心表情 - 黄色身体
                draw.ellipse([10, 20, 70, 70], fill='#FFC107', outline='#FF8F00', width=2)
                # 眼睛白色部分
                draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                # 开心的嘴巴
                draw.arc([30, 40, 50, 60], 0, 180, fill='black', width=3)

            elif emotion == 'sleepy':
                # 困倦表情 - 蓝色身体
                draw.ellipse([10, 20, 70, 70], fill='#2196F3', outline='#0D47A1', width=2)
                # 困倦的眼睛（闭着的）
                draw.ellipse([25, 33, 35, 37], fill='#FFFEFA', outline='black')
                draw.ellipse([45, 33, 55, 37], fill='#FFFEFA', outline='black')
                draw.line([25, 35, 35, 35], fill='black', width=2)
                draw.line([45, 35, 55, 35], fill='black', width=2)
                # 小嘴巴
                draw.ellipse([38, 48, 42, 52], fill='black')
                # Z字符表示睡觉
                draw.text((55, 15), "Z", fill='black')

            elif emotion == 'excited':
                # 兴奋表情 - 红色身体
                draw.ellipse([10, 20, 70, 70], fill='#F44336', outline='#B71C1C', width=2)
                # 大眼睛白色部分
                draw.ellipse([20, 25, 35, 40], fill='#FFFEFA', outline='black')
                draw.ellipse([45, 25, 60, 40], fill='#FFFEFA', outline='black')
                # 兴奋的嘴巴
                draw.ellipse([35, 45, 45, 55], fill='black')

            elif emotion == 'thinking':
                # 思考表情 - 紫色身体
                draw.ellipse([10, 20, 70, 70], fill='#9C27B0', outline='#4A148C', width=2)
                # 眼睛白色部分（向上看）
                draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                # 思考的嘴巴
                draw.arc([35, 50, 45, 55], 0, 180, fill='black', width=2)
                # 思考泡泡
                draw.ellipse([55, 10, 65, 20], fill='white', outline='black')
                draw.text((57, 12), "?", fill='black')
                
            elif emotion == 'curious':
                # 好奇表情 - 橙色身体
                draw.ellipse([10, 20, 70, 70], fill='#FF9800', outline='#E65100', width=2)
                # 好奇的大眼睛白色部分（一大一小表示疑惑）
                draw.ellipse([22, 28, 36, 42], fill='#FFFEFA', outline='black')  # 左眼大一些
                draw.ellipse([44, 30, 54, 40], fill='#FFFEFA', outline='black')  # 右眼小一些
                # 好奇的嘴巴（小圆形表示"哦"）
                draw.ellipse([37, 47, 43, 53], fill='black')
                # 感叹号表示惊讶
                draw.text((60, 15), "!", fill='black')

            # 添加可爱的腮红
            if emotion in ['happy', 'excited', 'curious']:
                draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
                draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)
            
            self.pet_images[emotion] = ImageTk.PhotoImage(img)

            # 眨眼动画相关
            self.blink_frame = 0
            self.is_blinking = False
            self.blink_interval = random.randint(80, 150)  # 眨眼间隔帧数

            def blink_animation():
                if not self.is_hidden:
                    self.blink_frame += 1
                # 随机眨眼
                if not self.is_blinking and self.blink_frame >= self.blink_interval:
                    self.is_blinking = True
                    self.blink_frame = 0
                    self.blink_interval = random.randint(80, 150)
                    # 眨眼持续帧数
                    self.blink_duration = 8
                    self.blink_count = 0
                if self.is_blinking:
                    self.blink_count += 1
                    # 眨眼持续一段时间
                    if self.blink_count >= self.blink_duration:
                        self.is_blinking = False
                        self.blink_count = 0
                self.root.after(50, blink_animation)
            blink_animation()

            # 修改 create_dynamic_pet_image 以支持眨眼
            old_create_dynamic_pet_image = self.create_dynamic_pet_image
            def create_dynamic_pet_image_with_blink(emotion, mouse_x, mouse_y):
                img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                pet_center_x = 40
                pet_center_y = 50

                blink = self.is_blinking

                if emotion == 'normal':
                    draw.ellipse([10, 20, 70, 70], fill='#4CAF50', outline='#2E7D32', width=2)
                    # 眼睛
                    if blink:
                        # 画闭眼（横线）
                        draw.line([25, 35, 35, 35], fill='black', width=3)
                        draw.line([45, 35, 55, 35], fill='black', width=3)
                    else:
                        draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                        draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                        left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
                        right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
                        draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
                        draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
                    draw.arc([35, 45, 45, 55], 0, 180, fill='black', width=2)

                elif emotion == 'happy':
                    draw.ellipse([10, 20, 70, 70], fill='#FFC107', outline='#FF8F00', width=2)
                    if blink:
                        draw.line([25, 35, 35, 35], fill='black', width=3)
                        draw.line([45, 35, 55, 35], fill='black', width=3)
                    else:
                        draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                        draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                        left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
                        right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
                        draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
                        draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
                    draw.arc([30, 40, 50, 60], 0, 180, fill='black', width=3)
                    draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
                    draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

                elif emotion == 'sleepy':
                    draw.ellipse([10, 20, 70, 70], fill='#2196F3', outline='#0D47A1', width=2)
                    # 困倦时始终闭眼
                    draw.ellipse([25, 33, 35, 37], fill='#FFFEFA', outline='black')
                    draw.ellipse([45, 33, 55, 37], fill='#FFFEFA', outline='black')
                    draw.line([25, 35, 35, 35], fill='black', width=2)
                    draw.line([45, 35, 55, 35], fill='black', width=2)
                    draw.ellipse([38, 48, 42, 52], fill='black')
                    z_count = (self.animation_frame // 5) % 4
                    z_text = "z" * z_count
                    draw.text((55, 15), z_text, fill='black')

                elif emotion == 'excited':
                    draw.ellipse([10, 20, 70, 70], fill='#F44336', outline='#B71C1C', width=2)
                    if blink:
                        draw.line([20, 32, 35, 32], fill='black', width=3)
                        draw.line([45, 32, 60, 32], fill='black', width=3)
                    else:
                        draw.ellipse([20, 25, 35, 40], fill='#FFFEFA', outline='black')
                        draw.ellipse([45, 25, 60, 40], fill='#FFFEFA', outline='black')
                        left_eye_x, left_eye_y = self.calculate_eye_position(27.5, 32.5, mouse_x, mouse_y)
                        right_eye_x, right_eye_y = self.calculate_eye_position(52.5, 32.5, mouse_x, mouse_y)
                        draw.ellipse([left_eye_x-2.5, left_eye_y-2.5, left_eye_x+2.5, left_eye_y+2.5], fill='black')
                        draw.ellipse([right_eye_x-2.5, right_eye_y-2.5, right_eye_x+2.5, right_eye_y+2.5], fill='black')
                    draw.ellipse([35, 45, 45, 55], fill='black')
                    draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
                    draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

                elif emotion == 'thinking':
                    draw.ellipse([10, 20, 70, 70], fill='#9C27B0', outline='#4A148C', width=2)
                    if blink:
                        draw.line([25, 32, 35, 32], fill='black', width=3)
                        draw.line([45, 32, 55, 32], fill='black', width=3)
                    else:
                        draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
                        draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
                        left_eye_x, left_eye_y = self.calculate_eye_position(30, 32, mouse_x, mouse_y-5)
                        right_eye_x, right_eye_y = self.calculate_eye_position(50, 32, mouse_x, mouse_y-5)
                        draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
                        draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
                    draw.arc([35, 50, 45, 55], 0, 180, fill='black', width=2)
                    draw.ellipse([55, 10, 65, 20], fill='white', outline='black')
                    draw.text((57, 12), "?", fill='black')

                elif emotion == 'curious':
                    draw.ellipse([10, 20, 70, 70], fill='#FF9800', outline='#E65100', width=2)
                    if blink:
                        draw.line([22, 35, 36, 35], fill='black', width=3)
                        draw.line([44, 35, 54, 35], fill='black', width=3)
                    else:
                        draw.ellipse([22, 28, 36, 42], fill='#FFFEFA', outline='black')
                        draw.ellipse([44, 30, 54, 40], fill='#FFFEFA', outline='black')
                        left_eye_x, left_eye_y = self.calculate_eye_position(29, 35, mouse_x, mouse_y)
                        right_eye_x, right_eye_y = self.calculate_eye_position(49, 35, mouse_x, mouse_y)
                        draw.ellipse([left_eye_x-3, left_eye_y-3, left_eye_x+3, left_eye_y+3], fill='black')
                        draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
                    draw.ellipse([37, 47, 43, 53], fill='black')
                    draw.text((60, 15), "!", fill='black')
                    draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
                    draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

                return ImageTk.PhotoImage(img)
            self.create_dynamic_pet_image = create_dynamic_pet_image_with_blink

    def create_dynamic_pet_image(self, emotion, mouse_x, mouse_y):
        """根据鼠标位置动态创建宠物图像"""
        # 创建图像
        img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 宠物在画布中的位置（相对于80x80图像）
        pet_center_x = 40
        pet_center_y = 50
        
        if emotion == 'normal':
            # 普通表情 - 绿色圆形身体
            draw.ellipse([10, 20, 70, 70], fill='#4CAF50', outline='#2E7D32', width=2)
            # 眼睛白色部分
            draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
            draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
            
            # 计算眼球位置
            # if self.mouse_over:
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
            # else:
            #     left_eye_x, left_eye_y = 30, 35
            #     right_eye_x, right_eye_y = 50, 35
            
            # 画眼球
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
            # 嘴巴
            draw.arc([35, 45, 45, 55], 0, 180, fill='black', width=2)

        elif emotion == 'happy':
            # 开心表情 - 黄色身体
            draw.ellipse([10, 20, 70, 70], fill='#FFC107', outline='#FF8F00', width=2)
            # 眼睛白色部分
            draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
            draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
            
            # 计算眼球位置
            # if self.mouse_over:
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
            # else:
            #     left_eye_x, left_eye_y = 30, 35
            #     right_eye_x, right_eye_y = 50, 35
            
            # 画眼球
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
            # 开心的嘴巴
            draw.arc([30, 40, 50, 60], 0, 180, fill='black', width=3)
            # 腮红
            draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
            draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

        elif emotion == 'sleepy':
            # 困倦表情 - 蓝色身体
            draw.ellipse([10, 20, 70, 70], fill='#2196F3', outline='#0D47A1', width=2)
            # 困倦的眼睛（闭着的，不跟随鼠标）
            draw.ellipse([25, 33, 35, 37], fill='#FFFEFA', outline='black')
            draw.ellipse([45, 33, 55, 37], fill='#FFFEFA', outline='black')
            draw.line([25, 35, 35, 35], fill='black', width=2)
            draw.line([45, 35, 55, 35], fill='black', width=2)
            # 小嘴巴
            draw.ellipse([38, 48, 42, 52], fill='black')
            # "zzz"动画 - 依次显示不同数量的z，形成动画效果
            z_count = (self.animation_frame // 5) % 4   # 0~3个z循环
            z_text = "z" * z_count
            draw.text((55, 15), z_text, fill='black')

        elif emotion == 'excited':
            # 兴奋表情 - 红色身体
            draw.ellipse([10, 20, 70, 70], fill='#F44336', outline='#B71C1C', width=2)
            # 大眼睛白色部分
            draw.ellipse([20, 25, 35, 40], fill='#FFFEFA', outline='black')
            draw.ellipse([45, 25, 60, 40], fill='#FFFEFA', outline='black')
            
            # 计算眼球位置（不同的眼睛中心）
            left_eye_x, left_eye_y = self.calculate_eye_position(27.5, 32.5, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(52.5, 32.5, mouse_x, mouse_y)

            
            # 画眼球
            draw.ellipse([left_eye_x-2.5, left_eye_y-2.5, left_eye_x+2.5, left_eye_y+2.5], fill='black')
            draw.ellipse([right_eye_x-2.5, right_eye_y-2.5, right_eye_x+2.5, right_eye_y+2.5], fill='black')
            # 兴奋的嘴巴
            draw.ellipse([35, 45, 45, 55], fill='black')
            # 腮红
            draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
            draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

        elif emotion == 'thinking':
            # 思考表情 - 紫色身体
            draw.ellipse([10, 20, 70, 70], fill='#9C27B0', outline='#4A148C', width=2)
            # 眼睛白色部分
            draw.ellipse([25, 30, 35, 40], fill='#FFFEFA', outline='black')
            draw.ellipse([45, 30, 55, 40], fill='#FFFEFA', outline='black')
            
            # 思考时眼睛倾向于向上看，但仍会跟随鼠标
            # if self.mouse_over:
                # 添加向上偏移
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 32, mouse_x, mouse_y-5)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 32, mouse_x, mouse_y-5)
            # else:
            #     left_eye_x, left_eye_y = 30, 32
            #     right_eye_x, right_eye_y = 50, 32
            
            # 画眼球
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
            # 思考的嘴巴
            draw.arc([35, 50, 45, 55], 0, 180, fill='black', width=2)
            # 思考泡泡
            draw.ellipse([55, 10, 65, 20], fill='white', outline='black')
            draw.text((57, 12), "?", fill='black')
                
        elif emotion == 'curious':
            # 好奇表情 - 橙色身体
            draw.ellipse([10, 20, 70, 70], fill='#FF9800', outline='#E65100', width=2)
            # 好奇的大眼睛白色部分（一大一小表示疑惑）
            draw.ellipse([22, 28, 36, 42], fill='#FFFEFA', outline='black')  # 左眼大一些
            draw.ellipse([44, 30, 54, 40], fill='#FFFEFA', outline='black')  # 右眼小一些
            
            # 计算眼球位置（不同大小的眼睛）
            # if self.mouse_over:
            left_eye_x, left_eye_y = self.calculate_eye_position(29, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(49, 35, mouse_x, mouse_y)
            # else:
            #     left_eye_x, left_eye_y = 29, 35
            #     right_eye_x, right_eye_y = 49, 35
            
            # 画眼球（左眼大一些）
            draw.ellipse([left_eye_x-3, left_eye_y-3, left_eye_x+3, left_eye_y+3], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')
            # 好奇的嘴巴（小圆形表示"哦"）
            draw.ellipse([37, 47, 43, 53], fill='black')
            # 感叹号表示惊讶
            draw.text((60, 15), "!", fill='black')
            # 腮红
            draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
            draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)
        
        return ImageTk.PhotoImage(img)

    def start_eye_tracking(self):
        """启动眼球追踪"""
        # 记录上次鼠标移动时间
        self.last_mouse_move_time = time.time()

        def track_eyes():
            if not self.is_hidden:
                # 更新宠物图像
                new_image = self.create_dynamic_pet_image(self.current_emotion, self.mouse_x, self.mouse_y)
                self.canvas.itemconfig(self.pet_sprite, image=new_image)
                # 保持引用避免被垃圾回收
                self.current_pet_image = new_image

                # 检查是否需要重置眼球位置
                if time.time() - self.last_mouse_move_time > 10:
                    # 回到默认位置（宠物中心）
                    self.mouse_x = self.pet_size // 2
                    self.mouse_y = self.total_height - self.pet_size // 2

            # 每100ms更新一次
            self.root.after(100, track_eyes)
        track_eyes()

        # 鼠标移动时更新last_mouse_move_time
        def on_mouse_motion_wrapper(event):
            self.last_mouse_move_time = time.time()
            pet_offset_x = (self.pet_size - 80) // 2
            pet_offset_y = self.total_height - self.pet_size
            self.mouse_x = event.x - pet_offset_x
            self.mouse_y = event.y - pet_offset_y
        # 重新绑定鼠标移动事件
        self.canvas.bind("<Motion>", on_mouse_motion_wrapper)

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建托盘图标图像（简化的宠物图标）
        tray_image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(tray_image)
        
        # 绘制可爱的宠物图标
        # 身体
        draw.ellipse([5, 15, 55, 55], fill='#4CAF50', outline='#2E7D32', width=2)
        # 眼睛
        draw.ellipse([15, 25, 25, 35], fill='white', outline='black')
        draw.ellipse([35, 25, 45, 35], fill='white', outline='black')
        draw.ellipse([18, 28, 22, 32], fill='black')
        draw.ellipse([38, 28, 42, 32], fill='black')
        # 嘴巴
        draw.arc([25, 35, 35, 45], 0, 180, fill='black', width=2)
        # 可爱的腮红
        draw.ellipse([8, 35, 15, 42], fill='#FF9999')
        draw.ellipse([45, 35, 52, 42], fill='#FF9999')
        
        # 创建托盘菜单
        menu = pystray.Menu(
            item('显示/隐藏宠物', self.toggle_pet_visibility, default=True),
            pystray.Menu.SEPARATOR,
            item('🐟 打开摸鱼提醒器', self.open_fish_reminder),
            pystray.Menu.SEPARATOR,
            # 表情切换子菜单
            item('切换表情', pystray.Menu(
                item('😊 开心', lambda: self.change_emotion('happy')),
                item('😴 困倦', lambda: self.change_emotion('sleepy')),
                item('🤔 思考', lambda: self.change_emotion('thinking')),
                item('🎉 兴奋', lambda: self.change_emotion('excited')),
                item('🤨 好奇', lambda: self.change_emotion('curious')),
                item('😐 普通', lambda: self.change_emotion('normal'))
            )),
            pystray.Menu.SEPARATOR,
            item('💬 随机说话', lambda: self.say_random_message('random')),
            item('📌 切换置顶', self.toggle_topmost),
            item('🎯 移到右下角', self.move_to_corner),
            pystray.Menu.SEPARATOR,
            item('❌ 退出程序', self.quit_app)
        )
        
        # 创建托盘图标对象
        self.tray_icon = pystray.Icon(
            "桌面宠物",
            tray_image,
            "桌面宠物 - 可爱的桌面伙伴",
            menu
        )

    def start_tray_icon(self):
        """在后台线程中启动托盘图标"""
        def run_tray():
            try:
                self.tray_icon.run()
            except Exception as e:
                print(f"托盘图标启动失败: {e}")
        
        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()

    def create_widgets(self):
        """创建界面元素"""
        # 主画布
        self.canvas = tk.Canvas(
            self.root, 
            width=self.pet_size, 
            height=self.total_height,
            bg='white',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # 显示宠物图像（位置调整到下方，为对话框留出空间）
        self.pet_sprite = self.canvas.create_image(
            self.pet_size//2, 
            self.total_height - self.pet_size//2, 
            image=self.pet_images[self.current_emotion]
        )
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🐟 打开摸鱼提醒器", command=self.open_fish_reminder)
        self.context_menu.add_separator()
        
        # 添加"切换心情"子菜单
        emotion_menu = tk.Menu(self.context_menu, tearoff=0)
        emotion_menu.add_command(label="😊 开心", command=lambda: self.change_emotion('happy'))
        emotion_menu.add_command(label="😴 困倦", command=lambda: self.change_emotion('sleepy'))
        emotion_menu.add_command(label="🤔 思考", command=lambda: self.change_emotion('thinking'))
        emotion_menu.add_command(label="🎉 兴奋", command=lambda: self.change_emotion('excited'))
        emotion_menu.add_command(label="🤨 好奇", command=lambda: self.change_emotion('curious'))
        emotion_menu.add_command(label="😐 普通", command=lambda: self.change_emotion('normal'))
        self.context_menu.add_cascade(label="切换心情", menu=emotion_menu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💬 随机说话", command=lambda: self.say_random_message('random'))
        self.context_menu.add_command(label="📌 置顶/取消置顶", command=self.toggle_topmost)
        self.context_menu.add_command(label="🎯 移到右下角", command=self.move_to_corner)
        self.context_menu.add_command(label="👁️ 隐藏到托盘", command=self.hide_to_tray)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 退出", command=self.quit_app)

    def bind_events(self):
        """绑定事件"""
        # 鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_context_menu)  # 右键菜单
        self.canvas.bind("<Double-Button-1>", self.on_double_click)  # 双击切换表情
        
        # 鼠标悬停事件
        self.canvas.bind("<Enter>", self.on_mouse_enter)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        self.canvas.bind("<Motion>", self.on_mouse_motion)  # 鼠标移动事件

    def on_mouse_motion(self, event):
        """鼠标移动事件"""
        # 转换为相对于宠物图像的坐标
        # 宠物图像是80x80，显示在100x150窗口的下方
        pet_offset_x = (self.pet_size - 80) // 2  # 居中偏移
        pet_offset_y = self.total_height - self.pet_size  # 下方偏移
        
        self.mouse_x = event.x - pet_offset_x
        self.mouse_y = event.y - pet_offset_y

    def update_interaction_time(self):
        """更新最后交互时间"""
        self.last_interaction_time = time.time()

    def start_behavior_monitoring(self):
        """开始行为监控 - 根据交互情况自动切换表情"""
        def monitor_behavior():
            if not self.is_hidden and not self.is_dragging and not self.mouse_over:
                current_time = time.time()
                idle_time = current_time - self.last_interaction_time
                
                # 根据空闲时间决定表情（只在鼠标不在宠物上时）
                if idle_time > self.idle_time_threshold:
                    # 超过300秒没有交互 - 困倦
                    if self.current_emotion != 'sleepy':
                        self.change_emotion('sleepy')
                        if random.random() < 0.3:  # 30%概率说话
                            self.say_random_message('sleepy')
                elif idle_time > self.thinking_time_threshold:
                    # 超过60秒没有交互 - 思考
                    if self.current_emotion not in ['sleepy', 'thinking']:
                        self.change_emotion('thinking')
                        if random.random() < 0.2:  # 20%概率说话
                            self.say_random_message('thinking')
            
            # 每5秒检查一次
            self.root.after(5000, monitor_behavior)
        
        # 5秒后开始监控
        self.root.after(5000, monitor_behavior)

    def create_speech_bubble(self, text):
        """创建对话框"""
        if self.is_hidden:
            return
            
        # 清除旧的对话框
        self.clear_speech_bubble()
        
        # 计算文本尺寸
        text_width = len(text) * 10  # 估算文本宽度
        text_height = 20
        
        # 对话框尺寸
        bubble_width = min(max(text_width + 20, 80), self.pet_size - 10)+10
        bubble_height = text_height + 20
        
        # 对话框位置（在宠物上方）
        bubble_x = self.pet_size // 2
        bubble_y = 30
        
        # 创建对话框背景（方形，带底色）
        self.speech_bubble = self.canvas.create_rectangle(
            bubble_x - bubble_width//2, bubble_y - bubble_height//2,
            bubble_x + bubble_width//2, bubble_y + bubble_height//2,
            fill='#FFFBEA', outline='#333333', width=2
        )
        
        # 创建对话框尾巴（三角形）
        tail_points = [
            bubble_x - 5, bubble_y + bubble_height//2,
            bubble_x + 5, bubble_y + bubble_height//2,
            bubble_x, bubble_y + bubble_height//2 + 10
        ]
        self.speech_tail = self.canvas.create_polygon(
            tail_points, fill='#FFFBEA', outline='#333333', width=2
        )
        
        # 创建文本
        self.speech_text = self.canvas.create_text(
            bubble_x, bubble_y,
            text=text,
            font=('微软雅黑', 10),
            fill='black',
            width=bubble_width - 10,
            justify='center'
        )
        
        self.is_speaking = True
        
        # 3秒后自动清除对话框
        self.root.after(3000, self.clear_speech_bubble)

    def clear_speech_bubble(self):
        """清除对话框"""
        if self.speech_bubble:
            self.canvas.delete(self.speech_bubble)
            self.speech_bubble = None
        if hasattr(self, 'speech_tail') and self.speech_tail:
            self.canvas.delete(self.speech_tail)
            self.speech_tail = None
        if self.speech_text:
            self.canvas.delete(self.speech_text)
            self.speech_text = None
        self.is_speaking = False

    def say_random_message(self, category='random'):
        """随机说话"""
        if category in self.hello_messages:
            message = random.choice(self.hello_messages[category])
            self.create_speech_bubble(message)

    def on_click(self, event):
        """鼠标点击事件 - 开心表情并随机说话"""
        # 更新交互时间
        self.update_interaction_time()
        
        # 判断点击位置，如果点击在宠物身上才响应
        pet_y = self.total_height - self.pet_size//2
        if event.y > pet_y - 40:  # 点击在宠物附近
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # 点击时表现开心
            self.change_emotion('happy')
            
            # 随机说开心的话
            categories = ['greeting', 'happy', 'work', 'random']
            category = random.choice(categories)
            self.say_random_message(category)

    def on_drag(self, event):
        """拖拽事件 - 好奇表情"""
        if self.is_dragging:
            # 更新交互时间
            self.update_interaction_time()
            
            # 拖拽时表现好奇
            if self.current_emotion != 'curious':
                self.change_emotion('curious')
                if random.random() < 0.5:  # 50%概率说话
                    self.say_random_message('curious')
            
            # 计算新位置
            x = self.root.winfo_x() + (event.x - self.drag_start_x)
            y = self.root.winfo_y() + (event.y - self.drag_start_y)
            
            # 限制在屏幕范围内
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            x = max(0, min(x, screen_width - self.pet_size))
            y = max(0, min(y, screen_height - self.total_height))
            
            self.root.geometry(f"+{x}+{y}")

    def on_release(self, event):
        """鼠标释放事件"""
        self.is_dragging = False
        # 更新交互时间
        self.update_interaction_time()

    def on_double_click(self, event):
        """双击事件 - 兴奋表情并说话"""
        # 更新交互时间
        self.update_interaction_time()
        
        # 双击时表现兴奋
        self.change_emotion('excited')
        self.say_random_message('excited')

    def on_mouse_enter(self, event):
        """鼠标进入事件"""
        # 更新交互时间和鼠标状态
        self.update_interaction_time()
        self.mouse_over = True
        
        if not self.is_dragging and not self.is_speaking:
            if random.random() < 0.3:  # 30%概率说话
                self.say_random_message('greeting')
            # 鼠标悬停时表现开心
            if self.current_emotion not in ['excited', 'curious']:
                self.change_emotion('happy')

    def on_mouse_leave(self, event):
        """鼠标离开事件"""
        # 更新鼠标状态
        self.mouse_over = False
        
        if not self.is_dragging:
            # 鼠标离开后恢复normal状态
            self.root.after(1000, lambda: self.change_emotion('normal') if not self.mouse_over else None)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 更新交互时间
        self.update_interaction_time()
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def change_emotion(self, emotion):
        """改变宠物表情"""
        if emotion in self.emotions and not self.is_hidden:
            self.current_emotion = emotion
        # 如果emotion是tired，身体不再抖动
        if emotion == 'tired':
            self.is_bobbing = False
        else:
            self.is_bobbing = True

    def start_animation(self):
        """开始动画循环"""
        def animate():
            if not self.is_hidden:
                # 简单的浮动动画
                self.animation_frame += 1
                offset = int(2 * abs(self.animation_frame % 20 - 10) / 10)
                
                # 更新宠物位置（轻微上下浮动）
                self.canvas.coords(
                    self.pet_sprite, 
                    self.pet_size//2, 
                    self.total_height - self.pet_size//2 + offset
                )
            
            # 继续动画
            self.root.after(100, animate)
        
        animate()

    def toggle_topmost(self):
        """切换置顶状态"""
        # 更新交互时间
        self.update_interaction_time()
        
        current_topmost = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current_topmost)
        
        if current_topmost:
            self.change_emotion('sleepy')
            self.say_random_message('sleepy')
            if self.tray_icon:
                self.tray_icon.notify("已取消置顶", "桌面宠物")
        else:
            self.change_emotion('excited')
            self.create_speech_bubble("我现在在最前面啦！")
            if self.tray_icon:
                self.tray_icon.notify("已设置置顶", "桌面宠物")

    def move_to_corner(self):
        """移动到右下角"""
        # 更新交互时间
        self.update_interaction_time()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.pet_size - 50
        y = screen_height - self.total_height - 100
        self.root.geometry(f"+{x}+{y}")
        self.change_emotion('happy')
        self.create_speech_bubble("我回到角落里啦~")
        if self.tray_icon:
            self.tray_icon.notify("已移动到右下角", "桌面宠物")

    def toggle_pet_visibility(self):
        """切换宠物显示/隐藏"""
        if self.is_hidden:
            self.show_pet()
        else:
            self.hide_to_tray()

    def hide_to_tray(self):
        """隐藏到托盘"""
        self.is_hidden = True
        self.mouse_over = False  # 重置鼠标状态
        self.clear_speech_bubble()  # 清除对话框
        self.root.withdraw()  # 隐藏窗口

    def show_pet(self):
        """显示宠物"""
        self.is_hidden = False
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 提升到前台
        self.root.focus_force()  # 获取焦点
        
        # 重新显示时更新交互时间并表现兴奋
        self.update_interaction_time()
        self.change_emotion('excited')
        self.create_speech_bubble("我回来啦！想我了吗？")

    def _start_fish_reminder(self, fish_reminder_path):
        """启动摸鱼提醒器"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包后模式 - 调用exe
                base_path = os.path.dirname(sys.executable)
                exe_path = os.path.join(base_path, "TouchFishReminder.exe")
                self.fish_reminder_process = subprocess.Popen(
                    [exe_path],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # 开发模式 - 调用python脚本
                current_dir = os.path.dirname(os.path.abspath(__file__))
                fish_reminder_path = os.path.join(current_dir, "TouchFishReminder.py")
                if os.path.exists(fish_reminder_path):
                   # 打开TouchFishReminder.py
                   self.fish_reminder_process = subprocess.Popen(
                       [sys.executable, fish_reminder_path],
                       creationflags=subprocess.CREATE_NO_WINDOW
                   )
        except Exception as e:
            print(f"启动摸鱼提醒器失败: {e}")

    # def _start_fish_reminder(self):
    #     import TouchFishReminder as TFR
    #     TFR.run()

    def _handle_error(self, error_msg):
        """内部方法：处理错误"""
        if self.tray_icon:
            self.tray_icon.notify(error_msg, "错误")
        else:
            messagebox.showerror("错误", error_msg)
        self.change_emotion('sleepy')
        self.create_speech_bubble("咦？出了点小问题...")

    def open_fish_reminder(self):
        """打开摸鱼提醒器GUI"""
        self.update_interaction_time()
        
        # 检查是否已运行
        if self.fish_reminder_process and self.fish_reminder_process.poll() is None:
            if self.tray_icon:
                self.tray_icon.notify("摸鱼提醒器已经在运行中！", "桌面宠物")
            self.change_emotion('normal')
            self.create_speech_bubble("摸鱼提醒器已经开着呢~")
            return
        
        # 获取路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fish_reminder_path = os.path.join(current_dir, "TouchFishReminder.py")
        if not os.path.exists(fish_reminder_path):
            fish_reminder_path = "TouchFishReminder.exe"
        if os.path.exists(fish_reminder_path):
            self._start_fish_reminder(fish_reminder_path)
        else:
            print("摸鱼提醒器文件不存在，请检查路径！")
        # try:
        #     self._start_fish_reminder()
        # except Exception as e:
        #     self._handle_error(f"启动摸鱼提醒器失败: {e}")

    def quit_app(self):
        """退出应用"""
        # 关闭摸鱼提醒器进程
        if self.fish_reminder_process and self.fish_reminder_process.poll() is None:
            self.fish_reminder_process.terminate()
        
        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def run(self):
        """运行宠物"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
        except Exception as e:
            print(f"程序运行出错: {e}")
            self.quit_app()

if __name__ == "__main__":
    try:
        print("🐾 桌面宠物启动中...")
        pet = DesktopPet()
        print("✨ 桌面宠物已启动！")
        print("📌 使用说明：")
        print("   • 默认状态：normal表情")
        print("   • 点击宠物：开心表情并说话")
        print("   • 拖拽移动：好奇表情")
        print("   • 双击宠物：兴奋表情")
        print("   • 鼠标悬停：开心表情，眼睛跟随鼠标")
        print("   • 鼠标离开：恢复normal表情")
        print("   • 待机60秒：思考表情")
        print("   • 待机300秒：困倦表情")
        print("   • 眼睛会智能跟随鼠标方向！")
        print("   • 右键打开菜单")
        print("   • 托盘图标可控制显示/隐藏")
        pet.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("📋 可能的解决方案：")
        print("   1. 确保已安装 Pillow: pip install Pillow")
        print("   2. 确保已安装 pystray: pip install pystray")
        input("按回车键退出...")
