import tkinter as tk
from tkinter import messagebox, ttk
import threading
import random
import time
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import sys
import subprocess
import platform
import datetime
import re
import json

class FishReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("摸鱼提醒器")
        self.root.geometry("400x400")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 默认提醒语句
        self.reminders = [
            "别忘了休息一下，放松放松！",
            "工作再忙，也要记得摸鱼哦！",
            "适当的摸鱼可以提高工作效率！",
            "不要让自己太累，来点摸鱼吧！",
            "摸鱼时间到，放松一下吧！",
            "眼睛酸了吧？看看远方放松一下",
            "坐久了，起来活动活动筋骨吧！",
            "喝口水，补充水分很重要哦",
            "深呼吸几次，给大脑充充氧",
            "听首轻音乐，舒缓一下心情"
        ]

        def load_reminders_from_json(self, filename):
            """从JSON文件加载提醒语句（格式：{关键词: [提醒语句, ...]}）"""
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for keyword, messages in data.items():
                        if isinstance(messages, list):
                            self.reminder_dict[keyword] = [str(msg).strip() for msg in messages if str(msg).strip()]
                # 如果有自定义提醒则覆盖默认提醒
                if self.reminder_dict:
                # 默认提醒语句为所有提醒的合集
                    self.reminders = [msg for msgs in self.reminder_dict.values() for msg in msgs]
            except FileNotFoundError:
                pass  # 文件不存在则使用默认提醒
            except Exception as e:
                print(f"读取提醒语句JSON文件失败: {e}")

        def get_reminders_by_keyword(self, keyword):
            """根据关键词获取提醒语句列表"""
            return self.reminder_dict.get(keyword, [])

        # 时间提醒设置
        self.meal_reminders = {
            'breakfast': {'time': '08:00', 'enabled': True, 'message': '🍳 早餐时间到了！记得吃早餐哦，一日之计在于晨！'},
            'lunch': {'time': '12:00', 'enabled': True, 'message': '🍛 午餐时间到了！好好吃饭，下午才有精神工作！'},
            'dinner': {'time': '18:00', 'enabled': True, 'message': '🍽️ 晚餐时间到了！辛苦一天了，好好享受晚餐吧！'}
        }
        
        self.work_reminder = {
            'time': '18:00', 
            'enabled': True, 
            'message': '⏰ 下班时间到了！今天辛苦了，记得准时下班哦！'
        }
        
        self.sleep_reminder = {
            'time': '22:00', 
            'enabled': True, 
            'message': '😴 该睡觉了！早睡早起身体好，明天继续摸鱼！'
        }
        print("初始化摸鱼提醒器")

        self.interval_var = tk.IntVar(value=30)
        self.running = False
        self.time_reminder_running = False
        self.thread = None
        self.time_thread = None
        self.tray_icon = None
        self.hidden_to_tray = False

        self.create_widgets()
        self.create_tray_icon()
        self.start_time_reminder()

    def create_widgets(self):
        # 创建notebook来组织界面
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 摸鱼提醒标签页
        fish_frame = ttk.Frame(notebook)
        notebook.add(fish_frame, text="摸鱼提醒")
        self.create_fish_reminder_widgets(fish_frame)
        
        # 时间提醒标签页
        time_frame = ttk.Frame(notebook)
        notebook.add(time_frame, text="时间提醒")
        self.create_time_reminder_widgets(time_frame)

    def create_fish_reminder_widgets(self, parent):
        # 标题
        title_label = tk.Label(parent, text="🐟 摸鱼提醒器 🐟", 
                              font=("微软雅黑", 14, "bold"))
        title_label.pack(pady=10)
        
        # 间隔设置
        tk.Label(parent, text="提醒间隔(分钟):").pack(pady=5)
        interval_frame = tk.Frame(parent)
        interval_frame.pack()
        tk.Entry(interval_frame, textvariable=self.interval_var, 
                width=10, justify='center').pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="开始提醒", command=self.start_reminder,
                 bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="停止提醒", command=self.stop_reminder,
                 bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        
        # 窗口控制按钮
        control_frame = tk.Frame(parent)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="隐藏到系统托盘", command=self.hide_to_tray,
                 bg="#2196F3", fg="white", width=15).pack(pady=2)
        
        # 测试按钮
        tk.Button(control_frame, text="测试通知", command=self.test_notification,
                 bg="#FF9800", fg="white", width=15).pack(pady=2)
        
        # 状态显示
        self.status_label = tk.Label(parent, text="状态：未启动", 
                                   fg="gray", font=("微软雅黑", 9))
        self.status_label.pack(pady=5)

    def create_time_reminder_widgets(self, parent):
        # 时间提醒标题
        title_label = tk.Label(parent, text="⏰ 时间提醒设置", 
                              font=("微软雅黑", 12, "bold"))
        title_label.pack(pady=10)
        
        # 滚动框架
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 三餐提醒设置
        meals_frame = tk.LabelFrame(scrollable_frame, text="🍽️ 三餐提醒", 
                                   font=("微软雅黑", 10, "bold"))
        meals_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.meal_vars = {}
        self.meal_time_vars = {}
        
        meals = [
            ('breakfast', '早餐'),
            ('lunch', '午餐'), 
            ('dinner', '晚餐')
        ]
        
        for meal_key, meal_name in meals:
            frame = tk.Frame(meals_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 复选框
            var = tk.BooleanVar(value=self.meal_reminders[meal_key]['enabled'])
            self.meal_vars[meal_key] = var
            tk.Checkbutton(frame, text=meal_name, variable=var,
                          command=lambda k=meal_key: self.update_meal_setting(k)).pack(side=tk.LEFT)
            
            # 时间设置
            tk.Label(frame, text="时间:").pack(side=tk.LEFT, padx=(10, 2))
            time_var = tk.StringVar(value=self.meal_reminders[meal_key]['time'])
            self.meal_time_vars[meal_key] = time_var
            time_entry = tk.Entry(frame, textvariable=time_var, width=8)
            time_entry.pack(side=tk.LEFT, padx=2)
            time_entry.bind('<Return>', lambda e, k=meal_key: self.update_meal_time(k))
            time_entry.bind('<Return>', lambda e, k=meal_key: self.update_meal_time(k))

            tk.Label(frame, text="(格式: HH:MM)").pack(side=tk.LEFT, padx=(2, 0))
        
        # 下班提醒设置
        work_frame = tk.LabelFrame(scrollable_frame, text="💼 下班提醒", 
                                  font=("微软雅黑", 10, "bold"))
        work_frame.pack(fill=tk.X, padx=10, pady=5)
        
        work_setting_frame = tk.Frame(work_frame)
        work_setting_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.work_var = tk.BooleanVar(value=self.work_reminder['enabled'])
        tk.Checkbutton(work_setting_frame, text="启用下班提醒", variable=self.work_var,
                      command=self.update_work_setting).pack(side=tk.LEFT)
        
        tk.Label(work_setting_frame, text="时间:").pack(side=tk.LEFT, padx=(10, 2))
        self.work_time_var = tk.StringVar(value=self.work_reminder['time'])
        work_time_entry = tk.Entry(work_setting_frame, textvariable=self.work_time_var, width=8)
        work_time_entry.pack(side=tk.LEFT, padx=2)
        work_time_entry.bind('<Return>', self.update_work_time)
        
        tk.Label(work_setting_frame, text="(格式: HH:MM)").pack(side=tk.LEFT, padx=(2, 0))
        
        # 睡觉提醒设置
        sleep_frame = tk.LabelFrame(scrollable_frame, text="😴 睡觉提醒", 
                                   font=("微软雅黑", 10, "bold"))
        sleep_frame.pack(fill=tk.X, padx=10, pady=5)
        
        sleep_setting_frame = tk.Frame(sleep_frame)
        sleep_setting_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.sleep_var = tk.BooleanVar(value=self.sleep_reminder['enabled'])
        tk.Checkbutton(sleep_setting_frame, text="启用睡觉提醒", variable=self.sleep_var,
                      command=self.update_sleep_setting).pack(side=tk.LEFT)
        
        tk.Label(sleep_setting_frame, text="时间:").pack(side=tk.LEFT, padx=(10, 2))
        self.sleep_time_var = tk.StringVar(value=self.sleep_reminder['time'])
        sleep_time_entry = tk.Entry(sleep_setting_frame, textvariable=self.sleep_time_var, width=8)
        sleep_time_entry.pack(side=tk.LEFT, padx=2)
        sleep_time_entry.bind('<Return>', self.update_sleep_time)
        
        tk.Label(sleep_setting_frame, text="(格式: HH:MM)").pack(side=tk.LEFT, padx=(2, 0))
        
        # 测试按钮
        # test_frame = tk.Frame(scrollable_frame)
        # test_frame.pack(pady=10)
        
        # tk.Button(test_frame, text="测试三餐提醒", command=self.test_meal_notification,
        #          bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        # tk.Button(test_frame, text="测试下班提醒", command=self.test_work_notification,
        #          bg="#2196F3", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        # tk.Button(test_frame, text="测试睡觉提醒", command=self.test_sleep_notification,
        #          bg="#9C27B0", fg="white", width=12).pack(side=tk.LEFT, padx=5)

        # 时间提醒状态
        self.time_status_label = tk.Label(scrollable_frame, text="时间提醒：运行中", 
                                        fg="green", font=("微软雅黑", 9))
        self.time_status_label.pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def validate_time(self, time_str):
        """验证时间格式"""
        try:
            datetime.datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def revalidate_time(self, time_str, default_value = None):
        """标准化时间格式"""
        time_str = re.sub(r'\s+', '', time_str)
        time_str = re.sub(r'(\d{2})\D(\d{2})', r'\1:\2', time_str)
        if self.validate_time(time_str):
            return time_str
        else:
            messagebox.showerror("时间格式错误", f"请输入正确的时间格式 (HH:MM)")
            return None

    def update_meal_setting(self, meal_key):
        """更新三餐提醒设置"""
        self.meal_reminders[meal_key]['enabled'] = self.meal_vars[meal_key].get()

    def update_meal_time(self, meal_key):
        """更新三餐时间"""
        time_str = self.meal_time_vars[meal_key].get()
        time_str = self.revalidate_time(time_str)
        if time_str:
            self.meal_reminders[meal_key]['time'] = time_str
            messagebox.showinfo("时间更新", f"{meal_key.capitalize()}时间已更新为 {time_str}")
        else:
            self.meal_time_vars[meal_key].set(self.meal_reminders[meal_key]['time'])

    def update_work_setting(self):
        """更新下班提醒设置"""
        self.work_reminder['enabled'] = self.work_var.get()

    def update_work_time(self, event=None):
        """更新下班时间"""
        time_str = self.work_time_var.get()
        time_str = self.revalidate_time(time_str)
        if time_str:
            self.work_reminder['time'] = time_str
            messagebox.showinfo("时间更新", f"下班时间已更新为 {time_str}")
        else:
            self.work_time_var.set(self.work_reminder['time'])

    def update_sleep_setting(self):
        """更新睡觉提醒设置"""
        self.sleep_reminder['enabled'] = self.sleep_var.get()

    def update_sleep_time(self, event=None):
        """更新睡觉时间"""
        time_str = self.sleep_time_var.get()
        time_str = self.revalidate_time(time_str)
        if time_str:
            self.sleep_reminder['time'] = time_str
            messagebox.showinfo("时间更新", f"睡觉时间已更新为 {time_str}")
        else:
            self.sleep_time_var.set(self.sleep_reminder['time'])


    def start_time_reminder(self):
        """启动时间提醒"""
        if not self.time_reminder_running:
            self.time_reminder_running = True
            self.time_thread = threading.Thread(target=self.time_reminder_loop, daemon=True)
            self.time_thread.start()

    def time_reminder_loop(self):
        """时间提醒循环"""
        last_check_time = ""
        
        while self.time_reminder_running:
            current_time = datetime.datetime.now().strftime("%H:%M")
            
            # 避免同一分钟内重复提醒
            if current_time != last_check_time:
                last_check_time = current_time
                
                # 检查三餐提醒
                for meal_key, meal_data in self.meal_reminders.items():
                    if meal_data['enabled'] and meal_data['time'] == current_time:
                        self.show_time_reminder(meal_data['message'])
                
                # 检查下班提醒
                if (self.work_reminder['enabled'] and 
                    self.work_reminder['time'] == current_time):
                    self.show_time_reminder(self.work_reminder['message'])
                
                # 检查睡觉提醒
                if (self.sleep_reminder['enabled'] and 
                    self.sleep_reminder['time'] == current_time):
                    self.show_time_reminder(self.sleep_reminder['message'])
            
            time.sleep(30)  # 每30秒检查一次

    def show_time_reminder(self, message):
        """显示时间提醒"""
        success = self.show_windows_notification("时间提醒", message, duration=10)
        if not success:
            self.show_custom_notification("时间提醒", message)

    def test_meal_notification(self):
        """测试三餐提醒"""
        test_msg = "🍛 这是一条测试的用餐提醒！记得按时吃饭哦！"
        self.show_time_reminder(test_msg)

    def test_work_notification(self):
        """测试下班提醒"""
        test_msg = "⏰ 这是一条测试的下班提醒！该休息了！"
        self.show_time_reminder(test_msg)

    def test_sleep_notification(self):
        """测试睡觉提醒"""
        test_msg = "😴 这是一条测试的睡觉提醒！早睡早起身体好！"
        self.show_time_reminder(test_msg)

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建一个简单的鱼形图标
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        # 画一个简单的鱼形
        draw.ellipse([10, 20, 45, 35], fill='#4CAF50')  # 鱼身
        draw.polygon([(45, 27), (55, 20), (55, 35)], fill='#4CAF50')  # 鱼尾
        draw.ellipse([35, 23, 40, 28], fill='white')  # 眼睛
        draw.ellipse([37, 25, 38, 26], fill='black')  # 眼珠
        
        # 创建托盘菜单
        menu = pystray.Menu(
            item('显示窗口', self.show_window, default=True),
            item('开始摸鱼提醒', self.start_reminder_from_tray),
            item('停止摸鱼提醒', self.stop_reminder_from_tray),
            pystray.Menu.SEPARATOR,
            item('测试摸鱼通知', self.test_notification),
            item('测试时间提醒', self.test_meal_notification),
            pystray.Menu.SEPARATOR,
            item('退出程序', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("摸鱼提醒器", image, "摸鱼提醒器", menu)

    def show_windows_notification(self, title, message, duration=5):
        """显示Windows原生通知"""
        try:
            # 方法1：使用PowerShell显示Windows 10/11原生通知
            if platform.system() == "Windows":
                # PowerShell脚本来显示气泡通知
                ps_script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                $notification = New-Object System.Windows.Forms.NotifyIcon
                $notification.Icon = [System.Drawing.SystemIcons]::Information
                $notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
                $notification.BalloonTipText = "{message}"
                $notification.BalloonTipTitle = "{title}"
                $notification.Visible = $true
                $notification.ShowBalloonTip({duration * 1000})
                Start-Sleep -Seconds {duration}
                $notification.Dispose()
                """
                
                # 异步执行PowerShell脚本
                threading.Thread(
                    target=lambda: subprocess.run([
                        "powershell", "-WindowStyle", "Hidden", "-Command", ps_script
                    ], capture_output=True, text=True),
                    daemon=True
                ).start()
                
                return True
        except Exception as e:
            print(f"Windows通知失败: {e}")
            
        # 备用方法：使用托盘通知
        try:
            if self.tray_icon and hasattr(self.tray_icon, 'notify'):
                self.tray_icon.notify(message, title)
                return True
        except Exception as e:
            print(f"托盘通知失败: {e}")
            
        return False

    def show_system_message(self, title, message):
        """显示系统级消息（备用方案）"""
        try:
            # 使用Windows msg命令（适用于企业环境）
            subprocess.run([
                "msg", "*", f"{title}\n\n{message}"
            ], capture_output=True, timeout=1)
            return True
        except:
            # 如果msg命令不可用，使用自定义弹窗
            return self.show_custom_notification(title, message)

    def show_custom_notification(self, title, message):
        """自定义非阻塞通知窗口"""
        def create_notification_window():
            # 创建通知窗口
            notify_window = tk.Toplevel()
            notify_window.title("摸鱼提醒")
            notify_window.geometry("300x150")
            notify_window.configure(bg="#2196F3")
            
            # 设置窗口属性
            notify_window.resizable(False, False)
            notify_window.attributes("-topmost", True)  # 置顶显示
            notify_window.attributes("-toolwindow", True)  # 不在任务栏显示
            
            # 居中显示
            screen_width = notify_window.winfo_screenwidth()
            screen_height = notify_window.winfo_screenheight()
            x = screen_width - 320  # 右侧显示
            y = screen_height - 200  # 底部显示
            notify_window.geometry(f"300x150+{x}+{y}")
            
            # 标题
            title_label = tk.Label(notify_window, text="🐟 " + title, 
                                 font=("微软雅黑", 12, "bold"),
                                 bg="#2196F3", fg="white")
            title_label.pack(pady=10)
            
            # 消息内容
            msg_label = tk.Label(notify_window, text=message,
                               font=("微软雅黑", 10),
                               bg="#2196F3", fg="white",
                               wraplength=250)
            msg_label.pack(pady=10)
            
            # 关闭按钮
            close_btn = tk.Button(notify_window, text="知道了", 
                                command=notify_window.destroy,
                                bg="white", fg="#2196F3",
                                font=("微软雅黑", 9))
            close_btn.pack(pady=10)
            
            # 自动关闭
            notify_window.after(5000, notify_window.destroy)
            
            # 显示窗口
            notify_window.focus_force()
            
        # 在主线程中创建通知窗口
        self.root.after(0, create_notification_window)
        return True

    def start_reminder(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.thread.start()
            self.status_label.config(text="状态：运行中", fg="green")
            
            # 使用Windows通知而不是弹窗
            self.show_windows_notification(
                "摸鱼提醒器", 
                f"摸鱼提醒已启动！每{self.interval_var.get()}分钟提醒一次"
            )

    def stop_reminder(self):
        self.running = False
        self.status_label.config(text="状态：已停止", fg="red")
        
        # 使用Windows通知
        self.show_windows_notification("摸鱼提醒器", "摸鱼提醒已停止！")

    def test_notification(self):
        """测试通知功能"""
        test_msg = random.choice(self.reminders)
        success = self.show_windows_notification("测试通知", test_msg)
        
        if not success:
            # 如果Windows通知失败，使用自定义通知
            self.show_custom_notification("测试通知", test_msg)

    def start_reminder_from_tray(self):
        """从托盘启动提醒"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.thread.start()
            if hasattr(self, 'status_label'):
                self.status_label.config(text="状态：运行中", fg="green")
            
            # 托盘通知
            self.show_windows_notification(
                "摸鱼提醒器", 
                f"后台提醒已启动！每{self.interval_var.get()}分钟提醒一次"
            )

    def stop_reminder_from_tray(self):
        """从托盘停止提醒"""
        self.running = False
        if hasattr(self, 'status_label'):
            self.status_label.config(text="状态：已停止", fg="red")
        
        self.show_windows_notification("摸鱼提醒器", "后台提醒已停止！")

    def reminder_loop(self):
        while self.running:
            time.sleep(self.interval_var.get() * 60)
            if self.running:
                self.show_reminder()

    def show_reminder(self):
        """显示提醒消息"""
        msg = random.choice(self.reminders)
        
        # 优先使用Windows原生通知
        success = self.show_windows_notification("🐟 摸鱼提醒", msg)
        
        # 如果Windows通知失败，使用自定义通知
        if not success:
            self.show_custom_notification("摸鱼提醒", msg)

    def hide_to_tray(self):
        """隐藏到系统托盘"""
        self.hidden_to_tray = True
        self.root.withdraw()  # 隐藏窗口
        
        # 启动托盘图标
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        """显示窗口"""
        self.hidden_to_tray = False
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 置于最前
        self.root.focus_force()  # 获取焦点
        
        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()

    def on_close(self):
        """窗口关闭事件"""
        if self.hidden_to_tray:
            # 如果已经隐藏到托盘，直接隐藏窗口
            self.root.withdraw()
            return
        
        # 使用Windows通知确认退出
        result = messagebox.askquestion("退出确认", 
                                      "确定要退出摸鱼提醒器吗？\n\n选择'Yes'完全退出\n选择'No'隐藏到托盘继续运行",
                                      icon='question')
        if result == 'yes':
            self.quit_app()
        else:
            self.hide_to_tray()

    def quit_app(self):
        """退出应用程序"""
        self.running = False
        self.time_reminder_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit()

def run():
    root = tk.Tk()
    app = FishReminderApp(root)
    root.mainloop()

if __name__ == "__main__":
    run()