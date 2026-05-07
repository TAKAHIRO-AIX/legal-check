# 契約書リーガルチェックシステム

スキャンPDFをアップロードするだけで、AIが契約書のリスクを洗い出しWordレポートを生成します。

## 構成

```
[ブラウザ]
  ↓ PDFアップロード + コンテキスト入力
[FastAPI (Python)]
  ↓
[AWS Textract] → OCRでテキスト抽出
  ↓
[Amazon Bedrock / Claude Opus 4.7] → リーガルチェック
  ↓
[python-docx] → Wordレポート生成
  ↓
[ブラウザ] → 結果表示 → Wordダウンロード
```

## 事前準備

### 1. AWS認証情報の設定

```bash
aws configure
```

- `AWS Access Key ID` と `AWS Secret Access Key` を入力
- リージョン: `us-east-1` 推奨

### 2. S3バケットの作成（Textract用）

```bash
aws s3 mb s3://your-legal-check-bucket --region us-east-1
```

### 3. Bedrockモデルアクセスの申請

1. [AWS Console](https://console.aws.amazon.com/bedrock/) を開く
2. 左メニュー「Model access」→「Manage model access」
3. `Claude Opus 4.7` にチェックを入れて申請（通常即時承認）

### 4. 必要なIAM権限

実行ユーザーに以下のポリシーが必要です：

- `AmazonTextractFullAccess`
- `AmazonS3FullAccess`（または対象バケットのみ）
- `AmazonBedrockFullAccess`

## ローカル起動手順

```bash
# 1. プロジェクトディレクトリへ移動
cd legal-check

# 2. 仮想環境の作成・有効化
python3 -m venv venv
source venv/bin/activate   # Windowsの場合: venv\Scripts\activate

# 3. 依存パッケージのインストール
pip install -r requirements.txt

# 4. 環境変数の設定
export AWS_REGION=us-east-1
export TEXTRACT_S3_BUCKET=your-legal-check-bucket

# 5. サーバー起動
uvicorn main:app --reload --port 8000
```

ブラウザで http://localhost:8000 を開いてください。

## 使い方

1. **STEP 1**: スキャンPDFをアップロード（ドラッグ＆ドロップ可）
2. **STEP 2**: 契約書の背景・経緯と、あなたの注目点を入力
3. **STEP 3**: 「リーガルチェックを開始する」をクリック
4. 30〜60秒後にWordレポートがダウンロードできます

## コスト目安（年数回・30〜40ページ/回）

| サービス | 1回あたり | 年間（5回） |
|---|---|---|
| AWS Textract | 約6〜9円 | 約30〜45円 |
| Amazon Bedrock (Claude Opus 4.7) | 約100〜300円 | 約500〜1,500円 |
| **合計** | **約110〜310円** | **約530〜1,545円** |
