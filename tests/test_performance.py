"""
性能测试
测试API响应时间、并发处理能力
"""

import os
import sys
import time
import statistics
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8352"


class TestAPIPerformance:
    """API 性能测试"""

    def test_api_response_time(self):
        """测试API响应时间"""
        endpoints = [
            "/api/status",
            "/api/playthroughs",
            "/api/playthroughs/current",
            "/api/recall/destiny-map",
        ]

        results = {}
        for endpoint in endpoints:
            times = []
            for _ in range(10):
                start = time.time()
                response = requests.get(f"{BASE_URL}{endpoint}")
                elapsed = time.time() - start
                times.append(elapsed)
                assert response.ok

            results[endpoint] = {
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "p95": sorted(times)[int(len(times) * 0.95)],
            }

        # 打印结果
        print("\nAPI 响应时间测试结果:")
        print("-" * 60)
        for endpoint, metrics in results.items():
            print(f"{endpoint}:")
            print(f"  平均: {metrics['avg']*1000:.2f}ms")
            print(f"  最小: {metrics['min']*1000:.2f}ms")
            print(f"  最大: {metrics['max']*1000:.2f}ms")
            print(f"  P95:  {metrics['p95']*1000:.2f}ms")

        # 验证响应时间
        for endpoint, metrics in results.items():
            assert metrics["avg"] < 1.0, f"{endpoint} 平均响应时间超过1秒"

    def test_concurrent_requests(self):
        """测试并发请求"""
        def make_request(endpoint):
            start = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}")
            elapsed = time.time() - start
            return {
                "endpoint": endpoint,
                "status": response.status_code,
                "time": elapsed
            }

        endpoints = ["/api/status"] * 20

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]
            results = [f.result() for f in as_completed(futures)]

        # 统计结果
        successful = [r for r in results if r["status"] == 200]
        avg_time = statistics.mean([r["time"] for r in successful])

        print(f"\n并发请求测试结果:")
        print(f"  总请求数: {len(results)}")
        print(f"  成功数: {len(successful)}")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        assert len(successful) == len(results), "有请求失败"
        assert avg_time < 2.0, "并发平均响应时间超过2秒"

    def test_create_playthrough_performance(self):
        """测试创建周目性能"""
        times = []
        for i in range(5):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/playthroughs",
                json={"route": f"性能测试路线{i}"}
            )
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.ok

        avg_time = statistics.mean(times)
        print(f"\n创建周目性能测试:")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        assert avg_time < 1.0, "创建周目平均响应时间超过1秒"

    def test_create_scene_performance(self):
        """测试创建场景性能"""
        # 先创建周目
        pt_response = requests.post(
            f"{BASE_URL}/api/playthroughs",
            json={"route": "场景性能测试"}
        )
        pt_id = pt_response.json()["id"]

        times = []
        for i in range(10):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/scenes",
                json={
                    "playthrough_id": pt_id,
                    "chapter": f"第{(i//3)+1}夜",
                    "scene_number": f"{(i//3)+1}-{(i%3)+1}",
                    "name": f"场景{i+1}"
                }
            )
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.ok

        avg_time = statistics.mean(times)
        print(f"\n创建场景性能测试:")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        assert avg_time < 1.0, "创建场景平均响应时间超过1秒"

    def test_get_timeline_performance(self):
        """测试获取时间线性能"""
        # 先创建周目和场景
        pt_response = requests.post(
            f"{BASE_URL}/api/playthroughs",
            json={"route": "时间线性能测试"}
        )
        pt_id = pt_response.json()["id"]

        # 创建多个场景
        for i in range(20):
            requests.post(
                f"{BASE_URL}/api/scenes",
                json={
                    "playthrough_id": pt_id,
                    "chapter": f"第{(i//5)+1}夜",
                    "scene_number": f"{(i//5)+1}-{(i%5)+1}",
                    "name": f"场景{i+1}"
                }
            )

        # 测试获取时间线
        times = []
        for _ in range(10):
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/scenes/timeline/{pt_id}")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.ok

        avg_time = statistics.mean(times)
        print(f"\n获取时间线性能测试:")
        print(f"  场景数量: 20")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        assert avg_time < 1.0, "获取时间线平均响应时间超过1秒"


class TestDatabasePerformance:
    """数据库性能测试"""

    def test_concurrent_writes(self):
        """测试并发写入"""
        def create_playthrough(i):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/playthroughs",
                json={"route": f"并发写入测试{i}"}
            )
            elapsed = time.time() - start
            return elapsed

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_playthrough, i) for i in range(10)]
            times = [f.result() for f in as_completed(futures)]

        avg_time = statistics.mean(times)
        print(f"\n并发写入性能测试:")
        print(f"  并发数: 5")
        print(f"  总操作数: 10")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        assert avg_time < 2.0, "并发写入平均响应时间超过2秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
