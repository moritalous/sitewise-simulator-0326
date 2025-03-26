"""
統合テスト
"""
import asyncio
import pytest
import pytest_asyncio
from asyncua import Client, ua

from src.config_loader import load_config
from src.data_generator import DataGenerator
from src.opcua_server import OpcUaServer


@pytest.fixture
def test_config():
    """テスト用の設定"""
    return {
        "server": {
            "endpoint": "opc.tcp://localhost:4841",  # 通常のテストと競合しないポート
            "name": "Integration Test Server",
            "uri": "urn:integration:test",
            "update_interval": 0.1,
            "client_update_interval": 0.5
        },
        "failure_simulation": {
            "enabled": True,
            "mean_time_between_failures": 10,  # テスト用に短い間隔
            "failure_duration_min": 1,
            "failure_duration_max": 2
        },
        "devices": {
            "conveyor_belt": {
                "name": "コンベアベルト",
                "sensors": {
                    "speed": {
                        "name": "速度",
                        "unit": "m/s",
                        "min": 0.5,
                        "max": 2.0,
                        "normal_min": 0.8,
                        "normal_max": 1.5,
                        "failure_min": 0.0,
                        "failure_max": 0.3
                    },
                    "status": {
                        "name": "稼働状態",
                        "type": "boolean",
                        "normal_value": True,
                        "failure_value": False
                    }
                }
            }
        }
    }


@pytest_asyncio.fixture
async def server_client(test_config):
    """OPC-UAサーバーとクライアントのフィクスチャ"""
    # データ生成器の作成
    data_generator = DataGenerator(test_config)
    
    # サーバーの作成
    server = OpcUaServer(test_config, data_generator)
    
    # サーバーの初期化
    await server.init()
    
    # サーバーの起動（非同期タスクとして）
    server_task = asyncio.create_task(server.update_data())
    
    # クライアントの作成
    client = Client(url=test_config["server"]["endpoint"])
    await client.connect()
    
    # フィクスチャの提供
    yield server, client, data_generator
    
    # クリーンアップ
    await client.disconnect()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_client_can_read_data(server_client):
    """クライアントがデータを読み取れることを確認"""
    server, client, _ = server_client
    
    # 名前空間のインデックスを取得
    nsindex = await client.get_namespace_index(server.uri)
    
    # コンベアベルトの速度ノードを取得
    speed_node = await client.nodes.objects.get_child(
        ["0:Factory", f"{nsindex}:ProductionLine1", f"{nsindex}:コンベアベルト", f"{nsindex}:速度"]
    )
    
    # 値を読み取り
    speed_value = await speed_node.read_value()
    
    # 値が範囲内にあることを確認
    assert 0.0 <= speed_value <= 2.0
    
    # ステータスノードを取得
    status_node = await client.nodes.objects.get_child(
        ["0:Factory", f"{nsindex}:ProductionLine1", f"{nsindex}:コンベアベルト", f"{nsindex}:稼働状態"]
    )
    
    # 値を読み取り
    status_value = await status_node.read_value()
    
    # ブール値であることを確認
    assert isinstance(status_value, bool)


@pytest.mark.asyncio
async def test_data_updates_over_time(server_client):
    """時間経過とともにデータが更新されることを確認"""
    server, client, _ = server_client
    
    # 名前空間のインデックスを取得
    nsindex = await client.get_namespace_index(server.uri)
    
    # コンベアベルトの速度ノードを取得
    speed_node = await client.nodes.objects.get_child(
        ["0:Factory", f"{nsindex}:ProductionLine1", f"{nsindex}:コンベアベルト", f"{nsindex}:速度"]
    )
    
    # 初期値を読み取り
    initial_value = await speed_node.read_value()
    
    # 少し待機
    await asyncio.sleep(0.5)
    
    # 更新後の値を読み取り
    updated_value = await speed_node.read_value()
    
    # 値が更新されていることを確認（厳密な等価性は期待しない）
    assert initial_value != updated_value


@pytest.mark.asyncio
async def test_failure_simulation(server_client):
    """故障シミュレーションが機能することを確認"""
    server, client, data_generator = server_client
    
    # 名前空間のインデックスを取得
    nsindex = await client.get_namespace_index(server.uri)
    
    # コンベアベルトのステータスノードを取得
    status_node = await client.nodes.objects.get_child(
        ["0:Factory", f"{nsindex}:ProductionLine1", f"{nsindex}:コンベアベルト", f"{nsindex}:稼働状態"]
    )
    
    # 故障を強制的に発生させる
    data_generator.device_states["conveyor_belt"]["is_failing"] = True
    
    # データを更新
    data_generator.generate_data()
    
    # サーバーの更新を待機
    await asyncio.sleep(0.2)
    
    # 故障状態を確認
    status_value = await status_node.read_value()
    assert status_value is False  # 故障時はFalse
    
    # 速度ノードを取得
    speed_node = await client.nodes.objects.get_child(
        ["0:Factory", f"{nsindex}:ProductionLine1", f"{nsindex}:コンベアベルト", f"{nsindex}:速度"]
    )
    
    # 速度値を読み取り
    speed_value = await speed_node.read_value()
    
    # 故障時は速度が低下することを確認
    assert 0.0 <= speed_value <= 0.5  # 故障時の範囲
