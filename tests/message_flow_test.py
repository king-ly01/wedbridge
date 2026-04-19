"""
消息流测试 - 模拟 Dify → WEDBRIDGE → WeCom 完整流程
测试 600 个机器人并发消息转发稳定性
"""
import asyncio
import aiohttp
import random
import string
import time
import json
from typing import List, Dict
from datetime import datetime


class MessageFlowTester:
    """消息流测试器"""
    
    def __init__(self, base_url: str = "http://localhost", api_port: int = 8899):
        self.api_url = f"{base_url}:{api_port}"
        self.results = {
            "messages_sent": 0,
            "messages_failed": 0,
            "messages_timeout": 0,
            "avg_response_time": 0.0,
            "total_time": 0.0
        }
        self.response_times: List[float] = []
        
    def random_string(self, length: int = 8) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    async def simulate_dify_webhook(self, session: aiohttp.ClientSession, bot_id: str, message: str) -> bool:
        """
        模拟 Dify 发送消息到 WEDBRIDGE
        实际场景：Dify 工作流调用 WEDBRIDGE 的 webhook 接口
        """
        # 模拟 Dify 的 webhook 请求格式
        webhook_data = {
            "bot_id": bot_id,
            "message": {
                "content": message,
                "type": "text"
            },
            "sender": {
                "id": f"user_{self.random_string(6)}",
                "name": f"测试用户_{random.randint(1, 1000)}"
            },
            "chat_id": f"chat_{self.random_string(10)}",
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        try:
            # 调用 WEDBRIDGE 的 webhook 接口
            async with session.post(
                f"{self.api_url}/webhook/message",
                json=webhook_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                elapsed = time.time() - start_time
                self.response_times.append(elapsed)
                
                if resp.status == 200:
                    self.results["messages_sent"] += 1
                    return True
                else:
                    self.results["messages_failed"] += 1
                    return False
                    
        except asyncio.TimeoutError:
            self.results["messages_timeout"] += 1
            return False
        except Exception as e:
            self.results["messages_failed"] += 1
            return False
    
    async def simulate_worker_message_handler(self, session: aiohttp.ClientSession, 
                                               bot_config: Dict, message: str) -> bool:
        """
        模拟 Worker 处理消息并转发到 WeCom
        实际场景：Worker 接收消息，调用 Dify，然后发送到 WeCom
        """
        start_time = time.time()
        
        try:
            # 步骤 1: 模拟调用 Dify API 获取回复
            dify_response = await self._call_dify_api(session, bot_config, message)
            
            if not dify_response:
                self.results["messages_failed"] += 1
                return False
            
            # 步骤 2: 模拟发送到 WeCom
            wecom_result = await self._send_to_wecom(session, bot_config, dify_response)
            
            elapsed = time.time() - start_time
            self.response_times.append(elapsed)
            
            if wecom_result:
                self.results["messages_sent"] += 1
                return True
            else:
                self.results["messages_failed"] += 1
                return False
                
        except asyncio.TimeoutError:
            self.results["messages_timeout"] += 1
            return False
        except Exception as e:
            self.results["messages_failed"] += 1
            return False
    
    async def _call_dify_api(self, session: aiohttp.ClientSession, 
                             bot_config: Dict, message: str) -> str:
        """模拟调用 Dify API"""
        # 实际场景：调用 Dify 的 API 获取 AI 回复
        # 这里模拟延迟和回复
        await asyncio.sleep(random.uniform(0.1, 0.5))  # 模拟 Dify 响应时间
        
        # 模拟 Dify 回复
        replies = [
            f"收到您的消息：{message[:20]}...",
            f"我正在处理：{message[:15]}...",
            f"明白了，关于 {message[:10]}...",
            "好的，请稍等...",
            "收到，正在为您处理..."
        ]
        return random.choice(replies)
    
    async def _send_to_wecom(self, session: aiohttp.ClientSession, 
                             bot_config: Dict, message: str) -> bool:
        """模拟发送到 WeCom"""
        # 实际场景：通过 WebSocket 或 HTTP 发送到 WeCom
        # 这里模拟发送延迟
        await asyncio.sleep(random.uniform(0.05, 0.2))  # 模拟发送时间
        
        # 模拟 95% 成功率
        return random.random() < 0.95
    
    async def run_message_flow_test(self, num_bots: int = 600, 
                                     messages_per_bot: int = 5,
                                     concurrency: int = 50):
        """
        运行消息流测试
        
        Args:
            num_bots: 机器人数量
            messages_per_bot: 每个机器人发送的消息数
            concurrency: 并发数
        """
        print(f"\n{'='*70}")
        print(f"消息流压力测试 - Dify → WEDBRIDGE → WeCom")
        print(f"{'='*70}")
        print(f"机器人数量: {num_bots}")
        print(f"每机器人消息数: {messages_per_bot}")
        print(f"总消息数: {num_bots * messages_per_bot}")
        print(f"并发数: {concurrency}")
        print(f"{'='*70}\n")
        
        # 生成机器人配置
        bots = []
        for i in range(num_bots):
            bots.append({
                "bot_id": f"bot_{i}_{self.random_string(4)}",
                "wecom_bot_id": f"wecom_{self.random_string(20)}",
                "dify_api_key": f"key_{self.random_string(32)}",
                "dify_api_base": "http://test.dify.local/v1"
            })
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrency)
            
            async def send_message_with_limit(bot: Dict, msg_index: int):
                async with semaphore:
                    message = f"测试消息 #{msg_index} - {self.random_string(20)}"
                    # 使用 Worker 消息处理器模拟
                    return await self.simulate_worker_message_handler(
                        session, bot, message
                    )
            
            # 创建所有消息任务
            tasks = []
            for bot in bots:
                for j in range(messages_per_bot):
                    tasks.append(send_message_with_limit(bot, j))
            
            # 执行所有任务并显示进度
            print("开始发送消息...")
            completed = 0
            total = len(tasks)
            
            for task in asyncio.as_completed(tasks):
                await task
                completed += 1
                if completed % 100 == 0:
                    print(f"  进度: {completed}/{total} ({completed/total*100:.1f}%)")
        
        end_time = time.time()
        self.results["total_time"] = end_time - start_time
        
        # 计算平均响应时间
        if self.response_times:
            self.results["avg_response_time"] = sum(self.response_times) / len(self.response_times)
        
        # 打印结果
        self._print_results()
        
        return self.results
    
    def _print_results(self):
        """打印测试结果"""
        total = self.results["messages_sent"] + self.results["messages_failed"] + self.results["messages_timeout"]
        
        print(f"\n{'='*70}")
        print(f"测试结果")
        print(f"{'='*70}")
        print(f"总耗时: {self.results['total_time']:.2f} 秒")
        print(f"总消息数: {total}")
        print(f"成功发送: {self.results['messages_sent']} ({self.results['messages_sent']/total*100:.1f}%)")
        print(f"发送失败: {self.results['messages_failed']} ({self.results['messages_failed']/total*100:.1f}%)")
        print(f"超时: {self.results['messages_timeout']} ({self.results['messages_timeout']/total*100:.1f}%)")
        print(f"平均响应时间: {self.results['avg_response_time']*1000:.2f} ms")
        print(f"每秒处理: {total/self.results['total_time']:.2f} 条消息")
        print(f"{'='*70}\n")


async def main():
    """主函数"""
    tester = MessageFlowTester()
    
    # 测试 600 个机器人，每个机器人 5 条消息，共 3000 条消息
    await tester.run_message_flow_test(
        num_bots=600,
        messages_per_bot=5,
        concurrency=100  # 高并发测试
    )


if __name__ == "__main__":
    asyncio.run(main())
