# 引き継ぎメモ

最終更新：2026-05-09

## システム概要
契約書（スキャンPDF）をアップロードしてAIがリーガルチェックし、Wordレポートを出力するWebアプリ。

## 確定構成

| 項目 | 内容 |
|---|---|
| 入力 | スキャンPDF（iPhoneカメラ→スキャンアプリでPDF化） |
| コンテキスト | 契約書の背景・経緯 ＋ 利用者の注目点 |
| OCR | AWS Textract |
| AI解析 | Claude Opus 4.6（Amazon Bedrock、us-east-1） |
| フレームワーク | FastAPI（Python） |
| UI | Webアプリ（ブラウザ操作） |
| 出力 | Wordファイル（コメント・リスク評価のみ、先方に編集可能な形で納品） |
| レポート形式 | 条項番号・ページ番号付きコメントリスト |
| デプロイ | ローカルMac |

## 実装済みファイル

- `main.py` — FastAPIバックエンド（Textract・Bedrock・Word生成）
- `templates/index.html` — フロントエンド（ドラッグ&ドロップ、コンテキスト入力、ダウンロード）
- `requirements.txt` — Python依存パッケージ
- `README.md` — 起動手順・AWS設定・コスト目安

## GitHub
- リポジトリ：https://github.com/TAKAHIRO-AIX/legal-check
- ブランチ：main

## 完了済みタスク
- [x] システム設計・構成確定
- [x] コード実装（main.py, index.html, requirements.txt, README.md）
- [x] GitHubアカウント作成（TAKAHIRO-AIX）
- [x] GitHubリポジトリ作成・push完了
- [x] S3バケット作成（`takahiro-legal-check-2026`、us-east-1）
- [x] Bedrockモデルアクセス確認（Opus 4.7は利用不可 → Opus 4.6に変更）
- [x] uvicornでの起動確認OK

## AWS環境
- S3バケット：`takahiro-legal-check-2026`（us-east-1）
- Bedrockモデル：`us.anthropic.claude-opus-4-6-v1`（Claude Opus 4.6）
  - ※ Claude Opus 4.7はこのAWSアカウントでは利用不可（AccessDenied）
  - ※ Claude Opus 4.6はThrottlingExceptionが返る場合あり（日次トークン上限）→ 翌日に再試行

## Macでの起動手順
```bash
cd ~/Documents
git clone https://github.com/TAKAHIRO-AIX/legal-check.git
cd legal-check
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export AWS_REGION=us-east-1
export TEXTRACT_S3_BUCKET=takahiro-legal-check-2026
uvicorn main:app --host 0.0.0.0 --port 8000
```
ブラウザで http://localhost:8000 を開く。

## 環境変数（起動時に必要）
```bash
export AWS_REGION=us-east-1
export TEXTRACT_S3_BUCKET=takahiro-legal-check-2026
```

## 注意事項
- GitHubのPersonal Access Tokenは使用済み。必要なら https://github.com/settings/tokens で再発行
- Claude Opus 4.7はこのAWSアカウントでは利用不可。Opus 4.6を使用
- Opus 4.6で「Too many tokens per day」エラーが出た場合は翌日に再試行

## ⭐ 次回キロちゃんへの声がけ（これをコピペ）

```
GitHubのこのファイルを読んで続きをお願い：https://github.com/TAKAHIRO-AIX/legal-check/blob/main/PROGRESS.md
```
