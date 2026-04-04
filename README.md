# volley

SeAT 5.x 向けの EVE Online ダメージ計算プラグインです。  
Pyfa ベースの damage application 計算式と SeAT の ESI スキル情報を組み合わせて、実戦に近い DPS を算出します。  
UI では EFT を貼り付け、Chart.js で DPS vs 距離グラフを表示できます。  
構成は `seat-plugin`（Laravel）+ `volley-engine`（FastAPI）です。

## 構成図

```text
SeAT (seat-docker) ──内部Docker network──▶ volley-engine (FastAPI)
  └ ESI キャラスキル                          └ EVE SDE (Fuzzwork SQLite)
  └ EFT ペースト                              └ Dogma エンジン
  └ Chart.js グラフ                           └ Damage application 計算
```

## 前提環境（実績ベース）

- SeAT 5.x（Docker Compose）
- Compose プロジェクト名: `seat-docker`
- SeAT 配置先: `/opt/seat-docker/`
- volley クローン先: `/opt/seat-docker/volley/`
- Web コンテナ: `seat-docker-front-1`
- Worker コンテナ: `seat-docker-worker-1`
- Scheduler コンテナ: `seat-docker-scheduler-1`
- SeAT 内部ネットワーク: `seat-docker_seat-internal`

必要ツール:

- Docker 20.10+
- Docker Compose v2
- Git

## インストール手順（実際に動作した手順）

### 1. リポジトリのクローン

```bash
cd /opt/seat-docker
git clone https://github.com/syaripin-i8i/volley.git
```

### 2. volley-engine の起動

```bash
cd /opt/seat-docker/volley/engine
docker compose up -d --build

# SDE ダウンロード確認（初回は数分）
docker compose logs -f volley-engine
```

### 3. 内部ネットワーク経由で疎通確認

Traefik 環境ではホストの `localhost` 経由での確認は使いません。  
必ずコンテナ内部から確認してください。

```bash
docker exec seat-docker-front-1 curl http://volley-engine:8000/health
# -> {"status":"ok"}
```

### 4. SeAT `.env` を編集

SeAT 5.x では `override.json` 方式は使わず、`SEAT_PLUGINS` 方式で導入します。  
`/opt/seat-docker/.env` をエディタで開き、以下を追記・編集します。

```env
# 既存の SEAT_PLUGINS 行に seat-volley を追加
SEAT_PLUGINS=cryptatech/seat-fitting,syaripin-i8i/seat-srp,syaripin-i8i/seat-volley

# 新規追加
VOLLEY_ENGINE_URL=http://volley-engine:8000
```

補足:

- `SEAT_PLUGINS` はスタック起動時に自動 `composer require` されます
- `syaripin-i8i/seat-volley` は Packagist 公開パッケージです

### 5. SeAT スタック再起動（3ファイル指定）

SeAT スタック操作は必ず以下3ファイルを指定します。

```bash
cd /opt/seat-docker

# 停止
docker compose -f docker-compose.yml -f docker-compose.mariadb.yml -f docker-compose.traefik.yml down

# 起動
docker compose -f docker-compose.yml -f docker-compose.mariadb.yml -f docker-compose.traefik.yml up -d
```

`php artisan cache:clear` はこの手順では不要です。

## 使い方

1. SeAT にログイン
2. サイドバーの `Damage Calc` を開く
3. EFT フィットを貼り付ける
4. ターゲット条件（プリセット or 手入力）を指定
5. `Calculate` を押してグラフと DPS サマリーを確認

## SDE 更新（EVE パッチ後）

```bash
cd /opt/seat-docker/volley/engine
docker compose exec volley-engine python scripts/download_sde.py
docker compose restart volley-engine
```

## トラブルシューティング

| 症状 | 確認箇所 |
|------|----------|
| `Failed to reach volley-engine` | `docker compose ps` で `volley-engine` が `Up` か確認。`seat-docker-front-1` から `curl http://volley-engine:8000/health` を実行 |
| グラフが表示されない | ブラウザ DevTools の Console/Network と `/volley/calculate` レスポンスを確認 |
| SDE の準備が進まない | `docker compose logs -f volley-engine` で SDE ダウンロードの進行・エラーを確認 |
| メニューが表示されない | `.env` の `SEAT_PLUGINS` に `syaripin-i8i/seat-volley` があるか確認し、3ファイル指定でスタック再起動 |

## アンインストール

```bash
cd /opt/seat-docker

# .env の SEAT_PLUGINS から syaripin-i8i/seat-volley を削除
# VOLLEY_ENGINE_URL も不要なら削除

# volley-engine 停止
cd /opt/seat-docker/volley/engine
docker compose down -v

# SeAT 再起動（3ファイル指定）
cd /opt/seat-docker
docker compose -f docker-compose.yml -f docker-compose.mariadb.yml -f docker-compose.traefik.yml down
docker compose -f docker-compose.yml -f docker-compose.mariadb.yml -f docker-compose.traefik.yml up -d
```

## 注意事項

- `localhost:8721` は Traefik 環境では確認手段として使わず、`docker exec seat-docker-front-1 curl ...` で確認する
- SeAT 5.x では `override.json` 方式ではなく `SEAT_PLUGINS` が正規手順
- `.env` 編集は `sed` ではなくエディタで直接編集する
- SDE は初回起動時に自動ダウンロードされるため、`docker compose logs -f volley-engine` で完了確認後に疎通テストする
- SeAT スタック操作は常に `-f docker-compose.yml -f docker-compose.mariadb.yml -f docker-compose.traefik.yml` の3ファイル指定で行う
