import boto3
import json
import cv2
from pyzbar.pyzbar import decode
from OCR import detect_text
from AWS_OCR import extract_text_from_invoice
# Initialize the Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")

# LLM parsing function
def parse_invoice_with_bedrock(image_path):
    ocr_text = detect_text(image_path)
    """ 
    使用 Amazon Bedrock Claude AI 解析發票內容，轉換為結構化 JSON 
    :param ocr_text: 來自 Textract OCR 擷取的文字內容 
    :return: 解析後的 JSON 結果 
    """ 
    prompt = f"Human: 這是一張台灣電子發票的 OCR 辨識結果：{ocr_text}，請解析出結構化 JSON，包含：'發票號碼'（發票號碼）、'隨機碼'（隨機碼）、'發票日期'（發票日期 YYYY-MM-DD）、'買方統一編號'（買方統一編號）、'賣方統一編號'（賣方統一編號）、'總金額'（總金額）、'稅額'（稅額）、'品名、數量、單價、總計'（品名、數量、單價、總計）。確保 JSON 格式正確，缺失欄位填入 null，不要額外說明。Assistant:"

    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-v2",
            body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 1000})
        )

        result = json.loads(response["body"].read().decode("utf-8"))
        parsed_invoice = result.get("completion", "Failed")

        return parsed_invoice
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

# Function to scan QR code from an image
def QR(image_path, parsed_invoice):
    """掃描發票上的 QR Code 並解析完整內容"""
    img = cv2.imread(image_path)
    qr_codes = decode(img)

    #if len(qr_codes) < 1:
    #    print("❌ 未偵測到完整的兩個 QR Code，請調整圖片或重試")
    #    return None
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
    cleaned_qr_data = total_qr_decoded[95:]  # Remove the first 88 characters
    fields = cleaned_qr_data.split(":")  # Split the fields by ":"
    
    if len(fields) < 0:
        print("⚠️ 解析錯誤：QR Code 內容不完整，請確認是否需要解密")
        return None

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

    # Step 2: Check if items are missing in the parsed invoice
    if parsed_invoice.get("品名、數量、單價、總計") == [
    {
        "品名": null,
        "數量": null,  
        "單價": null,
        "總計": null  
    }
]:
        print("No item details found in the AI parsing, attempting to scan QR code.")
        # Step 3: Use QR code scanning to get the missing items
        if invoice_items:
            parsed_invoice["品名、數量、單價、總計"] = invoice_items
            print(parsed_invoice)
        else:
            print("Failed to extract items from QR code.")

    return parsed_invoice

if __name__ == "__main__":
    image_path = "/home/pi/Downloads/收據_2025-03-08_123011_2.jpg"
    invoice_json = parse_invoice_with_bedrock(image_path)
    QRA = QR(image_path,invoice_json)
    print(invoice_json)
