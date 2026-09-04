# デプロイメモ

## GCPプロジェクト
- プロジェクトID: `agentic-ai-hackathon-test1`
  - 過去に`test1`という別名で試して権限エラー（AUTH_PERMISSION_DENIED）になった。正しいIDはこちら。
  - **削除禁止**（再利用予定のため）。同じプロジェクトIDは一度削除すると二度と使えない。
- デプロイリージョン: `asia-northeast1`（Cloud Runサービスのリージョン。Vertex AIのモデルロケーションとは別物）

## デプロイコマンド
```
gcloud run deploy agentic-hackathon --source . --region asia-northeast1 --project agentic-ai-hackathon-test1 --allow-unauthenticated
```

## Geminiモデルについて
- `gemini-1.5-*` / `gemini-2.0-*` 系はVertex AIから404（廃止済み、2026年時点）
- 動作確認できたのは `gemini-2.5-flash` / `gemini-2.5-pro` / `gemini-2.5-flash-lite`
- `main.py`の`GEMINI_MODEL`デフォルトは`gemini-2.5-flash`に修正済み

## エンドポイント
- `/` : 固定レスポンスのみ。LLMは呼ばない。
- `/chat?q=...` : Geminiを呼び出す。動作確認はここで行うこと。

## ローカル環境の注意
- `.venv`はPython 3.9でfastapi等が未インストール（IDEの警告はこのため。実害なし）
- gcloud CLIがPython 3.9を掴んでエラーになる場合は下記を先に実行:
  ```
  export CLOUDSDK_PYTHON="C:\Users\81902\AppData\Local\Programs\Python\Python313\python.exe"
  ```

## コスト管理
- 使わない間はCloud Runサービスと Artifact Registry イメージを削除してコストを抑える:
  ```
  gcloud run services delete agentic-hackathon --region asia-northeast1 --project agentic-ai-hackathon-test1
  gcloud artifacts repositories delete cloud-run-source-deploy --location asia-northeast1 --project agentic-ai-hackathon-test1
  ```
- プロジェクト自体（`agentic-ai-hackathon-test1`）は削除しないこと。
- 2026-09-01時点でCloud RunサービスとArtifact Registryイメージは削除済み。プロジェクトと課金アカウントのリンクは維持している。
