import asyncio
import logging
from asyncua import Server, ua

async def main():
    # ロギングの設定
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    try:
        # サーバーの作成
        server = Server()
        await server.init()
        server.set_endpoint("opc.tcp://0.0.0.0:4840")
        server.set_server_name("Debug Server")
        
        # 名前空間の登録
        uri = "urn:debug:server"
        idx = await server.register_namespace(uri)
        
        # オブジェクトの作成
        objects = server.nodes.objects
        
        # テストオブジェクトの作成
        test_obj = await objects.add_object(idx, "TestObject")
        logger.info(f"テストオブジェクトを作成しました: {test_obj}")
        
        # テスト変数の作成
        test_var = await test_obj.add_variable(idx, "TestVariable", 0.0)
        logger.info(f"テスト変数を作成しました: {test_var}")
        
        await test_var.set_writable()
        logger.info("変数を書き込み可能に設定しました")
        
        async with server:
            logger.info("サーバーを起動しました")
            
            # サーバーを実行し続ける
            counter = 0
            while counter < 5:  # 5回だけ実行
                await asyncio.sleep(1)
                counter += 1
                # テスト変数の値を更新
                current_value = await test_var.read_value()
                logger.info(f"現在の値: {current_value}")
                await test_var.write_value(current_value + 1.0)
                logger.info(f"変数の値を更新しました: {await test_var.read_value()}")
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
