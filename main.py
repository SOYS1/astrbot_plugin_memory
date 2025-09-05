"""
AstrBot 个人记忆插件（精美图片回复版）

支持精美图片回复的个人记忆管理插件
"""

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import io
import base64

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    logger.warning("Pillow未安装，将使用文本回复")

@register(
    name="personal_memory",
    author="AstrBot团队",
    desc="个人记忆管理插件（精美图片回复版）",
    version="2.0.0",
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
        self.save_interval = 5
        
        # 限制配置
        self.max_memory_per_user = 100
        self.max_key_length = 50
        self.max_content_length = 500
        self.max_file_size = 1024 * 1024
        
        # 图片配置
        self.card_width = 800
        self.card_height = 400
        self.bg_color = (248, 250, 252)
        self.primary_color = (59, 130, 246)
        self.text_color = (30, 41, 59)
        self.muted_color = (100, 116, 139)
        
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
                if os.path.getsize(self.memories_file) > self.max_file_size:
                    logger.warning("记忆文件过大，跳过加载")
                    return
                
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if len(data) > 100:
                        data = dict(list(data.items())[:100])
                    
                    for user_id, user_memories in data.items():
                        if isinstance(user_memories, dict):
                            if len(user_memories) > self.max_memory_per_user:
                                sorted_memories = sorted(
                                    user_memories.items(),
                                    key=lambda x: x[1].get('created', '')
                                )
                                user_memories = dict(sorted_memories[-self.max_memory_per_user:])
                            
                            cleaned_memories = {}
                            for key, memory in user_memories.items():
                                if isinstance(memory, dict):
                                    cleaned_memories[key] = {
                                        'content': str(memory.get('content', ''))[:self.max_content_length],
                                        'tags': memory.get('tags', []),
                                        'created': str(memory.get('created', datetime.now().isoformat()[:16])),
                                        'usage_count': memory.get('usage_count', 0)
                                    }
                            self.memories[user_id] = cleaned_memories
                        else:
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
    
    def _add_memory(self, user_id: str, key: str, content: str, tags: List[str] = None) -> bool:
        """添加记忆"""
        try:
            key = str(key)[:self.max_key_length]
            content = str(content)[:self.max_content_length]
            
            if not key or not content:
                return False
            
            if user_id not in self.memories:
                self.memories[user_id] = {}
            
            if len(self.memories[user_id]) >= self.max_memory_per_user:
                oldest_key = min(self.memories[user_id].keys(), 
                               key=lambda k: self.memories[user_id][k].get('created', ''))
                del self.memories[user_id][oldest_key]
            
            self.memories[user_id][key] = {
                'content': content,
                'tags': tags or [],
                'created': datetime.now().isoformat()[:16],
                'usage_count': 0
            }
            
            self._save_memories()
            return True
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return False
    
    def _get_memory(self, user_id: str, key: str) -> Optional[Dict]:
        """获取记忆"""
        try:
            if user_id in self.memories and key in self.memories[user_id]:
                memory = self.memories[user_id][key]
                memory['usage_count'] = memory.get('usage_count', 0) + 1
                self._save_memories()
                return memory
            return None
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None
    
    def _search_memories(self, user_id: str, keyword: str) -> List[Tuple[str, Dict]]:
        """搜索记忆"""
        try:
            if user_id not in self.memories:
                return []
            
            keyword = str(keyword).lower()
            results = []
            
            for key, memory in self.memories[user_id].items():
                content = memory.get('content', '').lower()
                tags = ' '.join(memory.get('tags', [])).lower()
                if keyword in key.lower() or keyword in content or keyword in tags:
                    results.append((key, memory))
            
            return results
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def _get_user_memories(self, user_id: str) -> List[Tuple[str, Dict]]:
        """获取用户的所有记忆"""
        try:
            if user_id not in self.memories:
                return []
            
            return list(self.memories[user_id].items())
        except Exception as e:
            logger.error(f"获取用户记忆失败: {e}")
            return []
    
    def _delete_memory(self, user_id: str, key: str) -> bool:
        """删除记忆"""
        try:
            if user_id in self.memories and key in self.memories[user_id]:
                del self.memories[user_id][key]
                self._save_memories()
                return True
            return False
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False
    
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
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "格式错误！用法: /记住 关键词 内容", action="添加失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 格式错误！用法: /记住 关键词 内容")
                return
            
            parts = content.split(None, 1)
            if len(parts) < 2:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "格式错误！用法: /记住 关键词 内容", action="添加失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 格式错误！用法: /记住 关键词 内容")
                return
            
            key, value = parts[0], parts[1]
            user_id = event.get_sender_id()
            user_name = event.get_sender_name() or "用户"
            
            if self._add_memory(user_id, key, value):
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card(key, value, action="记住", user_name=user_name)
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result(f"✅ 已记住: {key}")
            else:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "添加失败，请重试", action="添加失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 添加失败，请重试")
                    
        except Exception as e:
            logger.error(f"添加记忆指令错误: {e}")
            if HAS_PILLOW:
                img_base64 = self._create_memory_card("错误", "系统错误，请稍后重试", action="添加失败")
                yield event.image_result(img_base64)
            else:
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
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "格式错误！用法: /回忆 关键词", action="回忆失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 格式错误！用法: /回忆 关键词")
                return
            
            user_id = event.get_sender_id()
            user_name = event.get_sender_name() or "用户"
            memory = self._get_memory(user_id, key)
            
            if memory:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card(key, memory['content'], action="回忆", user_name=user_name)
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result(f"📋 {key}: {memory['content']}")
            else:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("未找到", f"没有找到关于 '{key}' 的记忆", action="回忆失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 没有找到相关记忆")
                    
        except Exception as e:
            logger.error(f"获取记忆指令错误: {e}")
            if HAS_PILLOW:
                img_base64 = self._create_memory_card("错误", "系统错误，请稍后重试", action="回忆失败")
                yield event.image_result(img_base64)
            else:
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
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "格式错误！用法: /搜索记忆 关键词", action="搜索失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 格式错误！用法: /搜索记忆 关键词")
                return
            
            user_id = event.get_sender_id()
            user_name = event.get_sender_name() or "用户"
            results = self._search_memories(user_id, keyword)
            
            if not results:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("未找到", f"没有找到关于 '{keyword}' 的记忆", action="搜索失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 没有找到相关记忆")
                return
            
            if HAS_PILLOW:
                img_base64 = self._create_memory_list_image(results, user_name)
                yield event.image_result(img_base64)
            else:
                response = f"🔍 找到 {len(results)} 条相关记忆:\n"
                for key, memory in results[:10]:
                    response += f"- {key}: {memory['content']}\n"
                
                if len(results) > 10:
                    response += f"... 还有 {len(results) - 10} 条"
                
                yield event.plain_result(response.strip())
                
        except Exception as e:
            logger.error(f"搜索记忆指令错误: {e}")
            if HAS_PILLOW:
                img_base64 = self._create_memory_card("错误", "系统错误，请稍后重试", action="搜索失败")
                yield event.image_result(img_base64)
            else:
                yield event.plain_result("❌ 系统错误，请稍后重试")
    
    @filter.command("我的记忆")
    async def list_memories_command(self, event: AstrMessageEvent):
        """列出所有记忆指令
        用法: /我的记忆
        """
        try:
            user_id = event.get_sender_id()
            user_name = event.get_sender_name() or "用户"
            memories = self._get_user_memories(user_id)
            
            if not memories:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("提示", "你还没有任何记忆", action="我的记忆")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("📭 你还没有任何记忆")
                return
            
            if HAS_PILLOW:
                img_base64 = self._create_memory_list_image(memories, user_name)
                yield event.image_result(img_base64)
            else:
                response = f"📚 你共有 {len(memories)} 条记忆:\n"
                for key, memory in memories[:10]:
                    response += f"- {key}: {memory['content']}\n"
                
                if len(memories) > 10:
                    response += f"... 还有 {len(memories) - 10} 条"
                
                yield event.plain_result(response.strip())
                
        except Exception as e:
            logger.error(f"列出记忆指令错误: {e}")
            if HAS_PILLOW:
                img_base64 = self._create_memory_card("错误", "系统错误，请稍后重试", action="我的记忆")
                yield event.image_result(img_base64)
            else:
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
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("错误", "格式错误！用法: /删除记忆 关键词", action="删除失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 格式错误！用法: /删除记忆 关键词")
                return
            
            user_id = event.get_sender_id()
            user_name = event.get_sender_name() or "用户"
            
            if self._delete_memory(user_id, key):
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("成功", f"已删除记忆: {key}", action="删除成功")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result(f"✅ 已删除记忆: {key}")
            else:
                if HAS_PILLOW:
                    img_base64 = self._create_memory_card("未找到", f"没有找到关于 '{key}' 的记忆", action="删除失败")
                    yield event.image_result(img_base64)
                else:
                    yield event.plain_result("❌ 没有找到相关记忆")
                    
        except Exception as e:
            logger.error(f"删除记忆指令错误: {e}")
            if HAS_PILLOW:
                img_base64 = self._create_memory_card("错误", "系统错误，请稍后重试", action="删除失败")
                yield event.image_result(img_base64)
            else:
                yield event.plain_result("❌ 系统错误，请稍后重试")
    
    async def terminate(self):
        """插件卸载时保存数据"""
        self._save_memories()
        logger.info("个人记忆插件已卸载，数据已保存")
    
    def _create_memory_card(self, title: str, content: str, tags: List[str] = None, 
                          action: str = "记住", user_name: str = "用户") -> str:
        """创建记忆卡片图片"""
        if not HAS_PILLOW:
            return f"{action}成功！\n{title}: {content}"
        
        try:
            # 计算图片高度
            lines = len(content) // 30 + 2
            height = max(200, min(400, 150 + lines * 20))
            
            # 创建图片
            img = Image.new('RGB', (self.card_width, height), self.bg_color)
            draw = ImageDraw.Draw(img)
            
            # 使用默认字体
            try:
                title_font = ImageFont.truetype("arial.ttf", 24)
                content_font = ImageFont.truetype("arial.ttf", 16)
                tag_font = ImageFont.truetype("arial.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                content_font = ImageFont.load_default()
                tag_font = ImageFont.load_default()
            
            # 绘制标题背景
            draw.rectangle([(0, 0), (self.card_width, 60)], fill=self.primary_color)
            
            # 绘制标题
            title_text = f"🧠 {action}成功"
            draw.text((20, 15), title_text, fill='white', font=title_font)
            
            # 绘制关键词
            draw.text((20, 80), f"关键词：{title}", fill=self.text_color, font=content_font)
            
            # 绘制内容
            content_lines = [content[i:i+40] for i in range(0, len(content), 40)]
            y_pos = 110
            for line in content_lines[:3]:  # 最多3行
                draw.text((20, y_pos), line, fill=self.text_color, font=content_font)
                y_pos += 25
            
            # 绘制标签
            if tags:
                tag_text = "标签：" + " ".join([f"#{tag}" for tag in tags])
                draw.text((20, y_pos + 10), tag_text, fill=self.muted_color, font=tag_font)
            
            # 绘制时间
            time_text = datetime.now().strftime("%Y-%m-%d %H:%M")
            draw.text((self.card_width - 150, height - 30), time_text, fill=self.muted_color, font=tag_font)
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=85, optimize=True)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"创建图片失败: {e}")
            return f"{action}成功！\n{title}: {content}"
    
    def _create_memory_list_image(self, memories: List[Tuple[str, Dict]], user_name: str = "用户") -> str:
        """创建记忆列表图片"""
        if not HAS_PILLOW:
            response = f"📚 {user_name}的记忆列表：\n"
            for key, memory in memories:
                response += f"- {key}: {memory['content'][:50]}...\n"
            return response
        
        try:
            # 计算高度
            item_height = 80
            height = 120 + len(memories) * item_height
            height = min(800, height)
            
            img = Image.new('RGB', (self.card_width, height), self.bg_color)
            draw = ImageDraw.Draw(img)
            
            try:
                title_font = ImageFont.truetype("arial.ttf", 20)
                content_font = ImageFont.truetype("arial.ttf", 14)
                count_font = ImageFont.truetype("arial.ttf", 12)
            except:
                title_font = content_font = count_font = ImageFont.load_default()
            
            # 标题背景
            draw.rectangle([(0, 0), (self.card_width, 60)], fill=self.primary_color)
            draw.text((20, 15), f"📚 {user_name}的记忆列表", fill='white', font=title_font)
            draw.text((20, 40), f"共{len(memories)}条记忆", fill='white', font=count_font)
            
            # 绘制每条记忆
            y_pos = 80
            for key, memory in memories[:10]:  # 最多10条
                # 记忆卡片背景
                draw.rectangle([(10, y_pos), (self.card_width-10, y_pos+70)], 
                             fill='white', outline=self.muted_color)
                
                # 关键词
                draw.text((20, y_pos+5), key, fill=self.text_color, font=content_font)
                
                # 内容预览
                preview = memory['content'][:50] + "..." if len(memory['content']) > 50 else memory['content']
                draw.text((20, y_pos+25), preview, fill=self.muted_color, font=count_font)
                
                # 使用次数
                count_text = f"使用{memory.get('usage_count', 0)}次"
                draw.text((self.card_width-100, y_pos+5), count_text, fill=self.muted_color, font=count_font)
                
                y_pos += 75
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=85, optimize=True)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"创建列表图片失败: {e}")
            response = f"📚 {user_name}的记忆列表：\n"
            for key, memory in memories:
                response += f"- {key}: {memory['content'][:50]}...\n"
            return response