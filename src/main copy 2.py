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

import yaml
from typing import Dict, Any, List

class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.configs = {
            'main': None,
            'messages': None
        }
        
    def load_all_configs(self) -> Dict[str, Any]:
        """加载所有配置文件"""
        try:
            self.configs['main'] = self._load_config('config.yaml')
            self.configs['messages'] = self._load_config('messages.yaml')
            return self.configs
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 提供默认配置
            return self._get_default_configs()

    def _load_config(self, filename: str) -> Dict[str, Any]:
        """加载单个YAML文件"""
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def _get_default_configs(self) -> Dict[str, Any]:
        """获取默认配置（当文件加载失败时使用）"""
        return {
            'main': {
                'pet': {
                    'size': 100,
                    'total_height': 150,
                    'animation_speed': 500,
                    'idle_time_threshold': 300,
                    'thinking_time_threshold': 60,
                    'blink_interval_min': 80,
                    'blink_interval_max': 150,
                    'blink_duration': 8
                },
                'initial_position': {
                    'x': 'right-50',
                    'y': 'bottom-100'
                },
                'eye_tracking': {
                    'max_radius': 3
                }
            },
            'messages': {
                'greeting': ["你好呀！我是你的桌面宠物~"],
                'happy': ["我今天心情特别好！"],
                'sleepy': ["好困啊...想睡觉了"],
                'excited': ["哇！好兴奋啊！"],
                'thinking': ["让我想想..."],
                'curious': ["咦？这是什么？"],
                'work': ["工作要加油哦！"],
                'random': ["我会一直陪着你的~"]
            }
        }

    def get_main_config(self) -> Dict[str, Any]:
        """获取主配置"""
        return self.configs['main'] or self._get_default_configs()['main']

    def get_messages_config(self) -> Dict[str, List[str]]:
        """获取消息配置"""
        return self.configs['messages'] or self._get_default_configs()['messages']



class BasePet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面宠物")
        self.root.overrideredirect(True)  # 去除窗口边框和标题栏，使窗口无边框
        self.root.attributes('-topmost', True)  # 设置窗口始终置顶
        self.root.attributes('-transparentcolor', 'white')  # 设置窗口白色为透明，实现宠物悬浮效果

        self.load_config()
        print("配置加载完成:", self.pet_config)


        # 获取屏幕宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 计算宠物窗口移动到右下角的位置
        x = screen_width - self.pet_size - 150  # 距离屏幕右侧150像素
        y = screen_height - self.total_height - 200  # 距离屏幕底部200像素
        # 设置窗口位置到右下角
        self.root.geometry(f"+{x}+{y}")

        self.emotions = ['normal', 'happy', 'sleepy', 'excited', 'thinking', 'curious']
        self.current_emotion = 'normal'
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.last_interaction_time = time.time()
        
        # 鼠标状态追踪
        self.mouse_over = False  # 追踪鼠标是否在宠物上方
        self.mouse_x = 0  # 鼠标相对于宠物的X坐标
        self.mouse_y = 0  # 鼠标相对于宠物的Y坐标

        # 说话相关
        self.is_speaking = False
        self.speech_bubble = None
        self.speech_text = None
        self.talk_messages = self.messages_config

        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.animation_frame = 0    # 动画帧
        self.animation_speed = 500   # 动画速度
        self.expand_scale = 3  # 扩展区域相对于宠物图像的比例
        self.tray_icon = None
        self.tray_thread = None
        self.is_hidden = False
        self.fish_reminder_process = None

        print("BasePet initialized.")

    def create_widgets(self):
        """
        初始化并创建宠物应用的主界面控件。
        """

        # 新增底层透明扩展图层
        self.expand_canvas = tk.Canvas(
            self.root,
            width=self.pet_size * self.expand_scale,
            height=self.total_height * self.expand_scale,
            bg='red',  # 透明色由窗口属性控制
            highlightthickness=0
        )
        # 让扩展canvas与root窗口左上角对齐
        self.expand_canvas.place(x=0, y=0)

        # 原有宠物主canvas，放在窗口的中间偏下
        canvas_x = (self.root.winfo_width() - self.pet_size) // 2
        canvas_y = int(self.root.winfo_height() * 4/7 - self.total_height // 2)
        # 由于窗口刚创建时winfo_width和winfo_height可能为1，需要用geometry设置后再update
        self.root.update_idletasks()
        canvas_x = (self.root.winfo_width() - self.pet_size) // 2
        canvas_y = int(self.root.winfo_height() * 4 / 7 - self.total_height // 2)
        self.canvas = tk.Canvas(
            self.root,
            width=self.pet_size,
            height=self.total_height,
            bg='white',
            highlightthickness=0
        )
        self.canvas.place(x=canvas_x, y=canvas_y)

        self.pet_sprite = self.canvas.create_image(
            self.pet_size // 2,
            self.total_height - self.pet_size // 2,
            image=None
        )
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🐟 打开摸鱼提醒器", command=self.open_fish_reminder)
        self.context_menu.add_separator()
        emotion_menu = tk.Menu(self.context_menu, tearoff=0)
        for emo in self.emotions:
            emotion_menu.add_command(label=emo, command=lambda e=emo: self.change_emotion(e))
        self.context_menu.add_cascade(label="切换心情", menu=emotion_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="💬 随机说话", command=lambda: self.say_random_message('random'))
        self.context_menu.add_command(label="📌 置顶/取消置顶", command=self.toggle_topmost)
        self.context_menu.add_command(label="🎯 移到右下角", command=self.move_to_corner)
        self.context_menu.add_command(label="👁️ 隐藏到托盘", command=self.hide_to_tray)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 退出", command=self.quit_app)




    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Enter>", self.on_mouse_enter)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        self.expand_canvas.bind("<Motion>", self.on_mouse_motion)

    def on_click(self, event):
        pass

    def on_drag(self, event):
        pass

    def on_release(self, event):
        pass

    def on_double_click(self, event):
        pass

    def on_mouse_enter(self, event):
        pass

    def on_mouse_leave(self, event):
        pass

    def show_context_menu(self, event):
        pass

    def on_mouse_motion(self, event):
        """鼠标移动事件"""
        # 转换为相对于宠物图像的坐标
        # 宠物图像是80x80，显示在100x150窗口的下方
        pet_offset_x = (self.pet_size - 80) // 2  # 居中偏移
        pet_offset_y = self.total_height - self.pet_size  # 下方偏移
        # mouse_x, mouse_y是相对于窗口的坐标
        self.mouse_x = event.x - pet_offset_x
        self.mouse_y = event.y - pet_offset_y
        # 记录本次鼠标移动时间
        self.last_mouse_move_time = time.time()
        print('last_mouse_move_time:', self.last_mouse_move_time)

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建托盘图标图像（简化的宠物图标）
        tray_image_path = r"D:\python工程\cute pet\image\tray_ico.png"
        tray_image = Image.open(tray_image_path).resize((64, 64), Image.LANCZOS)

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

        self.tray_thread = threading.Thread(target=run_tray, daemon=True)  # 将线程设置为守护线程
        self.tray_thread.start()

    def hide_to_tray(self):
        """隐藏到托盘"""
        self.is_hidden = True
        self.mouse_over = False  # 重置鼠标状态
        self.clear_speech_bubble()  # 清除对话框
        self.root.withdraw()  # 隐藏窗口

    def start_behavior_monitoring(self):
        pass

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
        if category in self.talk_messages:
            message = random.choice(self.talk_messages[category])
            self.create_speech_bubble(message)

    def change_emotion(self, emotion):
        pass

    def toggle_topmost(self):
        pass

    def move_to_corner(self):
        pass

    def toggle_pet_visibility(self):
        """切换宠物显示/隐藏"""
        if self.is_hidden:
            self.show_pet()
        else:
            self.hide_to_tray()


    def show_pet(self):
        pass

    def update_interaction_time(self):
        """更新最后交互时间"""
        self.last_interaction_time = time.time()

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
        self.root.mainloop()
    def load_config(self):
        self.config_loader = ConfigLoader()
        self.configs = self.config_loader.load_all_configs()
        self.main_config = self.config_loader.get_main_config()
        self.messages_config = self.config_loader.get_messages_config()

        # 从配置中获取窗口大小
        self.pet_config = self.main_config.get('pet', {})
        self.pet_size = self.pet_config.get('size', 100)
        self.total_height = self.pet_config.get('total_height', 150)  # 增加高度来容纳对话框
        self.root.geometry(f"{self.pet_size*3}x{self.total_height*2}")
        
        # 获取屏幕尺寸并设置初始位置（右下角）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 解析初始位置配置
        pos_config = self.main_config.get('initial_position', {})
        x_pos = pos_config.get('x', 'right-50')
        y_pos = pos_config.get('y', 'bottom-100')
        # 计算初始位置
        if x_pos.startswith('right-'):
            offset = int(x_pos.split('-')[1])
            x = screen_width - self.pet_size - offset
        else:
            x = int(x_pos)
            
        if y_pos.startswith('bottom-'):
            offset = int(y_pos.split('-')[1])
            y = screen_height - self.total_height - offset
        else:
            y = int(y_pos)
        self.root.geometry(f"+{x}+{y}")

        self.idle_time_threshold = self.pet_config.get('idle_time_threshold', 300)  # 进入困倦状态的时间阈值，单位秒
        self.thinking_time_threshold = self.pet_config.get('thinking_time_threshold', 60)  # 进入思考状态的时间阈值，单位秒

class DesktopPet(BasePet):
    def __init__(self):
        super().__init__()
        # 宠物状态
        self.emotions = ['normal', 'happy', 'sleepy', 'excited', 'thinking', 'curious']
        self.current_emotion = 'normal'  # 初始状态为正常

        # 从配置中获取时间相关参数
        self.last_interaction_time = time.time()

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
        for emotion in self.emotions:
            self.pet_images[emotion] = self.create_dynamic_pet_image_with_blink(emotion, self.mouse_x, self.mouse_y)

    def create_dynamic_pet_image_with_blink(self, emotion, mouse_x, mouse_y):
        # 根据是否眨眼选择不同的图片
        if self.is_blinking:
            image_path = rf"D:\python工程\cute pet\image\blink_{emotion}.png"
        else:
            image_path = rf"D:\python工程\cute pet\image\defaultPet_{emotion}.png"
        
        # 加载图片
        img = Image.open(image_path).convert('RGBA')
        draw = ImageDraw.Draw(img)
        
        # 如果不是困倦状态且没有眨眼，绘制动态眼球
        if emotion != 'sleepy' and not self.is_blinking:
            self.draw_eyes_with_movement(draw, emotion, mouse_x, mouse_y)
        
        return ImageTk.PhotoImage(img)

    def draw_eyes_with_movement(self, draw, emotion, mouse_x, mouse_y):
        """绘制带有动态追踪效果的眼球"""
        if emotion == 'normal':
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')

        elif emotion == 'happy':
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 35, mouse_x, mouse_y)
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')

        elif emotion == 'excited':
            left_eye_x, left_eye_y = self.calculate_eye_position(27.5, 32.5, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(52.5, 32.5, mouse_x, mouse_y)
            draw.ellipse([left_eye_x-2.5, left_eye_y-2.5, left_eye_x+2.5, left_eye_y+2.5], fill='black')
            draw.ellipse([right_eye_x-2.5, right_eye_y-2.5, right_eye_x+2.5, right_eye_y+2.5], fill='black')

        elif emotion == 'thinking':
            left_eye_x, left_eye_y = self.calculate_eye_position(30, 32, mouse_x, mouse_y-5)
            right_eye_x, right_eye_y = self.calculate_eye_position(50, 32, mouse_x, mouse_y-5)
            draw.ellipse([left_eye_x-2, left_eye_y-2, left_eye_x+2, left_eye_y+2], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')

        elif emotion == 'curious':
            left_eye_x, left_eye_y = self.calculate_eye_position(29, 35, mouse_x, mouse_y)
            right_eye_x, right_eye_y = self.calculate_eye_position(49, 35, mouse_x, mouse_y)
            draw.ellipse([left_eye_x-3, left_eye_y-3, left_eye_x+3, left_eye_y+3], fill='black')
            draw.ellipse([right_eye_x-2, right_eye_y-2, right_eye_x+2, right_eye_y+2], fill='black')

    def start_eye_tracking(self):
        """启动眼球追踪"""   
        self.last_mouse_move_time = time.time()
        def track_eyes():
            if not self.is_hidden:
                # 更新宠物图像
                new_image = self.create_dynamic_pet_image_with_blink(self.current_emotion, self.mouse_x, self.mouse_y)
                self.canvas.itemconfig(self.pet_sprite, image=new_image)
                # 保持引用避免被垃圾回收
                self.current_pet_image = new_image

                # 检查是否需要重置眼球位置
                if time.time() - self.last_mouse_move_time > 5:# 单位秒
                    # 回到默认位置（宠物中心）
                    print('reset mouse position',"time:",time.time())
                    self.mouse_x = self.pet_size // 2
                    self.mouse_y = self.total_height - self.pet_size // 2

            # 每100ms更新一次
            self.root.after(100, track_eyes)
        track_eyes()

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
            self.root.after(2000, lambda: self.change_emotion('normal') if not self.mouse_over else None)

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



    def _handle_error(self, error_msg):
        """内部方法：处理错误"""
        if self.tray_icon:
            self.tray_icon.notify(error_msg, "错误")
        else:
            messagebox.showerror("错误", error_msg)
        self.change_emotion('sleepy')
        self.create_speech_bubble("咦？出了点小问题...")

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
        pet.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("📋 可能的解决方案：")
        print("   1. 确保已安装 Pillow: pip install Pillow")
        print("   2. 确保已安装 pystray: pip install pystray")
        input("按回车键退出...")
