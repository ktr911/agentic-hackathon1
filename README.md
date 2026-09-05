# Agentic Hackathon

地質情報と観光情報を組み合わせ、地域の解説、地図ピン、補助画像を返す
Google ADK v2 ベースのエージェントアプリです。

## エージェント構成

```text
src/agent/
├── agent.py          # ADKの読み込み口
├── config.py         # 共通のモデル設定
├── root/             # 全体をまとめるオーケストレーター
│   ├── agent.py
│   └── tools.py      # 地図データ統合・画像生成
├── geology/          # 地質調査エージェント
│   ├── agent.py
│   └── tools.py      # 地質調査ツール
└── tour/             # 観光・ルート案内エージェント
    ├── agent.py
    └── tools.py      # 行き先選定・ルート策定ツール
```

`root_agent` が地質・観光の2エージェントを呼び出し、地質学的知見と地域の見どころ・周遊ルートを関連付けて
一つの回答にまとめます。調査結果や地形に合わせた地図ピン、補助画像も動的に生成されます。

## Webクライアント

`src/web` にモバイル向けクライアントがあります。送信時刻と、許可された場合は
現在位置をエージェントへ渡し、調査の進捗、地図ピン、生成画像を表示します。

## ローカル起動

Python 3.12、`uv`、ADCを用意し、Vertex AIの環境変数を設定して起動します。

```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=global

uvx --from google-adk==2.8.0 adk web --host 0.0.0.0 --port 8080 src
python -m http.server 5173 --directory src/web
```

- モバイルWeb: <http://localhost:5173>
- ADK Web UI: <http://localhost:8080/dev-ui/>

## Google Cloud へデプロイ

Web クライアントは Cloud Run、ADK は Agent Runtime（旧 Agent Engine）へデプロイします。
認証・IAM・GCS artifact・Cloud Run の設定を含む再実行可能なスクリプトがあります。

```bash
gcloud auth login
gcloud auth application-default login
./scripts/deploy.sh
```

既定の Google Cloud プロジェクトは `zenn-hack5-i-icc`、リージョンは
`asia-northeast1` です。詳しくは [Google Cloud デプロイ手順](docs/deployment.md) を参照してください。

ハッカソン終了後の専用リソース削除:

```bash
CONFIRM_DESTROY=zenn-hack5-i-icc ./scripts/destroy.sh
```
