import boto3
import json
import cv2
from pyzbar.pyzbar import decode
from OCR import detect_text
import os 
import glob
import pandas as pd
import sqlite3

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

def save_invoice_as_json(invoice_data, image_path):
    """ Save the invoice data as a JSON file in the same folder as the image """
    if invoice_data:
        # Get the image filename without extension
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        json_filename = f"{image_name}_invoice.json"
        json_filepath = os.path.join(os.path.dirname(image_path), json_filename)

        with open(json_filepath, "w", encoding="utf-8") as json_file:
            json.dump(invoice_data, json_file, ensure_ascii=False, indent=4)

        print(f"✅ Invoice data saved to {json_filepath}")
    else:
        print("❌ No data to save.")


# Function to write JSON data into the database
def write_json_to_db():
    """Reads invoice JSON files and inserts them into the SQLite database."""
    
    conn = sqlite3.connect("/home/pi/mydjango/e_invoice/e_invoice/db.sqlite3")
    cursor = conn.cursor()
    json_folder = "/home/pi/OCR/Samples"

    # Connect to SQLite database

    # Ensure tables exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS e_invoices_ocr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            random_code TEXT,
            invoice_date DATE,
            buyer_tax_id TEXT,
            seller_tax_id TEXT,
            total_amount REAL,
            tax_amount REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS e_invoices_ocritem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ocr_id INTEGER,
            product_name TEXT,
            quantity TEXT,
            unit_price REAL,
            FOREIGN KEY (ocr_id) REFERENCES Ocr(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()

    # Get all JSON files
    json_files = glob.glob(os.path.join(json_folder, "*.json"))

    if not json_files:
        print("No JSON files found in directory.")
        conn.close()
        return

    for json_file in json_files:
        print(f"Processing file: {json_file}")

        try:
            with open(json_file, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            # Extract invoice data
            invoice_number = json_data.get("發票號碼")
            random_code = json_data.get("隨機碼")
            invoice_date = json_data.get("發票日期")
            buyer_tax_id = json_data.get("買方統一編號")
            seller_tax_id = json_data.get("賣方統一編號")
            total_amount = json_data.get("總金額")
            tax_amount = json_data.get("稅額")
            items = json_data.get("品名、數量、單價、總計", [])

            # Ensure items is a list
            if not isinstance(items, list):
                print(f"⚠️ Warning: '品名、數量、單價、總計' is not a list in {json_file}. Skipping items.")
                items = []

            # Insert invoice data
            cursor.execute('''
                INSERT INTO e_invoices_ocr (
                    invoice_number, random_code, invoice_date, buyer_tax_id, 
                    seller_tax_id, total_amount, tax_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_number, random_code, invoice_date, buyer_tax_id, 
                seller_tax_id, total_amount, tax_amount
            ))

            ocr_id = cursor.lastrowid  # Get inserted invoice ID

            # Insert items
            for item in items:
                if not isinstance(item, dict):
                    print(f"⚠️ Skipping invalid item format in {json_file}: {item}")
                    continue  # Skip invalid item

                product_name = item.get("品名", "Unknown")
                quantity = item.get("數量", "1")  # Default to 1 if missing
                unit_price = item.get("單價")

                # Handle unit price safely
                if unit_price is None or unit_price == "":
                    unit_price = 0.00
                else:
                    try:
                        unit_price = float(str(unit_price).replace("**", "").strip())
                    except ValueError:
                        unit_price = 0.00  # Default to 0.00 if conversion fails

                cursor.execute('''
                    INSERT INTO e_invoices_ocritem (
                        ocr_id, product_name, quantity, unit_price
                    ) VALUES (?, ?, ?, ?)
                ''', (ocr_id, product_name, quantity, unit_price))

            print(f"✅ Inserted invoice {invoice_number} with {len(items)} items")

        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")

    # Commit and close database connection
    conn.commit()
    conn.close()
    print("✅ All JSON files processed successfully!")
if __name__ == "__main__":
    downloads_folder = os.path.expanduser("/home/pi/OCR/Samples")
    json_files = glob.glob(os.path.join(downloads_folder, "*.json"))  # Get all .json files in the folder

    folder_path = "/home/pi/OCR/Samples"  # Path to the folder with images

     # Loop through all files in the Samples folder
    for filename in os.listdir(folder_path):
         if filename.lower().endswith(('.jpeg', '.jpg', '.png', 'pdf')):  # Check if the file is an image
             image_path = os.path.join(folder_path, filename)

             print(f"🖼️ Analyzing {filename}...")

            # 1️⃣ OCR + Bedrock parsing
             invoice_json = parse_invoice_with_bedrock(image_path)

            # 2️⃣ If AI parsing fails, replace with QR Code
             final_invoice = validate_and_replace_items(invoice_json, image_path)

            # 3️⃣ Output the result (printed to console)
             print(json.dumps(final_invoice, ensure_ascii=False, indent=4))

            # 4️⃣ Save the result as a JSON file in the same folder
             save_invoice_as_json(final_invoice, image_path)
            
            #write_json_to_db(downloads_folder)
    write_json_to_db()
