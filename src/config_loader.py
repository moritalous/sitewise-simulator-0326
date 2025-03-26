"""
設定ファイルを読み込むモジュール
"""
import os
import yaml
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    YAMLファイルから設定を読み込む

    Args:
        config_path: 設定ファイルのパス。指定がない場合はデフォルトパスを使用

    Returns:
        Dict[str, Any]: 設定データ
    """
    if config_path is None:
        # デフォルトのパスを使用
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"設定ファイルの解析エラー: {e}")
