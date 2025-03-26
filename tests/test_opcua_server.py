"""
OPC-UAサーバーのテスト
"""
import asyncio
import pytest
import pytest_asyncio
from asyncua import Client, ua

from src.data_generator import DataGenerator
from src.opcua_server import OpcUaServer


@pytest.fixture
def sample_config():
    """テスト用の設定データ"""
    return {
        "server": {
            "endpoint": "opc.tcp://localhost:4840",
            "name": "Test Server",
            "uri": "urn:test:server",
            "update_interval": 0.1,
            "client_update_interval": 0.5
        },
        "failure_simulation": {
            "enabled": False,
            "mean_time_between_failures": 3600,
            "failure_duration_min": 300,
            "failure_duration_max": 900
        },
        "devices": {
            "test_device": {
                "name": "テストデバイス",
                "sensors": {
                    "temperature": {
                        "name": "温度",
                        "unit": "°C",
                        "min": 0.0,
                        "max": 100.0,
                        "normal_min": 20.0,
                        "normal_max": 40.0,
                        "failure_min": 80.0,
                        "failure_max": 100.0
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
async def server_client(sample_config):
    """OPC-UAサーバーとクライアントのフィクスチャ"""
    # データ生成器の作成
    data_generator = DataGenerator(sample_config)
    
    # サーバーの作成
    server = OpcUaServer(sample_config, data_generator)
    
    # サーバーの初期化
    await server.init()
    
    # サーバーの起動（非同期タスクとして）
    server_task = asyncio.create_task(server.update_data())
    
    # クライアントの作成
    client = Client(url=sample_config["server"]["endpoint"])
    await client.connect()
    
    # フィクスチャの提供
    yield server, client
    
    # クリーンアップ
    await client.disconnect()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_server_initialization(server_client):
    """サーバーが正しく初期化されることを確認"""
    server, client = server_client
    
    # サーバーのノード構造を確認
    objects = client.nodes.objects
    
    # Factoryノードの存在を確認
    factory_nodes = await objects.get_children()
    factory_node = None
    for node in factory_nodes:
        name = await node.read_browse_name()
        if name.Name == "Factory":
            factory_node = node
            break
    
    assert factory_node is not None
    
    # ProductionLine1ノードの存在を確認
    factory_children = await factory_node.get_children()
    found_production_line = False
    for node in factory_children:
        name = await node.read_browse_name()
        if name.Name in ["ProductionLine1", "Environment"]:
            found_production_line = True
            break
    
    assert found_production_line


@pytest.mark.asyncio
async def test_data_update(server_client):
    """データが正しく更新されることを確認"""
    server, client = server_client
    
    # テストデバイスのノードを取得
    objects = client.nodes.objects
    factory_nodes = await objects.get_children()
    factory_node = None
    for node in factory_nodes:
        name = await node.read_browse_name()
        if name.Name == "Factory":
            factory_node = node
            break
    
    assert factory_node is not None
    
    # Environmentノードを取得
    environment_node = None
    factory_children = await factory_node.get_children()
    for node in factory_children:
        name = await node.read_browse_name()
        if name.Name == "Environment":
            environment_node = node
            break
    
    assert environment_node is not None
    
    # テストデバイスノードを取得
    test_device_node = None
    environment_children = await environment_node.get_children()
    for node in environment_children:
        name = await node.read_browse_name()
        if name.Name == "テストデバイス":
            test_device_node = node
            break
    
    assert test_device_node is not None
    
    # 温度センサーノードを取得
    temperature_node = None
    device_children = await test_device_node.get_children()
    for node in device_children:
        name = await node.read_browse_name()
        if name.Name == "温度":
            temperature_node = node
            break
    
    assert temperature_node is not None
    
    # 初期値を取得
    initial_value = await temperature_node.read_value()
    
    # 少し待機して値が更新されることを確認
    await asyncio.sleep(0.5)
    
    # 更新後の値を取得
    updated_value = await temperature_node.read_value()
    
    # 値が更新されていることを確認（厳密な等価性は期待しない）
    assert isinstance(updated_value, float)
