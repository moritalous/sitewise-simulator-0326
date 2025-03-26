"""
設定ローダーのテスト
"""
import os
import pytest
import tempfile
import yaml

from src.config_loader import load_config


def test_load_config_with_valid_file():
    """有効な設定ファイルを読み込めることを確認"""
    # テスト用の設定ファイルを作成
    test_config = {
        "server": {
            "endpoint": "opc.tcp://localhost:4840",
            "name": "Test Server"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        yaml.dump(test_config, temp)
        temp_path = temp.name
    
    try:
        # テスト
        config = load_config(temp_path)
        
        # 検証
        assert config is not None
        assert "server" in config
        assert config["server"]["endpoint"] == "opc.tcp://localhost:4840"
        assert config["server"]["name"] == "Test Server"
    
    finally:
        # 一時ファイルの削除
        os.unlink(temp_path)


def test_load_config_with_nonexistent_file():
    """存在しないファイルを指定した場合にエラーが発生することを確認"""
    with pytest.raises(FileNotFoundError):
        load_config("/path/to/nonexistent/config.yaml")


def test_load_config_with_invalid_yaml():
    """無効なYAMLファイルを指定した場合にエラーが発生することを確認"""
    # 無効なYAMLを含むファイルを作成
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp:
        temp.write("server: {endpoint: 'opc.tcp://localhost:4840', name: 'Test Server'")  # 閉じ括弧がない
        temp_path = temp.name
    
    try:
        # テスト
        with pytest.raises(ValueError):
            load_config(temp_path)
    
    finally:
        # 一時ファイルの削除
        os.unlink(temp_path)
