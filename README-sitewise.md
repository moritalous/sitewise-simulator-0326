# AWS IoT SiteWise 設定ガイド

このドキュメントでは、OPC-UAサーバーシミュレーターからAWS IoT SiteWiseにデータを送信するための設定方法を説明します。

## 概要

以下の3つのCloudFormationテンプレートを使用して、AWS IoT SiteWiseの環境を構築します：

1. `sitewise-assets.yaml` - アセットモデルとアセットを作成
2. `sitewise-gateway.yaml` - SiteWise Gatewayとデータソース設定
3. `sitewise-property-mappings.yaml` - プロパティマッピング設定

## デプロイ手順

### 1. アセットモデルとアセットの作成

```bash
aws cloudformation create-stack \
  --stack-name factory-sitewise-assets \
  --template-body file://sitewise-assets.yaml \
  --capabilities CAPABILITY_IAM
```

スタックが完了したら、出力からアセットIDを取得します：

```bash
aws cloudformation describe-stacks \
  --stack-name factory-sitewise-assets \
  --query "Stacks[0].Outputs"
```

### 2. SiteWise Gatewayの設定

**注意**: SiteWise Gatewayを使用するには、AWS Greengrassが必要です。Greengrassグループを事前に作成し、そのARNを`sitewise-gateway.yaml`の`GroupArn`パラメータに設定してください。

```bash
aws cloudformation create-stack \
  --stack-name factory-sitewise-gateway \
  --template-body file://sitewise-gateway.yaml \
  --parameters ParameterKey=OpcUaEndpoint,ParameterValue=opc.tcp://YOUR_SERVER_IP:4840
```

### 3. プロパティマッピングの設定

前のステップで取得したアセットIDを使用して、プロパティマッピングを設定します。

**注意**: `sitewise-property-mappings.yaml`の`REPLACE_WITH_PROPERTY_ID_FOR_XXX`を実際のプロパティIDに置き換える必要があります。プロパティIDは以下のコマンドで取得できます：

```bash
aws iotsitewise describe-asset \
  --asset-id YOUR_ASSET_ID
```

プロパティIDを更新した後、以下のコマンドでスタックをデプロイします：

```bash
aws cloudformation create-stack \
  --stack-name factory-sitewise-mappings \
  --template-body file://sitewise-property-mappings.yaml \
  --parameters \
    ParameterKey=ConveyorBeltAssetId,ParameterValue=YOUR_CONVEYOR_BELT_ASSET_ID \
    ParameterKey=PressMachineAssetId,ParameterValue=YOUR_PRESS_MACHINE_ASSET_ID \
    ParameterKey=WeldingRobotAssetId,ParameterValue=YOUR_WELDING_ROBOT_ASSET_ID \
    ParameterKey=CNCMachineAssetId,ParameterValue=YOUR_CNC_MACHINE_ASSET_ID \
    ParameterKey=PaintingBoothAssetId,ParameterValue=YOUR_PAINTING_BOOTH_ASSET_ID \
    ParameterKey=EnvironmentSensorAssetId,ParameterValue=YOUR_ENVIRONMENT_SENSOR_ASSET_ID \
    ParameterKey=PowerMonitoringAssetId,ParameterValue=YOUR_POWER_MONITORING_ASSET_ID
```

## データフロー

1. OPC-UAサーバーシミュレーターがセンサーデータを生成
2. SiteWise Gatewayが5秒間隔でデータを収集
3. データがAWS IoT SiteWiseに送信され、アセットプロパティに保存
4. SiteWiseモニターでダッシュボードを作成して可視化可能

## SiteWiseモニターの設定

1. AWS IoT SiteWiseコンソールで「モニター」を選択
2. 新しいポータルを作成
3. アセットモデルをポータルに関連付け
4. ダッシュボードを作成して、各センサーのデータを可視化

## トラブルシューティング

- **データが表示されない場合**: SiteWise Gatewayのログを確認し、接続とデータ収集が正常に行われているか確認してください。
- **プロパティマッピングエラー**: プロパティIDが正しいことを確認してください。
- **OPC-UAサーバー接続エラー**: サーバーのIPアドレスとポートが正しく設定されているか確認してください。

## 参考リンク

- [AWS IoT SiteWise ドキュメント](https://docs.aws.amazon.com/iot-sitewise/)
- [AWS IoT SiteWise Gateway ドキュメント](https://docs.aws.amazon.com/iot-sitewise/latest/userguide/gateways.html)
- [AWS IoT SiteWise モニター ドキュメント](https://docs.aws.amazon.com/iot-sitewise/latest/appguide/)
