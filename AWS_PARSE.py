import boto3

import json

import cv2

from pyzbar.pyzbar import decode

from OCR import detect_text

 

# 初始化 Bedrock Client

bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")

 

# LLM 解析發票

def parse_invoice_with_bedrock(image_path):

    """ 使用 Amazon Bedrock Claude AI 解析發票內容，轉換為結構化 JSON """

    ocr_text = detect_text(image_path)

    prompt = f"Human: 這是一張台灣電子發票的 OCR 辨識結果：{ocr_text}，請解析出結構化 JSON，包含：'發票號碼'（發票號碼）、'隨機碼'（隨機碼）、'發票日期'（發票日期 YYYY-MM-DD）、'買方統一編號'（買方統一編號）、'賣方統一編號'（賣方統一編號）、'總金額'（總金額）、'稅額'（稅額）、'品名、數量、單價、總計'（品名、數量、單價、總計）。確保 JSON 格式正確，缺失欄位填入 null，不要額外說明。Assistant:"

 

    try:

        response = bedrock_client.invoke_model(

            modelId="anthropic.claude-v2",

            body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 1000})

        )

 

        raw_body = response["body"].read().decode("utf-8").strip()

 

        # 確保 Claude 有回傳內容

        if not raw_body:

            print("❌ Claude AI 沒有回傳內容")

            return None

 

        # 嘗試解析 Bedrock 回應 JSON

        try:

            result = json.loads(raw_body)

        except json.JSONDecodeError as e:

            print("❌ Claude AI 回傳格式錯誤，無法解析 JSON：", e)

            return None

 

        # 取出 JSON 內的 completion 內容

        parsed_invoice_str = result.get("completion", "").strip()

        if not parsed_invoice_str:

            print("❌ Claude AI 解析失敗，回傳內容為空")

            return None

 

        # 嘗試解析 Claude 產生的 JSON

        try:

            invoice_json = json.loads(parsed_invoice_str)

            return invoice_json

        except json.JSONDecodeError as e:

            print("❌ Claude AI 回傳的 JSON 內容格式錯誤：", e)

            return None

 

    except Exception as e:

        print(f"❌ Bedrock API 錯誤：{str(e)}")

        return None

 

# 掃描 QR Code 並解析

def scan_qr_code(image_path):

    """ 掃描發票上的 QR Code 並解析 """

    img = cv2.imread(image_path)

    qr_codes = decode(img)

 

    qr_data_list = sorted(qr_codes, key=lambda qr: qr.rect.left)

   

    if len(qr_data_list) == 1:

        left_qr_data = qr_data_list[0].data.decode("utf-8").strip()

        right_qr_data = ""

    elif len(qr_data_list) == 2:

        left_qr_data = qr_data_list[0].data.decode("utf-8").strip()

        right_qr_data = qr_data_list[1].data.decode("utf-8").strip()

        if right_qr_data == "**":

            right_qr_data = ""

    else:

        left_qr_data = ""

        right_qr_data = ""

 

    total_qr_decoded = f"{left_qr_data}{right_qr_data}"

    cleaned_qr_data = total_qr_decoded[95:]  # 移除前 95 個字

    fields = cleaned_qr_data.split(":") 

 

    if len(fields) < 3:

        print("⚠️ 解析錯誤：QR Code 內容不完整")

        return []

 

    # 解析 QR Code 內容

    invoice_items = []

    for i in range(0, len(fields), 3):

        if i + 2 < len(fields):

            item = {

                "品名": fields[i],

                "數量": fields[i + 1],

                "單價": fields[i + 2]

            }

            invoice_items.append(item)

 

    return invoice_items

 

# 核對發票解析內容，必要時替換品項

def validate_and_replace_items(parsed_invoice, image_path):

    """ 如果 AI 無法解析品項，則改用 QR Code 解析 """

    if not parsed_invoice:

        print("❌ AI 解析失敗，無法處理發票")

        return None

 

    # 判斷是否需要替換品項

    if parsed_invoice.get("品名、數量、單價、總計") in (None, [{"品名": None, "數量": None, "單價": None, "總計": None}]):

        print("⚠️ AI 解析發票品項失敗，改用 QR Code 解析")

       

        qr_items = scan_qr_code(image_path)

        if qr_items:

            parsed_invoice["品名、數量、單價、總計"] = qr_items

        else:

            print("⚠️ 無法解析 QR Code，品項資訊仍然為空")

 

    return parsed_invoice

 

if __name__ == "__main__":

    image_path = "/home/pi/Downloads/收據_2025-03-08_123011.jpeg"

   

    # 1️⃣ OCR + Bedrock 解析

    invoice_json = parse_invoice_with_bedrock(image_path)

 

    # 2️⃣ 若 AI 解析失敗，則改用 QR Code 補充

    final_invoice = validate_and_replace_items(invoice_json, image_path)
    

 

    # 3️⃣ 輸出結果

    print(json.dumps(final_invoice, ensure_ascii=False, indent=4))
