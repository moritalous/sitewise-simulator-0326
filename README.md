# OPC-UAサーバーシミュレーター

製造工場を模したOPC-UAサーバーシミュレーターです。AWS IoT SiteWiseおよびSiteWise Edgeのテスト環境用に開発されました。

## 機能

- Python 3.12環境で動作するOPC-UAサーバー
- 5秒間隔でクライアントからデータ取得可能
- 各センサー値は毎秒少しずつ変化する動的なデータ生成
- 製造工場を想定した複数のセンサー/機器をシミュレート
- 1時間に1回程度（ランダムタイミング）で機器故障をシミュレート

## 必要条件

- Python 3.12
- pip

## インストール

1. リポジトリをクローン

```bash
git clone <repository-url>
cd opcua-simulator
```

2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## 使用方法

### サーバーの起動

```bash
python src/main.py
```

デフォルトでは、サーバーは `opc.tcp://0.0.0.0:4840` でリッスンします。

### 設定のカスタマイズ

`config.yaml` ファイルを編集することで、シミュレーターの動作をカスタマイズできます。

## シミュレートされる機器/センサー

- 生産ライン1: コンベアベルト、プレス機、溶接ロボット
- 生産ライン2: CNC工作機械、塗装ブース
- 環境モニタリング: 工場環境センサー、電力モニタリング

## テスト

テストを実行するには:

```bash
pytest
```

## ライセンス

[MIT](LICENSE)
