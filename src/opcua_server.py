"""
OPC-UAサーバーの実装
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Union

from asyncua import Server, ua
from asyncua.common.node import Node

from data_generator import DataGenerator


class OpcUaServer:
    """OPC-UAサーバークラス"""

    def __init__(self, config: Dict[str, Any], data_generator: DataGenerator):
        """
        初期化

        Args:
            config: 設定データ
            data_generator: データ生成器
        """
        self.config = config
        self.server_config = config["server"]
        self.data_generator = data_generator
        
        # サーバーの設定
        self.server = Server()
        
        # 名前空間の設定
        self.uri = self.server_config["uri"]
        self.idx = None  # 名前空間インデックス（初期化時に設定）
        
        # ノードの参照を保持
        self.nodes = {}
        
        # 更新間隔
        self.update_interval = self.server_config["update_interval"]
        
        # ロガーの設定
        self.logger = logging.getLogger(__name__)
        
    async def init(self):
        """サーバーの初期化"""
        # サーバーの初期化
        await self.server.init()
        self.server.set_endpoint(self.server_config["endpoint"])
        self.server.set_server_name(self.server_config["name"])
        
        # 名前空間の登録
        self.idx = await self.server.register_namespace(self.uri)
        
        # オブジェクトの作成
        objects = self.server.nodes.objects
        
        # 工場オブジェクトの作成
        factory = await objects.add_object(self.idx, "Factory")
        
        # 生産ラインの作成
        production_line1 = await factory.add_object(self.idx, "ProductionLine1")
        production_line2 = await factory.add_object(self.idx, "ProductionLine2")
        environment = await factory.add_object(self.idx, "Environment")
        
        # デバイスとセンサーの作成
        for device_id, device_config in self.config["devices"].items():
            # デバイスの親オブジェクトを決定
            if device_id in ["conveyor_belt", "press_machine", "welding_robot"]:
                parent = production_line1
            elif device_id in ["cnc_machine", "painting_booth"]:
                parent = production_line2
            else:
                parent = environment
            
            # デバイスオブジェクトの作成
            device_node = await parent.add_object(self.idx, device_config["name"])
            self.nodes[device_id] = {"node": device_node, "sensors": {}}
            
            # センサーの作成
            for sensor_id, sensor_config in device_config["sensors"].items():
                sensor_name = sensor_config["name"]
                
                # センサーの種類に応じた変数を作成
                if sensor_config.get("type") == "boolean":
                    var = await device_node.add_variable(
                        self.idx, 
                        sensor_name, 
                        ua.Variant(sensor_config["normal_value"], ua.VariantType.Boolean)
                    )
                    # 単位の設定
                    if "unit" in sensor_config:
                        await var.add_property(self.idx, "EngineeringUnits", sensor_config["unit"])
                elif "increment_min" in sensor_config:  # カウンター型
                    var = await device_node.add_variable(
                        self.idx, 
                        sensor_name, 
                        ua.Variant(0, ua.VariantType.UInt32)
                    )
                    # 単位の設定
                    if "unit" in sensor_config:
                        await var.add_property(self.idx, "EngineeringUnits", sensor_config["unit"])
                else:  # 通常の数値型
                    var = await device_node.add_variable(
                        self.idx, 
                        sensor_name, 
                        ua.Variant(0.0, ua.VariantType.Double)
                    )
                    # 単位の設定
                    if "unit" in sensor_config:
                        await var.add_property(self.idx, "EngineeringUnits", sensor_config["unit"])
                
                # 変数を書き込み可能に設定
                await var.set_writable()
                
                # ノード参照を保存
                self.nodes[device_id]["sensors"][sensor_id] = var
    
    async def update_data(self):
        """センサーデータの更新"""
        while True:
            try:
                # データの生成
                data = self.data_generator.generate_data()
                
                # OPC-UAノードの更新
                for device_id, device_data in data.items():
                    for sensor_id, value in device_data.items():
                        node = self.nodes[device_id]["sensors"][sensor_id]
                        
                        # 値の型に応じた設定
                        if isinstance(value, bool):
                            await node.write_value(ua.Variant(value, ua.VariantType.Boolean))
                        elif isinstance(value, int):
                            await node.write_value(ua.Variant(value, ua.VariantType.UInt32))
                        else:
                            await node.write_value(ua.Variant(value, ua.VariantType.Double))
                
                # 更新間隔を待機
                await asyncio.sleep(self.update_interval)
            
            except Exception as e:
                self.logger.error(f"データ更新中にエラーが発生しました: {e}")
                await asyncio.sleep(1)  # エラー時は少し待機してから再試行
    
    async def start(self):
        """サーバーの起動"""
        try:
            await self.init()
            
            # サーバーの起動
            async with self.server:
                self.logger.info(f"サーバーを起動しました: {self.server_config['endpoint']}")
                
                # データ更新タスクの開始
                update_task = asyncio.create_task(self.update_data())
                
                # サーバーを実行し続ける
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"サーバー起動中にエラーが発生しました: {e}")
            raise
                
    def stop(self):
        """サーバーの停止"""
        self.logger.info("サーバーを停止します")
        # サーバーはasync withブロックを抜けると自動的に停止する
