import os
from PIL import Image, ImageDraw
def save_image(img, filename):
    img.save(filename, format="PNG")

save_dir = "image"  # 指定保存目录
# 检查目录是否存在
if not os.path.exists(save_dir):
    print(f"Directory '{save_dir}' does not exist. Creating it.")
    exit(1)

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


# save_image(img, os.path.join(save_dir, f"defaultPet_{emotion}.png"))
save_image(tray_image, os.path.join(save_dir, f"tray_ico.png"))


emotions = ['normal', 'happy', 'sleepy', 'excited', 'thinking', 'curious']
img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

for emotion in emotions:
        
    if emotion == 'normal':
        draw.ellipse([10, 20, 70, 70], fill='#4CAF50', outline='#2E7D32', width=2)
        # 眼睛
            # 画闭眼（横线）
        draw.line([25, 35, 35, 35], fill='black', width=3)
        draw.line([45, 35, 55, 35], fill='black', width=3)
        draw.arc([35, 45, 45, 55], 0, 180, fill='black', width=2)

    elif emotion == 'happy':
        draw.ellipse([10, 20, 70, 70], fill='#FFC107', outline='#FF8F00', width=2)

        draw.line([25, 35, 35, 35], fill='black', width=3)
        draw.line([45, 35, 55, 35], fill='black', width=3)
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

    elif emotion == 'excited':
        draw.ellipse([10, 20, 70, 70], fill='#F44336', outline='#B71C1C', width=2)
        draw.line([20, 32, 35, 32], fill='black', width=3)
        draw.line([45, 32, 60, 32], fill='black', width=3)
        draw.ellipse([35, 45, 45, 55], fill='black')
        draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
        draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

    elif emotion == 'thinking':
        draw.ellipse([10, 20, 70, 70], fill='#9C27B0', outline='#4A148C', width=2)
        draw.line([25, 32, 35, 32], fill='black', width=3)
        draw.line([45, 32, 55, 32], fill='black', width=3)
        draw.arc([35, 50, 45, 55], 0, 180, fill='black', width=2)
        draw.ellipse([55, 10, 65, 20], fill='white', outline='black')
        draw.text((57, 12), "?", fill='black')

    elif emotion == 'curious':
        draw.ellipse([10, 20, 70, 70], fill='#FF9800', outline='#E65100', width=2)
        draw.line([22, 35, 36, 35], fill='black', width=3)
        draw.line([44, 35, 54, 35], fill='black', width=3)
        draw.ellipse([37, 47, 43, 53], fill='black')
        draw.text((60, 15), "!", fill='black')
        draw.ellipse([15, 45, 25, 55], fill='#FF9999', outline=None)
        draw.ellipse([55, 45, 65, 55], fill='#FF9999', outline=None)

    # 保存每个表情的图像
    save_image(img, os.path.join(save_dir, f"blink_{emotion}.png"))


