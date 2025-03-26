"""
センサーデータを生成するモジュール
"""
import random
import time
import math
from typing import Dict, Any, Optional, Union, Tuple


class DataGenerator:
    """センサーデータを生成するクラス"""

    def __init__(self, config: Dict[str, Any]):
        """
        初期化

        Args:
            config: 設定データ
        """
        self.config = config
        self.devices = config["devices"]
        self.failure_config = config["failure_simulation"]
        self.failure_enabled = self.failure_config["enabled"]
        
        # 故障シミュレーション用の状態管理
        self.device_states = {}
        self.last_values = {}
        self.initialize_device_states()
        
    def initialize_device_states(self):
        """デバイスの初期状態を設定"""
        for device_id, device_config in self.devices.items():
            self.device_states[device_id] = {
                "is_failing": False,
                "failure_end_time": 0,
                "next_failure_time": self._calculate_next_failure_time()
            }
            
            # 初期値を設定
            self.last_values[device_id] = {}
            for sensor_id, sensor_config in device_config["sensors"].items():
                if sensor_config.get("type") == "boolean":
                    self.last_values[device_id][sensor_id] = sensor_config["normal_value"]
                else:
                    normal_min = sensor_config["normal_min"]
                    normal_max = sensor_config["normal_max"]
                    self.last_values[device_id][sensor_id] = random.uniform(normal_min, normal_max)
    
    def _calculate_next_failure_time(self) -> float:
        """
        次の故障発生時間を計算

        Returns:
            float: 次の故障発生時間（UNIXタイムスタンプ）
        """
        if not self.failure_enabled:
            return float('inf')
            
        # 平均故障間隔を使用して指数分布に従った次の故障時間を計算
        mean_time = self.failure_config["mean_time_between_failures"]
        # 指数分布を使用して次の故障までの時間を生成
        next_failure_delta = random.expovariate(1.0 / mean_time)
        return time.time() + next_failure_delta
    
    def _calculate_failure_duration(self) -> float:
        """
        故障の継続時間を計算

        Returns:
            float: 故障の継続時間（秒）
        """
        min_duration = self.failure_config["failure_duration_min"]
        max_duration = self.failure_config["failure_duration_max"]
        return random.uniform(min_duration, max_duration)
    
    def _update_failure_states(self):
        """故障状態を更新"""
        current_time = time.time()
        
        for device_id, state in self.device_states.items():
            # 故障中のデバイスをチェック
            if state["is_failing"] and current_time > state["failure_end_time"]:
                # 故障から回復
                state["is_failing"] = False
                state["next_failure_time"] = self._calculate_next_failure_time()
                print(f"デバイス '{self.devices[device_id]['name']}' が故障から回復しました")
            
            # 故障していないデバイスで次の故障時間に達したかチェック
            elif not state["is_failing"] and current_time > state["next_failure_time"]:
                # 故障発生
                state["is_failing"] = True
                failure_duration = self._calculate_failure_duration()
                state["failure_end_time"] = current_time + failure_duration
                print(f"デバイス '{self.devices[device_id]['name']}' が故障しました。予想復旧時間: {failure_duration:.1f}秒後")
    
    def _generate_sensor_value(
        self, 
        device_id: str, 
        sensor_id: str, 
        sensor_config: Dict[str, Any],
        is_failing: bool
    ) -> Union[float, bool, int]:
        """
        センサー値を生成

        Args:
            device_id: デバイスID
            sensor_id: センサーID
            sensor_config: センサー設定
            is_failing: 故障中かどうか

        Returns:
            Union[float, bool, int]: 生成されたセンサー値
        """
        # 前回の値を取得
        last_value = self.last_values[device_id].get(sensor_id)
        
        # ブール型の場合
        if sensor_config.get("type") == "boolean":
            if is_failing:
                return sensor_config["failure_value"]
            else:
                return sensor_config["normal_value"]
        
        # カウンター型の場合（サイクル数など）
        if "increment_min" in sensor_config:
            increment = 0 if is_failing and sensor_config.get("failure_increment") == 0 else random.randint(
                sensor_config["increment_min"], 
                sensor_config.get("increment_max", sensor_config["increment_min"])
            )
            new_value = last_value + increment
            # 最大値を超えないようにする
            if "max" in sensor_config and new_value > sensor_config["max"]:
                new_value = sensor_config["min"]
            return new_value
        
        # 通常の数値センサー
        if is_failing:
            target_min = sensor_config["failure_min"]
            target_max = sensor_config["failure_max"]
        else:
            target_min = sensor_config["normal_min"]
            target_max = sensor_config["normal_max"]
        
        # 現在値から目標範囲内の値へ徐々に変化させる
        target = random.uniform(target_min, target_max)
        # 前回の値と目標値の間を補間（急激な変化を避けるため）
        change_rate = 0.1  # 変化率（0.1 = 10%の変化）
        new_value = last_value + (target - last_value) * change_rate
        
        # 一部のセンサーに周期的な変動を追加
        if sensor_id in ["speed", "pressure", "rotation_speed", "temperature"]:
            # sin波による周期的な変動を追加
            period = 60.0  # 周期（秒）
            amplitude = (target_max - target_min) * 0.05  # 振幅（範囲の5%）
            new_value += amplitude * math.sin(time.time() * 2 * math.pi / period)
        
        # 値の範囲を制限
        new_value = max(sensor_config["min"], min(new_value, sensor_config["max"]))
        
        return new_value
    
    def generate_data(self) -> Dict[str, Dict[str, Union[float, bool, int]]]:
        """
        全デバイスのセンサーデータを生成

        Returns:
            Dict: デバイスとセンサーの階層構造でデータを返す
        """
        # 故障状態を更新
        self._update_failure_states()
        
        result = {}
        
        for device_id, device_config in self.devices.items():
            device_data = {}
            is_failing = self.device_states[device_id]["is_failing"]
            
            for sensor_id, sensor_config in device_config["sensors"].items():
                # センサー値を生成
                value = self._generate_sensor_value(device_id, sensor_id, sensor_config, is_failing)
                # 結果を保存
                device_data[sensor_id] = value
                # 最後の値を更新
                self.last_values[device_id][sensor_id] = value
            
            result[device_id] = device_data
        
        return result
