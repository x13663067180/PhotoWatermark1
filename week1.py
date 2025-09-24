import os
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
import argparse

def get_exif_datetime(image_path):
    """从图片EXIF中提取拍摄时间"""
    try:
        exif_dict = piexif.load(image_path)
        if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
            date_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            # 格式: "YYYY:MM:DD HH:MM:SS"
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y年%m月%d日")
    except Exception as e:
        print(f"无法读取 {image_path} 的EXIF信息: {e}")
    return None

def add_watermark(image_path, watermark_text, font_size=30, color=(255, 255, 255), position="右下角"):
    """给图片添加水印"""
    try:
        # 打开图片
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # 尝试加载系统字体，如果失败则使用默认字体
        try:
            # 在不同系统上尝试不同的字体路径
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "C:/Windows/Fonts/simhei.ttf",         # Windows
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
                "arial.ttf"  # 默认字体
            ]
            
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
                # PIL默认字体不支持指定大小，所以这里做个简单处理
                font_size = 16  # 默认字体大小有限
        except:
            font = ImageFont.load_default()
            font_size = 16
        
        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 根据位置计算坐标
        img_width, img_height = img.size
        padding = 20
        
        if position == "左上角":
            x = padding
            y = padding
        elif position == "居中":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        elif position == "右下角":
            x = img_width - text_width - padding
            y = img_height - text_height - padding
        else:  # 默认右下角
            x = img_width - text_width - padding
            y = img_height - text_height - padding
        
        # 绘制水印（添加阴影效果增强可读性）
        shadow_color = (0, 0, 0, 128)
        draw.text((x+2, y+2), watermark_text, font=font, fill=shadow_color)
        draw.text((x, y), watermark_text, font=font, fill=color)
        
        return img
    except Exception as e:
        print(f"添加水印失败: {e}")
        return None

def process_images_in_directory(directory_path, font_size=30, color=(255, 255, 255), position="右下角"):
    """处理目录中的所有图片"""
    # 创建输出目录
    output_dir = os.path.join(directory_path, os.path.basename(directory_path) + "_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    
    # 遍历目录中的所有文件
    processed_count = 0
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(supported_formats):
            file_path = os.path.join(directory_path, filename)
            
            # 获取拍摄日期
            shoot_date = get_exif_datetime(file_path)
            if not shoot_date:
                print(f"跳过 {filename}: 未找到拍摄日期")
                continue
            
            # 添加水印
            watermarked_img = add_watermark(file_path, shoot_date, font_size, color, position)
            if watermarked_img:
                # 保存新图片
                output_path = os.path.join(output_dir, filename)
                watermarked_img.save(output_path, quality=95)
                print(f"已处理: {filename} -> {output_path}")
                processed_count += 1
            else:
                print(f"处理失败: {filename}")
    
    print(f"总共处理了 {processed_count} 张图片，结果保存在: {output_dir}")

def parse_color(color_str):
    """解析颜色字符串，支持 'r,g,b' 格式"""
    try:
        parts = color_str.split(',')
        if len(parts) != 3:
            raise ValueError("颜色格式应为 'r,g,b'")
        r, g, b = [int(x.strip()) for x in parts]
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("颜色值应在0-255之间")
        return (r, g, b)
    except Exception as e:
        print(f"颜色格式错误: {e}，使用默认白色")
        return (255, 255, 255)

def main():
    parser = argparse.ArgumentParser(description="为图片添加拍摄日期水印")
    parser.add_argument("--directory", help="图片文件夹路径", default="D:/研究生文件汇总/研一上/大语言模型辅助软件工程/第一次作业/photos")
    parser.add_argument("--font_size", type=int, default=100, help="字体大小 (默认: 100)")
    parser.add_argument("--color", type=str, default="255,255,255", 
                       help="水印颜色，格式: r,g,b (默认: 255,255,255 白色)")
    parser.add_argument("--position", choices=["左上角", "居中", "右下角"], 
                       default="居中", help="水印位置 (默认: 右下角)")
    
    args = parser.parse_args()
    
    # 解析颜色
    color = parse_color(args.color)
    
    # 处理图片
    if not os.path.exists(args.directory):
        print(f"错误: 目录 {args.directory} 不存在")
        return
    
    print(f"开始处理目录: {args.directory}")
    print(f"字体大小: {args.font_size}")
    print(f"颜色: {color}")
    print(f"位置: {args.position}")
    
    process_images_in_directory(args.directory, args.font_size, color, args.position)

if __name__ == "__main__":
    main()