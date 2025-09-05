"""
AstrBot 个人记忆插件

一个轻量级的个人记忆管理插件，专为2核2G云服务器优化。
支持添加、查询、搜索个人记忆，具有内存优化和性能优化特性。
"""

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

@register(
    name="personal_memory",
    author="AstrBot团队",
    desc="个人记忆管理插件 - 轻量优化版",
    version="1.0.0",
    repo="https://github.com/AstrBotDevs/astrbot_plugin_personal_memory"
)
class PersonalMemoryPlugin(Star):
    """个人记忆插件主类"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.memories_file = os.path.join(self.data_dir, "memories.json")
        self.memories = {}
        self.last_save_time = 0
        self.save_interval = 5  # 5秒保存一次
        
        # 限制配置
        self.max_memory_per_user = 100
        self.max_key_length = 50
        self.max_content_length = 500
        self.max_file_size = 1024 * 1024  # 1MB
        
        # 初始化
        self._ensure_data_dir()
        self._load_memories()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_memories(self):
        """从文件加载记忆"""
        try:
            if os.path.exists(self.memories_file):
                # 检查文件大小
                if os.path.getsize(self.memories_file) > self.max_file_size:
                    logger.warning("记忆文件过大，跳过加载")
                    return
                
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 限制用户数
                    if len(data) > 100:
                        logger.warning("用户数据过多，限制加载")
                        data = dict(list(data.items())[:100])
                    
                    # 限制每个用户的记忆数
                    for user_id, user_memories in data.items():
                        if isinstance(user_memories, dict):
                            # 限制记忆数量
                            if len(user_memories) > self.max_memory_per_user:
                                sorted_memories = sorted(
                                    user_memories.items(),
                                    key=lambda x: x[1].get('created', '')
                                )
                                user_memories = dict(sorted_memories[-self.max_memory_per_user:])
                            
                            # 清理过长内容
                            cleaned_memories = {}
                            for key, memory in user_memories.items():
                                if isinstance(memory, dict):
                                    cleaned_memories[key] = {
                                        'content': str(memory.get('content', ''))[:self.max_content_length],
                                        'created': str(memory.get('created', datetime.now().isoformat()[:16]))
                                    }
                            self.memories[user_id] = cleaned_memories
                        else:
                            # 兼容旧格式
                            self.memories[user_id] = {}
                    
        except Exception as e:
            logger.error(f"加载记忆文件失败: {e}")
            self.memories = {}
    
    def _save_memories(self):
        """保存记忆到文件"""
        try:
            current_time = time.time()
            if current_time - self.last_save_time < self.save_interval:
                return
            
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, separators=(',', ':'), ensure_ascii=False)
            
            self.last_save_time = current_time
            
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
    
    def _add_memory(self, user_id: str, key: str, content: str) -> bool:
        """添加记忆"""
        try:
            # 长度限制
            key = str(key)[:self.max_key_length]
            content = str(content)[:self.max_content_length]
            
            if not key or not content:
                return False
            
            if user_id not in self.memories:
                self.memories[user_id] = {}
            
            # 检查并清理旧记忆
            if len(self.memories[user_id]) >= self.max_memory_per_user:
                oldest_key = min(self.memories[user_id].keys(), 
                               key=lambda k: self.memories[user_id][k].get('created', ''))
                del self.memories[user_id][oldest_key]
            
            self.memories[user_id][key] = {
                'content': content,
                'created': datetime.now().isoformat()[:16]
            }
            
            self._save_memories()
            return True
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return False
    
    def _get_memory(self, user_id: str, key: str) -> Optional[str]:
        """获取记忆"""
        try:
            if user_id in self.memories and key in self.memories[user_id]:
                return self.memories[user_id][key].get('content')
            return None
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None
    
    def _search_memories(self, user_id: str, keyword: str) -> List[tuple]:
        """搜索记忆"""
        try:
            if user_id not in self.memories:
                return []
            
            keyword = str(keyword).lower()
            results = []
            
            for key, memory in self.memories[user_id].items():
                content = memory.get('content', '').lower()
                if keyword in key.lower() or keyword in content:
                    results.append((key, memory.get('content', '')))
            
            return results
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def _get_user_memories(self, user_id: str) -> Dict[str, str]:
        """获取用户的所有记忆"""
        try:
            if user_id not in self.memories:
                return {}
            
            return {k: v.get('content', '') for k, v in self.memories[user_id].items()}
        except Exception as e:
            logger.error(f"获取用户记忆失败: {e}")
            return {}
    
    @filter.command("记住")
    async def add_memory_command(self, event: AstrMessageEvent):
        """添加记忆指令
        用法: /记住 关键词 内容
        示例: /记住 生日 2024年12月25日
        """
        try:
            message = event.message_str.strip()
            if not message.startswith("记住"):
                return
            
            content = message[2:].strip()
            if not content:
                yield event.plain_result("❌ 格式错误！用法: /记住 关键词 内容")
                return
            
            parts = content.split(None, 1)
            if len(parts) < 2:
                yield event.plain_result("❌ 格式错误！用法: /记住 关键词 内容")
                return
            
            key, value = parts[0], parts[1]
            user_id = event.get_sender_id()
            
            if self._add_memory(user_id, key, value):
                yield event.plain_result(f"✅ 已记住: {key}")
            else:
                yield event.plain_result("❌ 添加失败，请重试")
                
        except Exception as e:
            logger.error(f"添加记忆指令错误: {e}")
            yield event.plain_result("❌ 系统错误，请稍后重试")
    
    @filter.command("回忆")
    async def get_memory_command(self, event: AstrMessageEvent):
        """获取记忆指令
        用法: /回忆 关键词
        示例: /回忆 生日
        """
        try:
            message = event.message_str.strip()
            if not message.startswith("回忆"):
                return
            
            key = message[2:].strip()
            if not key:
                yield event.plain_result("❌ 格式错误！用法: /回忆 关键词")
                return
            
            user_id = event.get_sender_id()
            content = self._get_memory(user_id, key)
            
            if content:
                yield event.plain_result(f"📋 {key}: {content}")
            else:
                yield event.plain_result("❌ 没有找到相关记忆")
                
        except Exception as e:
            logger.error(f"获取记忆指令错误: {e}")
            yield event.plain_result("❌ 系统错误，请稍后重试")
    
    @filter.command("搜索记忆")
    async def search_memory_command(self, event: AstrMessageEvent):
        """搜索记忆指令
        用法: /搜索记忆 关键词
        示例: /搜索记忆 密码
        """
        try:
            message = event.message_str.strip()
            if not message.startswith("搜索记忆"):
                return
            
            keyword = message[4:].strip()
            if not keyword:
                yield event.plain_result("❌ 格式错误！用法: /搜索记忆 关键词")
                return
            
            user_id = event.get_sender_id()
            results = self._search_memories(user_id, keyword)
            
            if not results:
                yield event.plain_result("❌ 没有找到相关记忆")
                return
            
            response = f"🔍 找到 {len(results)} 条相关记忆:\n"
            for key, content in results[:10]:  # 最多显示10条
                response += f"- {key}: {content}\n"
            
            if len(results) > 10:
                response += f"... 还有 {len(results) - 10} 条"
            
            yield event.plain_result(response.strip())
            
        except Exception as e:
            logger.error(f"搜索记忆指令错误: {e}")
            yield event.plain_result("❌ 系统错误，请稍后重试")
    
    @filter.command("我的记忆")
    async def list_memories_command(self, event: AstrMessageEvent):
        """列出所有记忆指令
        用法: /我的记忆
        """
        try:
            user_id = event.get_sender_id()
            memories = self._get_user_memories(user_id)
            
            if not memories:
                yield event.plain_result("📭 你还没有任何记忆")
                return
            
            response = f"📚 你共有 {len(memories)} 条记忆:\n"
            for key, content in list(memories.items())[:10]:
                response += f"- {key}: {content}\n"
            
            if len(memories) > 10:
                response += f"... 还有 {len(memories) - 10} 条"
            
            yield event.plain_result(response.strip())
            
        except Exception as e:
            logger.error(f"列出记忆指令错误: {e}")
            yield event.plain_result("❌ 系统错误，请稍后重试")
    
    @filter.command("删除记忆")
    async def delete_memory_command(self, event: AstrMessageEvent):
        """删除记忆指令
        用法: /删除记忆 关键词
        示例: /删除记忆 生日
        """
        try:
            message = event.message_str.strip()
            if not message.startswith("删除记忆"):
                return
            
            key = message[4:].strip()
            if not key:
                yield event.plain_result("❌ 格式错误！用法: /删除记忆 关键词")
                return
            
            user_id = event.get_sender_id()
            
            if user_id in self.memories and key in self.memories[user_id]:
                del self.memories[user_id][key]
                self._save_memories()
                yield event.plain_result(f"✅ 已删除记忆: {key}")
            else:
                yield event.plain_result("❌ 没有找到相关记忆")
                
        except Exception as e:
            logger.error(f"删除记忆指令错误: {e}")
            yield event.plain_result("❌ 系统错误，请稍后重试")
    
    async def terminate(self):
        """插件卸载时保存数据"""
        self._save_memories()
        logger.info("个人记忆插件已卸载，数据已保存")
