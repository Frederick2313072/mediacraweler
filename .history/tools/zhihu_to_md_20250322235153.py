import os
import json
import time
from datetime import datetime

def convert_zhihu_to_md():
    try:
        # 获取数据目录
        data_dir = os.path.join('data', 'zhihu')
        json_dir = os.path.join(data_dir, 'json')
        output_dir = os.path.join('docs', 'zhihu')
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
                            question_id = comment.get('question_id')
                            if question_id:
                                if question_id not in comments_data:
                                    comments_data[question_id] = []
                                comments_data[question_id].append(comment)
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
            f.write('# 知乎数据\n\n')
            f.write(f'更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write('## 内容列表\n\n')
            
            # 处理每个内容
            for i, content in enumerate(contents_data, 1):
                try:
                    print(f"正在处理第 {i}/{len(contents_data)} 条内容")
                    # 创建内容文件
                    question_id = content.get('question_id')
                    if not question_id:
                        print(f"跳过没有question_id的内容: {content}")
                        continue
                        
                    content_file = os.path.join(output_dir, f'content_{question_id}.md')
                    
                    with open(content_file, 'w', encoding='utf-8') as cf:
                        # 写入内容标题
                        cf.write(f'# {content.get("title", "无标题")}\n\n')
                        
                        # 写入内容信息
                        cf.write('## 基本信息\n\n')
                        author = content.get('author', {})
                        cf.write(f'- 作者：{author.get("name", "匿名用户")}\n')
                        cf.write(f'- 发布时间：{datetime.fromtimestamp(content.get("created_time", 0)).strftime("%Y-%m-%d %H:%M:%S")}\n')
                        cf.write(f'- 点赞数：{content.get("voteup_count", 0)}\n')
                        cf.write(f'- 收藏数：{content.get("favorite_count", 0)}\n')
                        cf.write(f'- 评论数：{content.get("comment_count", 0)}\n')
                        cf.write(f'- 分享数：{content.get("share_count", 0)}\n')
                        if content.get('location'):
                            cf.write(f'- 发布地点：{content["location"]}\n')
                        cf.write('\n')
                        
                        # 写入内容正文
                        cf.write('## 正文\n\n')
                        cf.write(f'{content.get("content", "无内容")}\n\n')
                        
                        # 下载并写入图片
                        if content.get('images'):
                            cf.write('## 图片\n\n')
                            image_urls = content['images']
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
                        if question_id in comments_data:
                            cf.write('## 评论\n\n')
                            comments = comments_data[question_id]
                            print(f"正在处理 {len(comments)} 条评论")
                            for comment in comments:
                                comment_author = comment.get('author', {})
                                cf.write(f'### {comment_author.get("name", "匿名用户")} ({datetime.fromtimestamp(comment.get("created_time", 0)).strftime("%Y-%m-%d %H:%M:%S")})\n\n')
                                cf.write(f'{comment.get("content", "")}\n\n')
                                if comment.get('vote_count'):
                                    cf.write(f'- 点赞数：{comment["vote_count"]}\n\n')
                    
                    # 在索引文件中添加链接
                    f.write(f'- [{content.get("title", "无标题")}](content_{question_id}.md)\n')
                    
                except Exception as e:
                    print(f"处理内容时出错: {str(e)}")
                    continue
        
        print("转换完成！")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        raise 