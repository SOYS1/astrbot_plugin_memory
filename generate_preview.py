import io
import base64
from PIL import Image, ImageDraw, ImageFont

# 创建预览图
image = Image.new('RGB', (1200, 800), (240, 249, 255))
draw = ImageDraw.Draw(image)

try:
    # 尝试加载系统字体
    font_large = ImageFont.truetype("arial.ttf", 36)
    font_medium = ImageFont.truetype("arial.ttf", 24)
    font_small = ImageFont.truetype("arial.ttf", 18)
except:
    # 如果无法加载系统字体，使用默认字体
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()

# 绘制标题
bbox = draw.textbbox((0, 0), "AstrBot 个人记忆插件", font=font_large)
width = bbox[2] - bbox[0]
draw.text(((1200-width)/2, 50), "AstrBot 个人记忆插件", font=font_large, fill=(14, 165, 233))

# 绘制副标题
bbox = draw.textbbox((0, 0), "精美图片回复版", font=font_medium)
width = bbox[2] - bbox[0]
draw.text(((1200-width)/2, 100), "精美图片回复版", font=font_medium, fill=(100, 116, 139))

# 绘制功能亮点
features = [
    "个人专属记忆空间",
    "精美图片回复",
    "群聊记忆隔离",
    "智能标签系统",
    "使用频率统计",
    "数据持久化"
]

draw.text((100, 180), "功能亮点", font=font_medium, fill=(30, 41, 59))
for i, feature in enumerate(features):
    draw.text((120, 220 + i*40), f"• {feature}", font=font_small, fill=(71, 85, 105))

# 绘制命令示例
commands = [
    "记住 生日 1990年1月1日 #重要",
    "回忆 生日",
    "搜索记忆 生日",
    "我的记忆",
    "删除记忆 生日"
]

draw.text((600, 180), "命令示例", font=font_medium, fill=(30, 41, 59))
for i, cmd in enumerate(commands):
    draw.text((620, 220 + i*40), f"/{cmd}", font=font_small, fill=(71, 85, 105))

# 绘制图片效果展示区域
# 记忆卡片示例
draw.rectangle([100, 500, 500, 700], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
# 卡片标题
draw.rectangle([100, 500, 500, 540], fill=(14, 165, 233))
draw.text((120, 510), "记忆卡片", font=font_small, fill=(255, 255, 255))
# 卡片内容
draw.text((120, 560), "关键词: 生日", font=font_small, fill=(30, 41, 59))
draw.text((120, 590), "内容: 1990年1月1日", font=font_small, fill=(30, 41, 59))
draw.text((120, 620), "标签: #重要", font=font_small, fill=(30, 41, 59))
draw.text((120, 650), "使用次数: 5", font=font_small, fill=(30, 41, 59))

# 列表展示示例
draw.rectangle([600, 500, 1100, 700], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
# 列表标题
draw.rectangle([600, 500, 1100, 540], fill=(14, 165, 233))
draw.text((620, 510), "记忆列表", font=font_small, fill=(255, 255, 255))
# 列表内容
draw.text((620, 560), "1. 生日 - 使用5次", font=font_small, fill=(30, 41, 59))
draw.text((620, 590), "2. 工作邮箱 - 使用2次", font=font_small, fill=(30, 41, 59))
draw.text((620, 620), "3. 家庭地址 - 使用1次", font=font_small, fill=(30, 41, 59))

# 保存图片
image.save("preview.png")
print("预览图已生成: preview.png")