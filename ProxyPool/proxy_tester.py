import asyncio
import aiohttp
import time
import sys
try:
    from aiohttp import ClientError
except:
    from aiohttp import ClientProxyConnectionError as ProxyConnectionError
from aiohttp.client_exceptions import ClientConnectionError
from asyncio import TimeoutError

from proxy_db import RedisClient
from proxy_crawler import Crawler
from conf import *

class Tester():
    def __init__(self):
        self.redis = RedisClient()

    async def test_single_proxy(self, proxy):
        """
        测试单个代理
        :param proxy:
        :return:None
        """
        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            try:
                if isinstance(proxy, bytes):
                    proxy = proxy.decode('utf-8')
                real_proxy = 'http://'+ proxy
                print('正在测试：{}'.format(proxy))
                async with session.get(TEST_URL, proxy=real_proxy, timeout=15) as respone:
                    if respone.status in VALID_STATUS_CODES:
                        self.redis.max(proxy)
                        print('代理: {} 可用'.format(proxy))
                    else:
                        self.redis.decrease(proxy)
                        print('代理: {} 响应码不合法'.format(proxy))
            except (ClientError, ClientConnectionError, TimeoutError, AttributeError):
                self.redis.decrease(proxy)
                print('代理: {} 不可用'.format(proxy))

    def run(self):
        """
        测试主函数
        :return:
        """
        print('测试器开始运行')
        try:
            proxies = self.redis.all()
            loop = asyncio.get_event_loop()
            #批量测试
            for i in range(0, len(proxies), BATCH_TEST_SIZE):
                test_proxies = proxies[i:i+BATCH_TEST_SIZE]
                tasks = [self.test_single_proxy(proxy) for proxy in test_proxies]
                loop.run_until_complete(asyncio.wait(tasks))
                time.sleep(BATCH_TEST_SLEEP)
        except Exception as e:
            print('测试器发生错误:{}'.format(e.args))
