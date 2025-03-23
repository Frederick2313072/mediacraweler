# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  


# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 16:58
# @Desc    : 小红书存储实现类
import asyncio
import csv
import json
import os
import pathlib
from typing import Dict

import aiofiles

import config
from base.base_crawler import AbstractStore
from tools import utils, words
from var import crawler_type_var


def calculate_number_of_files(file_store_path: str) -> int:
    """计算数据保存文件的前部分排序数字，支持每次运行代码不写到同一个文件中
    Args:
        file_store_path;
    Returns:
        file nums
    """
    if not os.path.exists(file_store_path):
        return 1
    try:
        return max([int(file_name.split("_")[0])for file_name in os.listdir(file_store_path)])+1
    except ValueError:
        return 1


class XhsCsvStoreImplement(AbstractStore):
    csv_store_path: str = "data/xhs"
    file_count:int=calculate_number_of_files(csv_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        make save file name by store type
        Args:
            store_type: contents or comments

        Returns: eg: data/xhs/search_comments_20240114.csv ...

        """
        return f"{self.csv_store_path}/{self.file_count}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.csv"

    async def save_data_to_csv(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in CSV format.
        Args:
            save_item:  save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns: no returns

        """
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        async with aiofiles.open(save_file_name, mode='a+', encoding="utf-8-sig", newline="") as f:
            f.fileno()
            writer = csv.writer(f)
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            await writer.writerow(save_item.values())

    async def store_content(self, content_item: Dict):
        """
        Xiaohongshu content CSV storage implementation
        Args:
            content_item: note item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=content_item, store_type="contents")

    async def store_comment(self, comment_item: Dict):
        """
        Xiaohongshu comment CSV storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=comment_item, store_type="comments")

    async def store_creator(self, creator: Dict):
        """
        Xiaohongshu content CSV storage implementation
        Args:
            creator: creator dict

        Returns:

        """
        await self.save_data_to_csv(save_item=creator, store_type="creator")


class XhsDbStoreImplement(AbstractStore):
    async def store_content(self, content_item: Dict):
        """
        Xiaohongshu content DB storage implementation
        Args:
            content_item: content item dict

        Returns:

        """
        from .xhs_store_sql import (add_new_content,
                                    query_content_by_content_id,
                                    update_content_by_content_id)
        note_id = content_item.get("note_id")
        note_detail: Dict = await query_content_by_content_id(content_id=note_id)
        if not note_detail:
            content_item["add_ts"] = utils.get_current_timestamp()
            await add_new_content(content_item)
        else:
            await update_content_by_content_id(note_id, content_item=content_item)

    async def store_comment(self, comment_item: Dict):
        """
        Xiaohongshu content DB storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        from .xhs_store_sql import (add_new_comment,
                                    query_comment_by_comment_id,
                                    update_comment_by_comment_id)
        comment_id = comment_item.get("comment_id")
        comment_detail: Dict = await query_comment_by_comment_id(comment_id=comment_id)
        if not comment_detail:
            comment_item["add_ts"] = utils.get_current_timestamp()
            await add_new_comment(comment_item)
        else:
            await update_comment_by_comment_id(comment_id, comment_item=comment_item)

    async def store_creator(self, creator: Dict):
        """
        Xiaohongshu content DB storage implementation
        Args:
            creator: creator dict

        Returns:

        """
        from .xhs_store_sql import (add_new_creator, query_creator_by_user_id,
                                    update_creator_by_user_id)
        user_id = creator.get("user_id")
        user_detail: Dict = await query_creator_by_user_id(user_id)
        if not user_detail:
            creator["add_ts"] = utils.get_current_timestamp()
            await add_new_creator(creator)
        else:
            await update_creator_by_user_id(user_id, creator)


class XhsJsonStoreImplement(AbstractStore):
    json_store_path: str = "data/xhs/json"
    words_store_path: str = "data/xhs/words"
    lock = asyncio.Lock()
    file_count:int=calculate_number_of_files(json_store_path)
    WordCloud = words.AsyncWordCloudGenerator()

    def make_save_file_name(self, store_type: str) -> (str,str):
        """
        make save file name by store type
        Args:
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """

        return (
            f"{self.json_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.json",
            f"{self.words_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}"
        )

    async def save_data_to_json(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in json format.
        Args:
            save_item: save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.words_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name,words_file_name_prefix = self.make_save_file_name(store_type=store_type)
        save_data = []

        async with self.lock:
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, 'r', encoding='utf-8') as file:
                    save_data = json.loads(await file.read())

            save_data.append(save_item)
            async with aiofiles.open(save_file_name, 'w', encoding='utf-8') as file:
                await file.write(json.dumps(save_data, ensure_ascii=False, indent=4))

            if config.ENABLE_GET_COMMENTS and config.ENABLE_GET_WORDCLOUD:
                try:
                    await self.WordCloud.generate_word_frequency_and_cloud(save_data, words_file_name_prefix)
                except:
                    pass
    async def store_content(self, content_item: Dict):
        """
        content JSON storage implementation
        Args:
            content_item:

        Returns:

        """
        await self.save_data_to_json(content_item, "contents")

    async def store_comment(self, comment_item: Dict):
        """
        comment JSON storage implementatio
        Args:
            comment_item:

        Returns:

        """
        await self.save_data_to_json(comment_item, "comments")

    async def store_creator(self, creator: Dict):
        """
        Xiaohongshu content JSON storage implementation
        Args:
            creator: creator dict

        Returns:

        """
        await self.save_data_to_json(creator, "creator")
class XhsMarkdownStoreImplement(AbstractStore):
    markdown_store_path: str = "data/xhs/markdown"

    def make_save_file_name(self, note_id: str) -> str:
        """
        生成保存文件的路径
        Args:
            note_id: 笔记ID
        Returns:
            文件路径
        """
        return f"{self.markdown_store_path}/{note_id}.md"

    async def save_data_to_markdown(self, note_data: Dict):
        """
        将笔记数据保存为 Markdown 文件
        Args:
            note_data: 笔记数据，包含标题、内容、图片、视频等信息
        """
        # 确保保存目录存在
        pathlib.Path(self.markdown_store_path).mkdir(parents=True, exist_ok=True)

        # 提取笔记数据
        note_id = note_data.get("note_id", "unknown")
        title = note_data.get("title", "无标题")
        content = note_data.get("content", "无内容")
        images = note_data.get("image_list", [])
        videos = note_data.get("video_list", [])
        author = note_data.get("user", {}).get("nickname", "未知作者")
        publish_time = note_data.get("time", "未知时间")

        # 构建 Markdown 内容
        markdown_content = f"# {title}\n\n"
        markdown_content += f"**作者**: {author}  \n"
        markdown_content += f"**发布时间**: {publish_time}  \n\n"
        markdown_content += f"{content}\n\n"

        # 添加图片
        if images:
            markdown_content += "## 图片\n\n"
            for img in images:
                markdown_content += f"![图片]({img.get('url')})\n\n"

       

        # 保存 Markdown 文件
        save_file_name = self.make_save_file_name(note_id)
        async with aiofiles.open(save_file_name, "w", encoding="utf-8") as f:
            await f.write(markdown_content)
            utils.logger.info(f"[XhsMarkdownStoreImplement.save_data_to_markdown] 笔记已保存为 Markdown 文件: {save_file_name}")

    async def store_content(self, content_item: Dict):
        """
        将笔记内容保存为 Markdown 文件
        Args:
            content_item: 笔记数据
        """
        await self.save_data_to_markdown(content_item)

    async def store_comment(self, comment_item: Dict):
        """
        评论数据暂不保存为 Markdown 文件
        Args:
            comment_item: 评论数据
        """
        pass

    async def store_creator(self, creator: Dict):
        """
        创作者数据暂不保存为 Markdown 文件
        Args:
            creator: 创作者数据
        """
        pass