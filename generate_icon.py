#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Mass Auto UI 应用程序图标
- 橘红色背景
- 白色文字，分两行显示：
  - 第一行：Auto
  - 第二行：PV Mass
"""

from PIL import Image, ImageDraw, ImageFont
import os

def generate_mass_auto_icon(output_path="resources/icon.ico", size=256):
    """
    生成 Mass Auto UI 图标

    Args:
        output_path: 输出文件路径
        size: 图标尺寸（默认256x256）
    """
    # 创建图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 橘红色背景 (#FF6B35 - 橘红色)
    bg_color = (255, 107, 53, 255)

    # 绘制圆角矩形背景
    margin = size // 16
    draw.rounded_rectangle(
        [(margin, margin), (size - margin, size - margin)],
        radius=size // 8,
        fill=bg_color
    )

    # 白色
    white = (255, 255, 255, 255)

    # === 绘制两行文字：第一行 "Auto"，第二行 "PV Mass" ===
    text_line1 = "Auto"
    text_line2 = "PV Mass"
    
    # 尝试使用系统字体，如果没有则使用默认字体
    try:
        # Windows 常用字体
        font_size = size // 7
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except:
            try:
                # 尝试使用微软雅黑
                font = ImageFont.truetype("msyh.ttc", font_size)
            except:
                # 如果没有找到字体，使用默认字体
                font = ImageFont.load_default()

    # 计算第一行文字位置
    bbox1 = draw.textbbox((0, 0), text_line1, font=font)
    text1_width = bbox1[2] - bbox1[0]
    text1_height = bbox1[3] - bbox1[1]
    
    # 计算第二行文字位置
    bbox2 = draw.textbbox((0, 0), text_line2, font=font)
    text2_width = bbox2[2] - bbox2[0]
    text2_height = bbox2[3] - bbox2[1]
    
    # 计算行间距
    line_spacing = size // 20
    
    # 计算总高度（两行文字 + 行间距）
    total_height = text1_height + text2_height + line_spacing
    
    # 计算起始 Y 位置（垂直居中）
    start_y = (size - total_height) // 2
    
    # 第一行文字位置（水平居中）
    text1_x = (size - text1_width) // 2
    text1_y = start_y
    
    # 第二行文字位置（水平居中）
    text2_x = (size - text2_width) // 2
    text2_y = start_y + text1_height + line_spacing

    # 绘制第一行文字
    draw.text((text1_x, text1_y), text_line1, fill=white, font=font)
    
    # 绘制第二行文字
    draw.text((text2_x, text2_y), text_line2, fill=white, font=font)

    # 保存为多尺寸 ICO 文件
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []

    for icon_size in icon_sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        images.append(resized)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存为 ICO 文件
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    # 同时保存一个 PNG 版本用于预览
    png_path = output_path.replace('.ico', '.png')
    img.save(png_path, 'PNG')

    print(f"[OK] Icon generated:")
    print(f"   - ICO file: {output_path}")
    print(f"   - PNG preview: {png_path}")
    print(f"   - Sizes: {icon_sizes}")

if __name__ == "__main__":
    # 生成图标到 resources 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "resources", "icon.ico")
    generate_mass_auto_icon(output_file, size=256)

