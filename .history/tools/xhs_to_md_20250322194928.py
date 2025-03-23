import pandas as pd
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
    # 获取数据目录
    data_dir = os.path.join('data', 'xhs')
    output_dir = os.path.join('docs', 'xhs')
    images_dir = os.path.join(output_dir, 'images')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # 读取内容数据
    contents_file = [f for f in os.listdir(data_dir) if 'search_contents' in f][0]
    contents_df = pd.read_csv(os.path.join(data_dir, contents_file))
    
    # 读取评论数据
    comments_file = [f for f in os.listdir(data_dir) if 'search_comments' in f][0]
    comments_df = pd.read_csv(os.path.join(data_dir, comments_file))
    
    # 创建索引文件
    with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write('# 小红书数据\n\n')
        f.write(f'更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        f.write('## 内容列表\n\n')
        
        # 遍历每个内容
        for _, content in contents_df.iterrows():
            # 创建内容文件
            content_id = content['id']
            content_file = os.path.join(output_dir, f'content_{content_id}.md')
            
            # 获取该内容的评论
            content_comments = comments_df[comments_df['content_id'] == content_id]
            
            # 准备JSON数据
            json_data = {
                'id': content_id,
                'title': content['title'],
                'author': content['author'],
                'publish_time': content['publish_time'],
                'likes': content['likes'],
                'favorites': content['favorites'],
                'comments': content['comments'],
                'content': content['content'],
                'images': content['images'].split(',') if pd.notna(content['images']) else [],
                'comments_data': content_comments.to_dict('records') if not content_comments.empty else []
            }
            
            # 保存JSON数据
            json_file = os.path.join(output_dir, f'content_{content_id}.json')
            with open(json_file, 'w', encoding='utf-8') as jf:
                json.dump(json_data, jf, ensure_ascii=False, indent=2)
            
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
                cf.write(f'- [原始JSON数据](content_{content_id}.json)\n\n')
                
                # 写入内容正文
                cf.write('## 正文\n\n')
                cf.write(f'{content["content"]}\n\n')
                
                # 下载并写入图片
                if 'images' in content and pd.notna(content['images']):
                    cf.write('## 图片\n\n')
                    for img_url in content['images'].split(','):
                        img_url = img_url.strip()
                        if img_url:
                            local_path = download_image(img_url, images_dir)
                            if local_path:
                                relative_path = os.path.relpath(local_path, output_dir)
                                cf.write(f'![图片]({relative_path})\n\n')
                
                # 写入评论
                if not content_comments.empty:
                    cf.write('## 评论\n\n')
                    for _, comment in content_comments.iterrows():
                        cf.write(f'### {comment["user_name"]} ({comment["publish_time"]})\n\n')
                        cf.write(f'{comment["content"]}\n\n')
                        cf.write(f'- 点赞数：{comment["likes"]}\n\n')
            
            # 在索引文件中添加链接
            f.write(f'- [{content["title"]}](content_{content_id}.md)\n')

if __name__ == '__main__':
    convert_xhs_to_md() 