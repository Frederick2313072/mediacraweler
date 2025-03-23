import os
import json
import requests
from datetime import datetime
from urllib.parse import urlparse
import hashlib
import time

def download_image(url, save_dir):
    """下载图片并返回本地路径"""
    try:
        # 创建文件名（使用URL的MD5值）
        file_ext = os.path.splitext(urlparse(url).path)[1] or '.jpg'
        file_name = hashlib.md5(url.encode()).hexdigest() + file_ext
        file_path = os.path.join(save_dir, file_name)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(file_path):
            print(f"图片已存在: {file_name}")
            return file_path
            
        print(f"开始下载图片: {url}")
        # 下载图片，设置超时时间为10秒
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        # 保存图片
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        print(f"\r下载进度: {progress:.1f}%", end='')
        
        print(f"\n图片下载完成: {file_name}")
        return file_path
    except requests.Timeout:
        print(f"下载超时: {url}")
        return None
    except requests.RequestException as e:
        print(f"下载失败: {url}, 错误: {str(e)}")
        return None
    except Exception as e:
        print(f"处理图片时出错: {url}, 错误: {str(e)}")
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
        
        # 读取内容和评论数据
        contents_data = []
        comments_data = {}
        
        for json_file in json_files:
            try:
                print(f"正在读取文件: {json_file}")
                start_time = time.time()
                
                with open(os.path.join(json_dir, json_file), 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    print(f"文件 {json_file} 读取完成，耗时: {time.time() - start_time:.2f}秒")
                    print(f"数据长度: {len(data)}")
                    
                    if 'search_contents' in json_file:
                        contents_data = data
                        print(f"内容数据读取完成，共 {len(contents_data)} 条")
                    elif 'search_comments' in json_file:
                        # 将评论按内容ID分组
                        comment_count = 0
                        for comment in data:
                            note_id = comment.get('note_id')
                            if note_id:
                                if note_id not in comments_data:
                                    comments_data[note_id] = []
                                comments_data[note_id].append(comment)
                                comment_count += 1
                        print(f"评论数据读取完成，共 {comment_count} 条")
                        
            except Exception as e:
                print(f"读取文件 {json_file} 时出错: {str(e)}")
                continue
        
        if not contents_data:
            print("错误: 未读取到内容数据")
            return
            
        print(f"开始处理 {len(contents_data)} 条内容...")
        
        # 创建索引文件
        with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
            f.write('# 小红书数据\n\n')
            f.write(f'更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write('## 内容列表\n\n')
            
            # 处理每个内容
            for i, content in enumerate(contents_data, 1):
                try:
                    print(f"正在处理第 {i}/{len(contents_data)} 条内容")
                    # 创建内容文件
                    note_id = content['note_id']
                    content_file = os.path.join(output_dir, f'content_{note_id}.md')
                    
                    with open(content_file, 'w', encoding='utf-8') as cf:
                        # 写入内容标题
                        cf.write(f'# {content["title"]}\n\n')
                        
                        # 写入内容信息
                        cf.write('## 基本信息\n\n')
                        cf.write(f'- 作者：{content["nickname"]}\n')
                        cf.write(f'- 发布时间：{datetime.fromtimestamp(content["time"]/1000).strftime("%Y-%m-%d %H:%M:%S")}\n')
                        cf.write(f'- 点赞数：{content["liked_count"]}\n')
                        cf.write(f'- 收藏数：{content["collected_count"]}\n')
                        cf.write(f'- 评论数：{content["comment_count"]}\n')
                        cf.write(f'- 分享数：{content["share_count"]}\n')
                        if content.get('ip_location'):
                            cf.write(f'- 发布地点：{content["ip_location"]}\n')
                        cf.write('\n')
                        
                        # 写入内容正文
                        cf.write('## 正文\n\n')
                        cf.write(f'{content["desc"]}\n\n')
                        
                        # 下载并写入图片
                        if content.get('image_list'):
                            cf.write('## 图片\n\n')
                            image_urls = content['image_list'].split(',')
                            print(f"正在处理 {len(image_urls)} 张图片")
                            for idx, img_url in enumerate(image_urls, 1):
                                img_url = img_url.strip()
                                if img_url:
                                    print(f"\n处理第 {idx}/{len(image_urls)} 张图片")
                                    local_path = download_image(img_url, images_dir)
                                    if local_path:
                                        relative_path = os.path.relpath(local_path, output_dir)
                                        cf.write(f'![图片]({relative_path})\n\n')
                                    else:
                                        print(f"跳过失败的图片: {img_url}")
                                        cf.write(f'![图片下载失败]({img_url})\n\n')
                        
                        # 写入评论
                        if note_id in comments_data:
                            cf.write('## 评论\n\n')
                            comments = comments_data[note_id]
                            print(f"正在处理 {len(comments)} 条评论")
                            for comment in comments:
                                cf.write(f'### {comment.get("nickname", "匿名用户")} ({datetime.fromtimestamp(comment.get("time", 0)/1000).strftime("%Y-%m-%d %H:%M:%S")})\n\n')
                                cf.write(f'{comment.get("content", "")}\n\n')
                                if comment.get('liked_count'):
                                    cf.write(f'- 点赞数：{comment["liked_count"]}\n\n')
                    
                    # 在索引文件中添加链接
                    f.write(f'- [{content["title"]}](content_{note_id}.md)\n')
                    
                except Exception as e:
                    print(f"处理内容 {note_id} 时出错: {str(e)}")
                    continue
        
        print("转换完成！")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        raise

if __name__ == '__main__':
    convert_xhs_to_md()