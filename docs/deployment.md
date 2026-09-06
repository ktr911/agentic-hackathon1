# Google Cloud デプロイ手順

Web クライアントを Cloud Run、ADK エージェントを Agent Runtime（旧称 Vertex AI
Agent Engine）へデプロイします。既定のプロジェクトは `agentic-ai-hackathon-test1`、リージョンは
東京の `asia-northeast1` です。

## 構成

```text
Browser
  └─ HTTPS → Cloud Run: fieldnote-client
                ├─ HTML / CSS / JavaScript
                ├─ Agent Runtime API への認証付き BFF
                └─ GCS artifact 読み出し
                         │
                         ├─ Agent Runtime: fieldnote-agent
                         └─ GCS: 生成画像 artifact
```

Cloud Run は一般公開されます。Google Cloud の認証トークンやサービスアカウント鍵は
ブラウザへ渡さず、Cloud Run のサービスアカウントで Agent Runtime を呼び出します。

## 前提条件

- `gcloud` と `uv` がインストール済み
- `agentic-ai-hackathon-test1` で課金が有効
- 実行ユーザーに API 有効化、IAM、サービスアカウント、Cloud Run、Cloud Build、
  Agent Runtime、Cloud Storage を設定できる権限がある
- Gemini モデル `gemini-3.7-flash` と画像モデル `gemini-3.1-flash-image` を対象
  プロジェクトから利用できる

ローカル端末を認証します。

```bash
gcloud auth login
gcloud auth application-default login
```

## デプロイ

リポジトリのルートで実行します。

```bash
./scripts/deploy.sh
```

スクリプトは以下を冪等に実行します。

1. 必要な Google Cloud API の有効化
2. Agent Runtime / Cloud Run 用サービスアカウントと最小限の実行権限の設定
3. 生成画像を保存する非公開 GCS バケットの作成
4. ADK CLI による Agent Runtime の作成または更新
5. Cloud Run のソースデプロイ
6. `/api/healthz` と実際の Agent Runtime 呼び出しによる E2E 疎通確認

初回デプロイで得た Agent Runtime リソース名は
`.deploy/agent-engine-resource.txt` に保存され、2回目以降は同じリソースを更新します。

設定を変える場合は環境変数で上書きできます。

```bash
REGION=asia-northeast1 \
WEB_SERVICE=fieldnote-client \
ARTIFACT_BUCKET=agentic-ai-hackathon-test1-fieldnote-artifacts \
./scripts/deploy.sh
```

画像生成を含む E2E 確認を省略してデプロイだけ行う場合は `SMOKE_TEST=false` を指定します。

## 確認

Cloud Run URL はスクリプトの最後に表示されます。設定だけを確認する場合は次を実行します。

```bash
gcloud run services describe fieldnote-client \
  --project=agentic-ai-hackathon-test1 \
  --region=asia-northeast1 \
  --format='value(status.url)'

curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  'https://asia-northeast1-aiplatform.googleapis.com/v1/projects/agentic-ai-hackathon-test1/locations/asia-northeast1/reasoningEngines'
```

ログは Cloud Logging のほか、デプロイ時の Agent Runtime 出力が
`.deploy/agent-engine-deploy.log` に残ります。

## ローカル確認

Cloud Run 用サーバーは、デプロイ済み Agent Runtime のリソース名を指定して起動できます。

```bash
export GOOGLE_CLOUD_PROJECT=agentic-ai-hackathon-test1
export GOOGLE_CLOUD_LOCATION=asia-northeast1
export AGENT_ENGINE_RESOURCE='projects/PROJECT_NUMBER/locations/asia-northeast1/reasoningEngines/RESOURCE_ID'
export ARTIFACT_BUCKET=agentic-ai-hackathon-test1-fieldnote-artifacts

uv run --with-requirements src/web/requirements.txt \
  uvicorn server:app --app-dir src/web --host 0.0.0.0 --port 8080
```

## 注意点と削除

- Cloud Run はハッカソンでブラウザから利用できるよう未認証アクセスを許可しています。
  URL が広まると第三者がモデル利用料金を発生させられるため、公開期間を限定してください。
- Agent Runtime と Cloud Run は最大 3 インスタンスに制限していますが、モデル呼び出し料金は
  別途発生します。
- Agent Runtime は東京、Gemini のモデル呼び出しはモデル提供地域に合わせて `global`
  endpoint を使用します。
- ハッカソン終了後は次のコマンドで、このスクリプトが作成した専用リソースを削除できます。

```bash
CONFIRM_DESTROY=agentic-ai-hackathon-test1 ./scripts/destroy.sh
```

削除対象は `fieldnote-client`、保存済み Agent Runtime リソース、生成画像バケット、
`fieldnote-agent-runtime` / `fieldnote-web` サービスアカウントです。プロジェクトで共有される
API と Cloud Run ソース build 用 Artifact Registry は残します。
