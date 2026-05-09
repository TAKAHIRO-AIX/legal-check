import io
import json
import os
import tempfile
import time

import boto3
from docx import Document
from docx.shared import Pt, RGBColor
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI(title="契約書リーガルチェックシステム")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

textract = boto3.client("textract", region_name=AWS_REGION)
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """TextractでスキャンPDFからテキスト抽出（非同期ジョブ）"""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    bucket = os.getenv("TEXTRACT_S3_BUCKET")

    if not bucket:
        raise HTTPException(status_code=500, detail="環境変数 TEXTRACT_S3_BUCKET が未設定です")

    key = f"legal-check-tmp/{int(time.time())}.pdf"
    s3.put_object(Bucket=bucket, Key=key, Body=pdf_bytes)

    try:
        response = textract.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
        )
        job_id = response["JobId"]

        # ジョブ完了待ち
        while True:
            result = textract.get_document_text_detection(JobId=job_id)
            status = result["JobStatus"]
            if status == "SUCCEEDED":
                break
            if status == "FAILED":
                raise HTTPException(status_code=500, detail="Textractのテキスト抽出に失敗しました")
            time.sleep(3)

        # 全ページのテキストを結合
        pages: dict[int, list[str]] = {}
        next_token = None
        while True:
            kwargs = {"JobId": job_id}
            if next_token:
                kwargs["NextToken"] = next_token
            result = textract.get_document_text_detection(**kwargs)
            for block in result.get("Blocks", []):
                if block["BlockType"] == "LINE":
                    page = block.get("Page", 1)
                    pages.setdefault(page, []).append(block["Text"])
            next_token = result.get("NextToken")
            if not next_token:
                break

        lines = []
        for page_num in sorted(pages.keys()):
            lines.append(f"\n--- ページ {page_num} ---")
            lines.extend(pages[page_num])
        return "\n".join(lines)
    finally:
        s3.delete_object(Bucket=bucket, Key=key)


def legal_check_with_bedrock(contract_text: str, background: str, focus: str) -> list[dict]:
    """BedrockのClaude Opus 4.7でリーガルチェック"""
    prompt = f"""あなたは日本法に精通した法律の専門家です。以下の契約書をリーガルチェックしてください。

## 契約書の背景・経緯・概要
{background}

## 利用者の注目点・着眼点・希望
{focus}

## 契約書本文
{contract_text}

## 指示
上記の契約書を精査し、以下の観点でリスクや問題点を洗い出してください：
- 利用者に不利な条項
- 必須条項の欠落（秘密保持・準拠法・管轄裁判所・損害賠償上限など）
- 曖昧・不明確な表現
- 利用者の注目点に関連する事項

結果は必ず以下のJSON配列形式のみで返してください（説明文不要）：
[
  {{
    "page": ページ番号(int),
    "clause": "条項番号または条項名",
    "risk_level": "高/中/低",
    "issue": "問題点の説明",
    "recommendation": "修正・対応の提案"
  }}
]"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    })

    response = bedrock.invoke_model(modelId=BEDROCK_MODEL_ID, body=body)
    result_text = json.loads(response["body"].read())["content"][0]["text"]

    # JSON部分を抽出
    start = result_text.find("[")
    end = result_text.rfind("]") + 1
    return json.loads(result_text[start:end])


def generate_word_report(issues: list[dict], background: str, focus: str) -> str:
    """python-docxでWordレポート生成、一時ファイルパスを返す"""
    doc = Document()

    # タイトル
    title = doc.add_heading("契約書リーガルチェックレポート", level=1)
    title.runs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

    # コンテキスト
    doc.add_heading("■ チェック背景・コンテキスト", level=2)
    doc.add_paragraph(f"【背景・経緯】\n{background}")
    doc.add_paragraph(f"【注目点・着眼点】\n{focus}")

    # サマリー
    doc.add_heading("■ リスクサマリー", level=2)
    high = sum(1 for i in issues if i.get("risk_level") == "高")
    mid = sum(1 for i in issues if i.get("risk_level") == "中")
    low = sum(1 for i in issues if i.get("risk_level") == "低")
    doc.add_paragraph(f"高リスク: {high}件　中リスク: {mid}件　低リスク: {low}件　合計: {len(issues)}件")

    # 詳細
    doc.add_heading("■ 指摘事項詳細", level=2)
    risk_colors = {"高": RGBColor(0xC0, 0x00, 0x00), "中": RGBColor(0xFF, 0x7F, 0x00), "低": RGBColor(0x00, 0x70, 0xC0)}

    for i, issue in enumerate(issues, 1):
        level = issue.get("risk_level", "低")
        p = doc.add_paragraph()
        run = p.add_run(f"【{i}】{issue.get('clause', '')}　（ページ {issue.get('page', '-')}）　リスク: {level}")
        run.bold = True
        run.font.color.rgb = risk_colors.get(level, RGBColor(0, 0, 0))

        doc.add_paragraph(f"問題点: {issue.get('issue', '')}")
        rec = doc.add_paragraph(f"推奨対応: {issue.get('recommendation', '')}")
        rec.runs[0].font.color.rgb = RGBColor(0x00, 0x60, 0x00)
        doc.add_paragraph("")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    return tmp.name


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/check")
async def check_contract(
    pdf: UploadFile = File(...),
    background: str = Form(...),
    focus: str = Form(...),
):
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルのみ対応しています")

    pdf_bytes = await pdf.read()

    # 1. OCR
    contract_text = extract_text_from_pdf(pdf_bytes)

    # 2. リーガルチェック
    issues = legal_check_with_bedrock(contract_text, background, focus)

    # 3. Wordレポート生成
    word_path = generate_word_report(issues, background, focus)

    return FileResponse(
        word_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="legal_check_report.docx",
        background=None,
    )
