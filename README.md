# volley

SeAT 5.x 向けの EVE Online ダメージ計算プラグインです。  
Pyfa の damage application 計算式をベースに、SeAT が保持する ESI スキル情報を使って実運用に近い DPS を計算します。  
フロントエンドでは EFT を貼り付けて、Chart.js で DPS vs 距離グラフを表示できます。  
`seat-plugin`（Laravel）と `volley-engine`（FastAPI）の2コンポーネント構成です。

## 構成図

```text
SeAT (seat-docker) ──内部Docker network──▶ volley-engine (FastAPI)
  └ ESI キャラスキル                          └ EVE SDE (Fuzzwork SQLite)
  └ EFT ペースト                              └ Dogma エンジン
  └ Chart.js グラフ                           └ Damage application 計算
```

## 必要要件

- Docker 20.10+
- Docker Compose v2
- Git
- SeAT 5.x が `seat-docker` プロジェクトで稼働中
- SeAT 内部ネットワーク: `seat-docker_seat-internal`
- SeAT 外部ネットワーク: `seat-docker_seat-gateway`（volley-engine は接続しません）

## インストール手順

### 1. リポジトリのクローン

```bash
# SeAT サーバー上で実行（seat-docker の docker-compose.yml と同じディレクトリ推奨）
git clone https://github.com/syaripin-i8i/volley.git
cd volley
```

### 2. volley-engine の起動

```bash
cd engine
docker compose up -d --build

# 起動確認
curl http://localhost:8721/health
# -> {"status":"ok"}

# SDE ダウンロード確認（初回は数分）
docker compose logs -f volley-engine
```

### 3. SeAT 側からの疎通確認

```bash
# seat-web コンテナから疎通テスト
docker exec -it seat-docker-seat-web-1 curl http://volley-engine:8000/health
# -> {"status":"ok"}
```

`engine/docker-compose.yml` では `seat-docker_seat-internal` に接続する設定済みです。  
基本的に SeAT 本体の `docker-compose.yml` 側に追加編集は不要です。

### 4. SeAT プラグイン配置

```bash
# 例: seat-docker の packages 配下へコピー
cp -r seat-plugin /opt/seat-docker/packages/volley/seat-volley

# またはホーム配下の運用例
cp -r seat-plugin ~/seat-docker/packages/volley/seat-volley
```

### 5. SeAT の override.json に追記

`/opt/seat-docker/override.json`（環境に応じてパス調整）に次を追記:

```json
{
  "autoload": {
    "Volley\\SeatVolley\\": "packages/volley/seat-volley/src/"
  },
  "providers": [
    "Volley\\SeatVolley\\VolleyServiceProvider"
  ]
}
```

### 6. SeAT の .env に追記

```bash
echo "VOLLEY_ENGINE_URL=http://volley-engine:8000" >> /opt/seat-docker/.env
```

### 7. キャッシュクリアと再起動

```bash
cd /opt/seat-docker
docker compose exec seat-web php artisan config:clear
docker compose exec seat-web php artisan cache:clear
docker compose restart seat-web
```

## 使い方

1. SeAT にログインしてキャラクターページを開く  
2. サイドバーの `Damage Calc` を開く  
3. EFT フィットを貼り付ける  
4. ターゲット条件（プリセットまたは手動）を設定  
5. `Calculate` でグラフと DPS サマリーを表示

## SDE の更新（EVE パッチ後）

```bash
cd volley/engine
docker compose exec volley-engine python scripts/download_sde.py
docker compose restart volley-engine
```

またはボリュームごと再生成:

```bash
docker compose down -v
docker compose up -d --build
```

## トラブルシューティング

| 症状 | 確認箇所 |
|------|----------|
| `Failed to reach volley-engine` | `docker compose ps` で `volley-engine` が `Up` か、`seat-docker_seat-internal` 接続を確認 |
| グラフが表示されない | ブラウザ DevTools の Console / Network と `/volley/calculate` のレスポンスを確認 |
| `SDE not found` | `docker compose logs volley-engine` で SDE ダウンロード失敗を確認。必要なら `download_sde.py` を手動実行 |
| SeAT サイドバーに出ない | `override.json` の設定と `php artisan cache:clear` の実行を確認 |

## アンインストール

```bash
# プラグイン削除
rm -rf /opt/seat-docker/packages/volley

# volley-engine 停止
cd volley/engine
docker compose down -v

# override.json から volley エントリ削除後
docker compose exec seat-web php artisan cache:clear
docker compose restart seat-web
```

## 注意事項

- `engine/data/sde.db` は `.gitignore` 除外済みです。コンテナ起動時に自動ダウンロードされます  
- `volley-engine` は内部 API 用です。Traefik 用の外部ネットワークには接続しません  
- EFT テキストは `volley-engine` に送信されますが、外部サービス連携なしでローカル処理します
