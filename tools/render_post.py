# tools/render_util.py
import os
from typing import Dict

async def render_note_to_html(note_data: Dict, output_dir: str = "data/html") -> str:
    """
    将小红书笔记数据渲染为 HTML 文件
    Args:
        note_data: 笔记数据，包含标题、内容、图片、视频等信息
        output_dir: HTML 文件的输出目录，默认为 "data/html"
    Returns:
        HTML 文件的路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 提取笔记数据
    note_id = note_data.get("note_id", "unknown")
    title = note_data.get("title", "无标题")
    content = note_data.get("content", "无内容")
    images = note_data.get("image_list", [])
    videos = note_data.get("video_list", [])
    author = note_data.get("user", {}).get("nickname", "未知作者")
    publish_time = note_data.get("time", "未知时间")

    # 构建 HTML 内容
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .note {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}
            .title {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
            .author {{ color: #666; margin-bottom: 10px; }}
            .content {{ margin-bottom: 20px; }}
            .images img {{ max-width: 100%; height: auto; margin-bottom: 10px; }}
            .videos video {{ max-width: 100%; height: auto; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="note">
            <div class="title">{title}</div>
            <div class="author">作者: {author} | 发布时间: {publish_time}</div>
            <div class="content">{content}</div>
            <div class="images">
                {"".join([f'<img src="{img.get("url")}" />' for img in images])}
            </div>
            <div class="videos">
                {"".join([f'<video src="{video.get("url")}" controls></video>' for video in videos])}
            </div>
        </div>
    </body>
    </html>
    """

    # 保存 HTML 文件
    html_file_path = os.path.join(output_dir, f"{note_id}.html")
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_file_path