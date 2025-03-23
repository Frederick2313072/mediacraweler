import os
import json
import requests
from datetime import datetime
from urllib.parse import urlparse
import hashlib

def download_image(url, save_dir):
    """下载图片并返回本地路径"""
    try:
        # 创建文件名（使用URL的MD5值）
        file_ext = os.path.splitext(urlparse(url).path)[1] or '.jpg'
        file_name = hashlib.md5(url.encode()).hexdigest() + file_ext
        file_path = os.path.join(save_dir, file_name)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(file_path):
            return file_path
            
        # 下载图片
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 保存图片
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return file_path
    except Exception as e:
        print(f"下载图片失败: {url}, 错误: {str(e)}")
        return None

def convert_xhs_to_md():
    try:
        # 获取数据目录
        data_dir = os.path.join('data', 'xhs')
        json_dir = os.path.join(data_dir, 'json')
        output_dir = os.path.join('docs', 'xhs')
        images_dir = os.path.join(output_dir, 'images')
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        
        # 检查JSON目录是否存在
        if not os.path.exists(json_dir):
            print(f"错误: JSON目录不存在: {json_dir}")
            return
        
        # 获取所有JSON文件
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        if not json_files:
            print("错误: 未找到JSON数据文件")
            return
            
        print(f"找到以下JSON文件: {json_files}")
        
        # 创建索引文件
        with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
            f.write('# 小红书数据\n\n')
            f.write(f'更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write('## 内容列表\n\n')
            
            # 处理每个JSON文件
            for json_file in json_files:
                try:
                    # 读取JSON数据
                    with open(os.path.join(json_dir, json_file), 'r', encoding='utf-8') as jf:
                        content = json.load(jf)
                    
                    # 创建内容文件
                    content_id = content['id']
                    content_file = os.path.join(output_dir, f'content_{content_id}.md')
                    
                    with open(content_file, 'w', encoding='utf-8') as cf:
                        # 写入内容标题
                        cf.write(f'# {content["title"]}\n\n')
                        
                        # 写入内容信息
                        cf.write('## 基本信息\n\n')
                        cf.write(f'- 作者：{content["author"]}\n')
                        cf.write(f'- 发布时间：{content["publish_time"]}\n')
                        cf.write(f'- 点赞数：{content["likes"]}\n')
                        cf.write(f'- 收藏数：{content["favorites"]}\n')
                        cf.write(f'- 评论数：{content["comments"]}\n')
                        cf.write(f'- [原始JSON数据](json/{json_file})\n\n')
                        
                        # 写入内容正文
                        cf.write('## 正文\n\n')
                        cf.write(f'{content["content"]}\n\n')
                        
                        # 下载并写入图片
                        if 'images' in content and content['images']:
                            cf.write('## 图片\n\n')
                            for img_url in content['images']:
                                img_url = img_url.strip()
                                if img_url:
                                    local_path = download_image(img_url, images_dir)
                                    if local_path:
                                        relative_path = os.path.relpath(local_path, output_dir)
                                        cf.write(f'![图片]({relative_path})\n\n')
                        
                        # 写入评论
                        if 'comments_data' in content and content['comments_data']:
                            cf.write('## 评论\n\n')
                            for comment in content['comments_data']:
                                cf.write(f'### {comment["user_name"]} ({comment["publish_time"]})\n\n')
                                cf.write(f'{comment["content"]}\n\n')
                                cf.write(f'- 点赞数：{comment["likes"]}\n\n')
                    
                    # 在索引文件中添加链接
                    f.write(f'- [{content["title"]}](content_{content_id}.md)\n')
                    
                except Exception as e:
                    print(f"处理文件 {json_file} 时出错: {str(e)}")
                    continue
        
        print("转换完成！")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        raise

if __name__ == '__main__':
    convert_xhs_to_md() 