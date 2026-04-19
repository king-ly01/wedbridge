"""
压力测试脚本 - 模拟 100+ 用户并发创建机器人
"""
import asyncio
import aiohttp
import random
import string
import time
from typing import List, Dict
import argparse


class StressTester:
    """压力测试器"""
    
    def __init__(self, base_url: str, api_port: int = 8899):
        self.base_url = base_url
        self.api_port = api_port
        self.api_url = f"http://{base_url}:{api_port}"
        self.users: List[Dict] = []
        self.results = {
            "users_created": 0,
            "users_failed": 0,
            "bots_created": 0,
            "bots_failed": 0,
            "connections_success": 0,
            "connections_failed": 0,
        }
    
    def random_string(self, length: int = 8) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    async def create_user(self, session: aiohttp.ClientSession, user_index: int) -> Dict:
        """创建用户"""
        username = f"stress_user_{user_index}_{self.random_string(4)}"
        email = f"{username}@test.com"
        password = "Test123456"
        
        try:
            async with session.post(
                f"{self.api_url}/api/auth/register",
                json={"username": username, "email": email, "password": password},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.results["users_created"] += 1
                    print(f"✅ 用户创建成功: {username}")
                    return {
                        "username": username,
                        "password": password,
                        "user_id": data.get("id"),
                        "token": None
                    }
                else:
                    self.results["users_failed"] += 1
                    print(f"❌ 用户创建失败: {username} - {resp.status}")
                    return None
        except Exception as e:
            self.results["users_failed"] += 1
            print(f"❌ 用户创建异常: {username} - {e}")
            return None
    
    async def login_user(self, session: aiohttp.ClientSession, user: Dict, semaphore: asyncio.Semaphore) -> bool:
        """用户登录获取 token"""
        async with semaphore:
            for retry in range(3):  # 重试3次
                try:
                    async with session.post(
                        f"{self.api_url}/api/auth/login",
                        json={"username": user["username"], "password": user["password"]},
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            user["token"] = data.get("access_token")
                            print(f"✅ 登录成功: {user['username']}")
                            return True
                        else:
                            text = await resp.text()
                            print(f"❌ 登录失败: {user['username']} - {resp.status} - {text[:50]}")
                            return False
                except asyncio.TimeoutError:
                    if retry < 2:
                        print(f"⏳ 登录超时，重试 {retry+1}/3: {user['username']}")
                        await asyncio.sleep(1)
                    else:
                        print(f"❌ 登录超时: {user['username']}")
                        return False
                except Exception as e:
                    print(f"❌ 登录异常: {user['username']} - {e}")
                    return False
            return False
    
    async def create_bot(self, session: aiohttp.ClientSession, user: Dict, bot_index: int, semaphore: asyncio.Semaphore) -> bool:
        """为用户创建机器人"""
        if not user.get("token"):
            return False
        
        bot_id = f"bot_{user['username']}_{bot_index}_{self.random_string(4)}"
        
        # 模拟企微机器人配置（使用随机值，实际测试会失败，但测试 API 压力）
        bot_data = {
            "bot_id": bot_id,
            "name": f"测试机器人 {bot_index}",
            "description": "压力测试机器人",
            "wecom_bot_id": f"test_bot_{self.random_string(20)}",
            "wecom_secret": f"test_secret_{self.random_string(32)}",
            "dify_api_key": f"test_key_{self.random_string(32)}",
            "dify_api_base": "http://test.dify.local/v1",
            "enabled": True
        }
        
        headers = {"Authorization": f"Bearer {user['token']}"}
        
        async with semaphore:
            for retry in range(3):
                try:
                    async with session.post(
                        f"{self.api_url}/api/bots",
                        json=bot_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            self.results["bots_created"] += 1
                            print(f"✅ 机器人创建成功: {bot_id} (用户: {user['username']})")
                            return True
                        else:
                            self.results["bots_failed"] += 1
                            text = await resp.text()
                            print(f"❌ 机器人创建失败: {bot_id} - {resp.status} - {text[:50]}")
                            return False
                except asyncio.TimeoutError:
                    if retry < 2:
                        print(f"⏳ 创建机器人超时，重试 {retry+1}/3: {bot_id}")
                        await asyncio.sleep(1)
                    else:
                        self.results["bots_failed"] += 1
                        print(f"❌ 创建机器人超时: {bot_id}")
                        return False
                except Exception as e:
                    self.results["bots_failed"] += 1
                    print(f"❌ 机器人创建异常: {bot_id} - {e}")
                    return False
            return False
    
    async def run_stress_test(self, num_users: int = 100, bots_per_user: int = 3, concurrency: int = 10):
        """
        运行压力测试
        
        Args:
            num_users: 创建的用户数
            bots_per_user: 每个用户创建的机器人数
            concurrency: 并发数
        """
        print(f"\n{'='*60}")
        print(f"开始压力测试")
        print(f"用户数: {num_users}, 每用户机器人数: {bots_per_user}, 并发: {concurrency}")
        print(f"目标: {num_users * bots_per_user} 个机器人")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 阶段 1: 创建用户
            print("【阶段 1】创建用户...")
            semaphore = asyncio.Semaphore(concurrency)
            
            async def create_user_with_limit(i):
                async with semaphore:
                    return await self.create_user(session, i)
            
            user_tasks = [create_user_with_limit(i) for i in range(num_users)]
            users = await asyncio.gather(*user_tasks)
            self.users = [u for u in users if u]
            
            print(f"\n用户创建完成: {len(self.users)}/{num_users}\n")
            
            # 阶段 2: 登录 (提高并发)
            print("【阶段 2】用户登录...")
            login_semaphore = asyncio.Semaphore(20)  # 登录并发提高到20
            login_tasks = [self.login_user(session, u, login_semaphore) for u in self.users]
            await asyncio.gather(*login_tasks)
            
            logged_in_users = [u for u in self.users if u.get("token")]
            print(f"\n登录完成: {len(logged_in_users)}/{len(self.users)}\n")
            
            # 阶段 3: 创建机器人 (提高并发)
            print("【阶段 3】创建机器人...")
            bot_semaphore = asyncio.Semaphore(30)  # 创建机器人并发提高到30
            bot_tasks = []
            for user in logged_in_users:
                for j in range(bots_per_user):
                    bot_tasks.append(
                        asyncio.create_task(self.create_bot(session, user, j, bot_semaphore))
                    )
            
            await asyncio.gather(*bot_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 打印结果
        print(f"\n{'='*60}")
        print(f"压力测试完成")
        print(f"{'='*60}")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"用户创建: {self.results['users_created']}/{num_users} (失败: {self.results['users_failed']})")
        print(f"机器人创建: {self.results['bots_created']}/{num_users * bots_per_user} (失败: {self.results['bots_failed']})")
        print(f"平均每秒: {self.results['bots_created'] / duration:.2f} 个机器人")
        print(f"{'='*60}\n")
        
        return self.results


async def main():
    parser = argparse.ArgumentParser(description='WEDBRIDGE 压力测试')
    parser.add_argument('--host', default='localhost', help='API 主机地址')
    parser.add_argument('--port', type=int, default=8899, help='API 端口')
    parser.add_argument('--users', type=int, default=100, help='用户数量')
    parser.add_argument('--bots-per-user', type=int, default=3, help='每用户机器人数')
    parser.add_argument('--concurrency', type=int, default=10, help='并发数')
    
    args = parser.parse_args()
    
    tester = StressTester(args.host, args.port)
    await tester.run_stress_test(args.users, args.bots_per_user, args.concurrency)


if __name__ == "__main__":
    asyncio.run(main())
