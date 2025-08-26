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

