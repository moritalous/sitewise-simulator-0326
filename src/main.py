"""
OPC-UAサーバーシミュレーターのメインモジュール
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from src.config_loader import load_config
from src.data_generator import DataGenerator
from src.opcua_server import OpcUaServer


def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main(config_path: Optional[str] = None):
    """
    メイン関数

    Args:
        config_path: 設定ファイルのパス（オプション）
    """
    # ロギングの設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 設定の読み込み
        logger.info("設定を読み込んでいます...")
        config = load_config(config_path)
        
        # データ生成器の作成
        logger.info("データ生成器を初期化しています...")
        data_generator = DataGenerator(config)
        
        # OPC-UAサーバーの作成
        logger.info("OPC-UAサーバーを初期化しています...")
        server = OpcUaServer(config, data_generator)
        
        # シグナルハンドラの設定
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(server, loop)))
        
        # サーバーの起動
        logger.info("サーバーを起動しています...")
        await server.start()
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)


async def shutdown(server: OpcUaServer, loop: asyncio.AbstractEventLoop):
    """
    シャットダウン処理

    Args:
        server: OPC-UAサーバー
        loop: イベントループ
    """
    logger = logging.getLogger(__name__)
    logger.info("シャットダウンしています...")
    
    # サーバーの停止
    server.stop()
    
    # タスクのキャンセル
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # イベントループの停止
    loop.stop()


if __name__ == "__main__":
    asyncio.run(main())
