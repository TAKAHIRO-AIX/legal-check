# 引き継ぎメモ

最終更新：2026-05-07

## システム概要
契約書（スキャンPDF）をアップロードしてAIがリーガルチェックし、Wordレポートを出力するWebアプリ。

## 確定構成

| 項目 | 内容 |
|---|---|
| 入力 | スキャンPDF（iPhoneカメラ→スキャンアプリでPDF化） |
| コンテキスト | 契約書の背景・経緯 ＋ 利用者の注目点 |
| OCR | AWS Textract |
| AI解析 | Claude Opus 4.7（Amazon Bedrock、us-east-1） |
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

## 今日完了したこと
- [x] システム設計・構成確定
- [x] コード実装（main.py, index.html, requirements.txt, README.md）
- [x] GitHubアカウント作成（TAKAHIRO-AIX）
- [x] GitHubリポジトリ作成・push完了

## 明日やること（Mac側）
1. MacのターミナルでGitHubからclone
   ```bash
   cd ~/Documents
   git clone https://github.com/TAKAHIRO-AIX/legal-check.git
   cd legal-check
   ```
2. Python仮想環境セットアップ＆パッケージインストール
3. S3バケット作成（名前未定、例：`takahiro-legal-check-2026`）
4. BedrockコンソールでClaude Opus 4.7のモデルアクセス申請
5. 環境変数設定＆サーバー起動・動作確認

## 環境変数（起動時に必要）
```bash
export AWS_REGION=us-east-1
export TEXTRACT_S3_BUCKET=（S3バケット名）
```

## ⭐ 明日キロちゃんへの声がけ（これをコピペ）

```
GitHubのこのファイルを読んで続きをお願い：https://github.com/TAKAHIRO-AIX/legal-check/blob/main/PROGRESS.md
```

---

## 注意事項
- GitHubのPersonal Access Tokenは使用済み。必要なら https://github.com/settings/tokens で再発行
- Claude Opus 4（旧）は2026年5月31日でサポート終了のため、Claude Opus 4.7を採用
