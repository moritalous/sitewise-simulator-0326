"""
データ生成器のテスト
"""
import pytest
import time
from src.data_generator import DataGenerator


@pytest.fixture
def sample_config():
    """テスト用の設定データ"""
    return {
        "failure_simulation": {
            "enabled": True,
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
                    },
                    "counter": {
                        "name": "カウンター",
                        "unit": "count",
                        "min": 0,
                        "max": 1000,
                        "increment_min": 1,
                        "increment_max": 5,
                        "failure_increment": 0,
                        "normal_min": 0,
                        "normal_max": 1000
                    }
                }
            }
        }
    }


def test_data_generator_initialization(sample_config):
    """データ生成器が正しく初期化されることを確認"""
    generator = DataGenerator(sample_config)
    
    # デバイス状態が初期化されていることを確認
    assert "test_device" in generator.device_states
    assert generator.device_states["test_device"]["is_failing"] is False
    
    # 最後の値が初期化されていることを確認
    assert "test_device" in generator.last_values
    assert "temperature" in generator.last_values["test_device"]
    assert "status" in generator.last_values["test_device"]
    assert "counter" in generator.last_values["test_device"]
    
    # 温度が正常範囲内にあることを確認
    temp = generator.last_values["test_device"]["temperature"]
    assert 20.0 <= temp <= 40.0
    
    # ステータスが正常値であることを確認
    assert generator.last_values["test_device"]["status"] is True


def test_generate_data(sample_config):
    """データが正しく生成されることを確認"""
    generator = DataGenerator(sample_config)
    
    # データ生成
    data = generator.generate_data()
    
    # 構造を確認
    assert "test_device" in data
    assert "temperature" in data["test_device"]
    assert "status" in data["test_device"]
    assert "counter" in data["test_device"]
    
    # 値の範囲を確認
    temp = data["test_device"]["temperature"]
    assert 0.0 <= temp <= 100.0
    
    # ブール値を確認
    assert isinstance(data["test_device"]["status"], bool)
    
    # カウンターを確認
    counter = data["test_device"]["counter"]
    assert isinstance(counter, (int, float))
    assert 0 <= counter <= 1000


def test_failure_simulation(sample_config):
    """故障シミュレーションが機能することを確認"""
    generator = DataGenerator(sample_config)
    
    # 故障状態を強制的に設定
    device_id = "test_device"
    generator.device_states[device_id]["is_failing"] = True
    
    # 故障状態が正しく設定されていることを確認
    assert generator.device_states[device_id]["is_failing"] is True
    
    # 故障終了時間を未来に設定して、_update_failure_statesで状態が変わらないようにする
    generator.device_states[device_id]["failure_end_time"] = time.time() + 3600
    
    # データ生成
    data = generator.generate_data()
    
    # 故障時の値を確認（ステータスがFalseになっていることを確認）
    assert data[device_id]["status"] is False  # 故障時はFalse
    
    # 温度が故障範囲内にあることを確認（ただし、すぐには故障範囲に達しない可能性がある）
    # 複数回更新して確認
    initial_temp = data[device_id]["temperature"]
    for _ in range(10):
        data = generator.generate_data()
    
    # 10回の更新後、温度が上昇していることを確認
    assert data[device_id]["temperature"] > initial_temp
