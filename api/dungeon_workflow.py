"""
副本工作流API
提供场景、周目、属性、存档、回忆等REST API端点
"""

import json
import os
import time
from typing import Optional

try:
    from aiohttp import web
except ImportError:
    web = None

try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..core.scene_manager import SceneManager
from ..core.playthrough_manager import PlaythroughManager
from ..core.save_manager import SaveManager
from ..core.asset_manager import AssetManager
from ..core.recall_system import RecallSystem


class DungeonWorkflowAPI:
    """
    副本工作流API
    提供REST API端点
    """

    def __init__(self, db_path: str, assets_dir: str = "assets"):
        """
        初始化API

        Args:
            db_path: 数据库路径
            assets_dir: 资产目录
        """
        self.db_path = db_path
        self.scene_manager = SceneManager(db_path)
        self.playthrough_manager = PlaythroughManager(db_path)
        self.save_manager = SaveManager(db_path)
        self.asset_manager = AssetManager(db_path, assets_dir)
        self.recall_system = RecallSystem(db_path)

    def setup_routes(self, app: web.Application):
        """设置API路由"""
        # 周目API
        app.router.add_get("/api/playthroughs", self.get_playthroughs)
        app.router.add_post("/api/playthroughs", self.create_playthrough)
        app.router.add_get("/api/playthroughs/current", self.get_current_playthrough)
        app.router.add_get("/api/playthroughs/{id}", self.get_playthrough)
        app.router.add_put("/api/playthroughs/{id}", self.update_playthrough)
        app.router.add_delete("/api/playthroughs/{id}", self.delete_playthrough)

        # 场景API
        app.router.add_get("/api/scenes", self.get_scenes)
        app.router.add_post("/api/scenes", self.create_scene)
        app.router.add_get("/api/scenes/{id}", self.get_scene)
        app.router.add_put("/api/scenes/{id}", self.update_scene)
        app.router.add_put("/api/scenes/{id}/progress", self.update_scene_progress)
        app.router.add_delete("/api/scenes/{id}", self.delete_scene)
        app.router.add_get("/api/scenes/timeline/{playthrough_id}", self.get_scene_timeline)

        # 属性API
        app.router.add_get("/api/attributes", self.get_attributes)
        app.router.add_post("/api/attributes", self.create_attribute)
        app.router.add_put("/api/attributes/{id}", self.update_attribute)
        app.router.add_get("/api/attributes/{id}/history", self.get_attribute_history)
        app.router.add_get("/api/attributes/panel/{playthrough_id}", self.get_attribute_panel)

        # 存档API
        app.router.add_get("/api/saves", self.get_saves)
        app.router.add_post("/api/saves", self.create_save)
        app.router.add_get("/api/saves/{id}", self.get_save)
        app.router.add_put("/api/saves/{id}", self.update_save)
        app.router.add_delete("/api/saves/{id}", self.delete_save)
        app.router.add_post("/api/saves/{id}/export", self.export_save)
        app.router.add_post("/api/saves/import", self.import_save)

        # 回忆API
        app.router.add_get("/api/recall", self.get_recall)
        app.router.add_post("/api/recall/memories", self.discover_memory)
        app.router.add_delete("/api/recall/memories/{id}", self.delete_memory)
        app.router.add_get("/api/recall/endings", self.get_endings)
        app.router.add_post("/api/recall/endings", self.unlock_ending)
        app.router.add_get("/api/recall/destiny-map", self.get_destiny_map)

        # 资产API
        app.router.add_get("/api/assets", self.get_assets)
        app.router.add_post("/api/assets", self.upload_asset)
        app.router.add_get("/api/assets/{id}", self.get_asset)
        app.router.add_delete("/api/assets/{id}", self.delete_asset)

    # ============================================
    # 周目API
    # ============================================

    async def get_playthroughs(self, request: web.Request) -> web.Response:
        """获取周目列表"""
        playthroughs = self.playthrough_manager.get_playthrough_history()
        data = [
            {
                "id": p.id,
                "number": p.playthrough_number,
                "status": p.status,
                "route": p.route,
                "started_at": p.started_at,
                "completed_at": p.completed_at,
                "ending": p.ending,
            }
            for p in playthroughs
        ]
        return web.json_response({"playthroughs": data})

    async def create_playthrough(self, request: web.Request) -> web.Response:
        """创建新周目"""
        try:
            body = await request.json()
            route = body.get("route")
            playthrough = self.playthrough_manager.start_new_playthrough(route)
            return web.json_response(
                {
                    "id": playthrough.id,
                    "number": playthrough.playthrough_number,
                    "status": playthrough.status,
                    "route": playthrough.route,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_current_playthrough(self, request: web.Request) -> web.Response:
        """获取当前周目"""
        playthrough = self.playthrough_manager.get_current_playthrough()
        if not playthrough:
            return web.json_response({"error": "没有活跃的周目"}, status=404)
        return web.json_response(
            {
                "id": playthrough.id,
                "number": playthrough.playthrough_number,
                "status": playthrough.status,
                "route": playthrough.route,
                "started_at": playthrough.started_at,
            }
        )

    async def get_playthrough(self, request: web.Request) -> web.Response:
        """获取周目详情"""
        playthrough_id = request.match_info["id"]
        playthrough = self.playthrough_manager.get_playthrough(playthrough_id)
        if not playthrough:
            return web.json_response({"error": "周目不存在"}, status=404)
        return web.json_response(
            {
                "id": playthrough.id,
                "number": playthrough.playthrough_number,
                "status": playthrough.status,
                "route": playthrough.route,
                "started_at": playthrough.started_at,
                "completed_at": playthrough.completed_at,
                "ending": playthrough.ending,
                "summary": playthrough.summary,
            }
        )

    async def update_playthrough(self, request: web.Request) -> web.Response:
        """更新周目"""
        playthrough_id = request.match_info["id"]
        try:
            body = await request.json()
            ending = body.get("ending")
            summary = body.get("summary", "")

            if ending:
                playthrough = self.playthrough_manager.complete_playthrough(playthrough_id, ending, summary)
            else:
                playthrough = self.playthrough_manager.get_playthrough(playthrough_id)

            if not playthrough:
                return web.json_response({"error": "周目不存在"}, status=404)

            return web.json_response(
                {
                    "id": playthrough.id,
                    "number": playthrough.playthrough_number,
                    "status": playthrough.status,
                    "ending": playthrough.ending,
                }
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def delete_playthrough(self, request: web.Request) -> web.Response:
        """删除周目"""
        playthrough_id = request.match_info["id"]
        success = self.playthrough_manager.delete_playthrough(playthrough_id)
        if not success:
            return web.json_response({"error": "删除失败"}, status=400)
        return web.json_response({"success": True})

    # ============================================
    # 场景API
    # ============================================

    async def get_scenes(self, request: web.Request) -> web.Response:
        """获取场景列表"""
        playthrough_id = request.query.get("playthrough_id")
        if not playthrough_id:
            return web.json_response({"error": "缺少playthrough_id参数"}, status=400)

        scenes = self.scene_manager.get_scenes_by_playthrough(playthrough_id)
        data = [
            {
                "id": s.id,
                "chapter": s.chapter,
                "scene_number": s.scene_number,
                "name": s.name,
                "status": s.status,
                "progress": s.progress,
            }
            for s in scenes
        ]
        return web.json_response({"scenes": data})

    async def create_scene(self, request: web.Request) -> web.Response:
        """创建场景"""
        try:
            body = await request.json()
            playthrough_id = body.get("playthrough_id")
            chapter = body.get("chapter")
            scene_number = body.get("scene_number")
            name = body.get("name")
            description = body.get("description", "")
            sort_order = body.get("sort_order", 0)

            if not all([playthrough_id, chapter, scene_number, name]):
                return web.json_response({"error": "缺少必要参数"}, status=400)

            scene = self.scene_manager.create_scene(
                playthrough_id, chapter, scene_number, name, description, sort_order
            )
            return web.json_response(
                {
                    "id": scene.id,
                    "chapter": scene.chapter,
                    "scene_number": scene.scene_number,
                    "name": scene.name,
                    "status": scene.status,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_scene(self, request: web.Request) -> web.Response:
        """获取场景详情"""
        scene_id = request.match_info["id"]
        scene = self.scene_manager.get_scene(scene_id)
        if not scene:
            return web.json_response({"error": "场景不存在"}, status=404)
        return web.json_response(
            {
                "id": scene.id,
                "playthrough_id": scene.playthrough_id,
                "chapter": scene.chapter,
                "scene_number": scene.scene_number,
                "name": scene.name,
                "description": scene.description,
                "status": scene.status,
                "progress": scene.progress,
            }
        )

    async def update_scene(self, request: web.Request) -> web.Response:
        """更新场景"""
        scene_id = request.match_info["id"]
        try:
            body = await request.json()
            # 实现更新逻辑
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def update_scene_progress(self, request: web.Request) -> web.Response:
        """更新场景进度"""
        scene_id = request.match_info["id"]
        try:
            body = await request.json()
            progress = body.get("progress", 0)
            scene = self.scene_manager.update_scene_progress(scene_id, progress)
            if not scene:
                return web.json_response({"error": "场景不存在"}, status=404)
            return web.json_response(
                {
                    "id": scene.id,
                    "status": scene.status,
                    "progress": scene.progress,
                }
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def delete_scene(self, request: web.Request) -> web.Response:
        """删除场景"""
        scene_id = request.match_info["id"]
        success = self.scene_manager.delete_scene(scene_id)
        if not success:
            return web.json_response({"error": "删除失败"}, status=400)
        return web.json_response({"success": True})

    async def get_scene_timeline(self, request: web.Request) -> web.Response:
        """获取场景时间线"""
        playthrough_id = request.match_info["playthrough_id"]
        timeline = self.scene_manager.get_scene_timeline(playthrough_id)
        return web.json_response(timeline)

    # ============================================
    # 属性API
    # ============================================

    async def get_attributes(self, request: web.Request) -> web.Response:
        """获取属性列表"""
        playthrough_id = request.query.get("playthrough_id")
        if not playthrough_id:
            return web.json_response({"error": "缺少playthrough_id参数"}, status=400)

        attributes = self.playthrough_manager.get_attributes_by_playthrough(playthrough_id)
        data = [
            {
                "id": a.id,
                "name": a.attribute_name,
                "value": a.attribute_value,
                "max_value": a.max_value,
                "min_value": a.min_value,
                "category": a.category,
                "icon": a.icon,
                "percentage": a.percentage,
            }
            for a in attributes
        ]
        return web.json_response({"attributes": data})

    async def create_attribute(self, request: web.Request) -> web.Response:
        """创建属性"""
        try:
            body = await request.json()
            playthrough_id = body.get("playthrough_id")
            name = body.get("name")
            initial_value = body.get("initial_value", 0)
            max_value = body.get("max_value", 100)
            min_value = body.get("min_value", 0)
            category = body.get("category", "other")
            icon = body.get("icon")

            if not all([playthrough_id, name]):
                return web.json_response({"error": "缺少必要参数"}, status=400)

            attribute = self.playthrough_manager.create_attribute(
                playthrough_id, name, initial_value, max_value, min_value, category, icon
            )
            return web.json_response(
                {
                    "id": attribute.id,
                    "name": attribute.attribute_name,
                    "value": attribute.attribute_value,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def update_attribute(self, request: web.Request) -> web.Response:
        """更新属性"""
        attribute_id = request.match_info["id"]
        try:
            body = await request.json()
            delta = body.get("delta", 0)
            reason = body.get("reason", "")

            attribute = self.playthrough_manager.update_attribute_value(attribute_id, delta, reason)
            if not attribute:
                return web.json_response({"error": "属性不存在"}, status=404)

            return web.json_response(
                {
                    "id": attribute.id,
                    "name": attribute.attribute_name,
                    "value": attribute.attribute_value,
                }
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_attribute_history(self, request: web.Request) -> web.Response:
        """获取属性历史"""
        attribute_id = request.match_info["id"]
        history = self.playthrough_manager.get_attribute_history(attribute_id)
        return web.json_response({"history": history})

    async def get_attribute_panel(self, request: web.Request) -> web.Response:
        """获取属性面板"""
        playthrough_id = request.match_info["playthrough_id"]
        panel = self.playthrough_manager.get_attribute_panel(playthrough_id)
        return web.json_response(panel)

    # ============================================
    # 存档API
    # ============================================

    async def get_saves(self, request: web.Request) -> web.Response:
        """获取存档列表"""
        playthrough_id = request.query.get("playthrough_id")
        if not playthrough_id:
            return web.json_response({"error": "缺少playthrough_id参数"}, status=400)

        saves = self.save_manager.get_save_list(playthrough_id)
        return web.json_response({"saves": saves})

    async def create_save(self, request: web.Request) -> web.Response:
        """创建存档"""
        try:
            body = await request.json()
            playthrough_id = body.get("playthrough_id")
            save_type = body.get("save_type", "manual")
            save_name = body.get("save_name")
            save_data = body.get("save_data", {})

            if not playthrough_id:
                return web.json_response({"error": "缺少playthrough_id"}, status=400)

            save = self.save_manager.create_save(playthrough_id, save_type, save_name, save_data)
            return web.json_response(
                {
                    "id": save.id,
                    "save_name": save.save_name,
                    "save_type": save.save_type,
                    "created_at": save.created_at,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_save(self, request: web.Request) -> web.Response:
        """获取存档"""
        save_id = request.match_info["id"]
        save = self.save_manager.get_save(save_id)
        if not save:
            return web.json_response({"error": "存档不存在"}, status=404)

        save_data = self.save_manager.load_save(save_id)
        return web.json_response(
            {
                "id": save.id,
                "save_name": save.save_name,
                "save_type": save.save_type,
                "created_at": save.created_at,
                "data": save_data,
            }
        )

    async def update_save(self, request: web.Request) -> web.Response:
        """更新存档"""
        save_id = request.match_info["id"]
        try:
            body = await request.json()
            save_data = body.get("save_data", {})

            save = self.save_manager.update_save(save_id, save_data)
            if not save:
                return web.json_response({"error": "存档不存在"}, status=404)

            return web.json_response(
                {
                    "id": save.id,
                    "save_name": save.save_name,
                    "updated_at": save.created_at,
                }
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def delete_save(self, request: web.Request) -> web.Response:
        """删除存档"""
        save_id = request.match_info["id"]
        success = self.save_manager.delete_save(save_id)
        if not success:
            return web.json_response({"error": "删除失败"}, status=400)
        return web.json_response({"success": True})

    async def export_save(self, request: web.Request) -> web.Response:
        """导出存档"""
        save_id = request.match_info["id"]
        export_data = self.save_manager.export_save(save_id)
        if not export_data:
            return web.json_response({"error": "导出失败"}, status=400)
        return web.json_response({"export_data": export_data})

    async def import_save(self, request: web.Request) -> web.Response:
        """导入存档"""
        try:
            body = await request.json()
            export_data = body.get("export_data")

            if not export_data:
                return web.json_response({"error": "缺少export_data"}, status=400)

            save = self.save_manager.import_save(export_data)
            if not save:
                return web.json_response({"error": "导入失败"}, status=400)

            return web.json_response(
                {
                    "id": save.id,
                    "save_name": save.save_name,
                    "created_at": save.created_at,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    # ============================================
    # 回忆API
    # ============================================

    async def get_recall(self, request: web.Request) -> web.Response:
        """获取回忆面板"""
        playthrough_id = request.query.get("playthrough_id")
        if not playthrough_id:
            return web.json_response({"error": "缺少playthrough_id参数"}, status=400)

        panel = self.recall_system.get_recall_panel(playthrough_id)
        return web.json_response(panel)

    async def discover_memory(self, request: web.Request) -> web.Response:
        """发现跨周目记忆"""
        try:
            body = await request.json()
            memory_content = body.get("memory_content")
            playthrough_id = body.get("playthrough_id")
            memory_type = body.get("memory_type", "memory")
            related_scene_id = body.get("related_scene_id")
            importance = body.get("importance", 0.5)

            if not all([memory_content, playthrough_id]):
                return web.json_response({"error": "缺少必要参数"}, status=400)

            memory = self.recall_system.discover_memory(
                memory_content, playthrough_id, memory_type, related_scene_id, importance
            )
            return web.json_response(
                {
                    "id": memory.id,
                    "content": memory.memory_content,
                    "type": memory.memory_type,
                    "discovered_at": memory.discovered_at,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def delete_memory(self, request: web.Request) -> web.Response:
        """删除跨周目记忆"""
        memory_id = request.match_info["id"]
        success = self.recall_system.delete_memory(memory_id)
        if not success:
            return web.json_response({"error": "删除失败"}, status=400)
        return web.json_response({"success": True})

    async def get_endings(self, request: web.Request) -> web.Response:
        """获取已解锁结局"""
        playthrough_id = request.query.get("playthrough_id")
        endings = self.recall_system.get_unlocked_endings(playthrough_id)
        return web.json_response({"endings": endings})

    async def unlock_ending(self, request: web.Request) -> web.Response:
        """解锁结局"""
        try:
            body = await request.json()
            ending_name = body.get("ending_name")
            playthrough_id = body.get("playthrough_id")
            ending_description = body.get("ending_description", "")
            ending_data = body.get("ending_data")

            if not all([ending_name, playthrough_id]):
                return web.json_response({"error": "缺少必要参数"}, status=400)

            result = self.recall_system.unlock_ending(
                ending_name, playthrough_id, ending_description, ending_data
            )
            return web.json_response(result, status=201)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_destiny_map(self, request: web.Request) -> web.Response:
        """获取命运地图"""
        destiny_map = self.recall_system.get_destiny_map()
        return web.json_response(destiny_map)

    # ============================================
    # 资产API
    # ============================================

    async def get_assets(self, request: web.Request) -> web.Response:
        """获取场景资产"""
        scene_id = request.query.get("scene_id")
        if not scene_id:
            return web.json_response({"error": "缺少scene_id参数"}, status=400)

        assets = self.asset_manager.get_scene_assets(scene_id)
        return web.json_response(assets)

    async def upload_asset(self, request: web.Request) -> web.Response:
        """上传资产"""
        try:
            reader = await request.multipart()
            field = await reader.next()

            if not field:
                return web.json_response({"error": "没有上传文件"}, status=400)

            # 获取场景ID
            scene_id = request.query.get("scene_id")

            # 保存临时文件
            temp_path = f"/tmp/upload_{int(time.time())}_{field.filename}"
            with open(temp_path, "wb") as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    f.write(chunk)

            # 上传资产
            asset = self.asset_manager.upload_asset(temp_path, scene_id)

            # 删除临时文件
            os.remove(temp_path)

            return web.json_response(
                {
                    "id": asset.id,
                    "file_name": asset.file_name,
                    "asset_type": asset.asset_type,
                    "file_path": asset.file_path,
                },
                status=201,
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def get_asset(self, request: web.Request) -> web.Response:
        """获取资产详情"""
        asset_id = request.match_info["id"]
        asset = self.asset_manager.get_asset(asset_id)
        if not asset:
            return web.json_response({"error": "资产不存在"}, status=404)
        return web.json_response(
            {
                "id": asset.id,
                "scene_id": asset.scene_id,
                "asset_type": asset.asset_type,
                "file_name": asset.file_name,
                "file_path": asset.file_path,
                "thumbnail_path": asset.thumbnail_path,
                "file_size": asset.file_size,
                "mime_type": asset.mime_type,
            }
        )

    async def delete_asset(self, request: web.Request) -> web.Response:
        """删除资产"""
        asset_id = request.match_info["id"]
        success = self.asset_manager.delete_asset(asset_id)
        if not success:
            return web.json_response({"error": "删除失败"}, status=400)
        return web.json_response({"success": True})
