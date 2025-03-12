import cv2
from pyzbar.pyzbar import decode
import base64
import json 

def scan_invoice_qr(image_path):

    """掃描發票圖片上的兩個 QR Code 並解析內容"""

    img = cv2.imread(image_path)

    qr_codes = decode(img)

 

    if len(qr_codes) < 2:

        print("❌ 未偵測到兩個 QR Code，請確保發票完整")

        return None, None

   

    # 取左邊的 QR Code（一般來說，QR Code 會依座標順序排列）

    right_qr_data = qr_codes[0].data.decode("utf-8")

    left_qr_data = qr_codes[1].data.decode("utf-8")

 

    return left_qr_data, right_qr_data

 

def decode_base64_if_needed(qr_data):

    """判斷 QR Code 內容是否為 Base64，若是則解碼"""

    try:

        decoded_bytes = base64.b64decode(qr_data)

        decoded_text = decoded_bytes.decode("utf-8")

        return decoded_text

    except Exception:

        return qr_data  # 不是 Base64，就直接回傳原內容

 

def parse_invoice_items(qr_data):

    """解析 QR Code 解碼後的發票品項資訊"""

    fields = qr_data.split(":")  # 使用 ":" 作為分隔符號

   

    if len(fields) < 0:

        print("⚠️ 發票格式不符，可能需要解密")

        return None

 

    # 解析品項資訊

    invoice_items = []

    for i in range(0, len(fields), 3):

        if i + 2 < len(fields):

            item = {

                "品名": fields[i],

                "單價": fields[i + 1],

                "數量": fields[i + 2]

            }

            invoice_items.append(item)

 

    return invoice_items

 

if __name__ == "__main__":

    image_path = "/home/pi/Downloads/IMG_4343.jpeg"  # 發票圖片路徑

 

    # 讀取 QR Code

    left_qr, right_qr = scan_invoice_qr(image_path)

   

    if left_qr and right_qr:

        print("📌 左邊 QR Code 原始內容：", left_qr)

        print("📌 右邊 QR Code 原始內容：", right_qr)

 

        # 先解碼（如果是 Base64）

        #left_qr_decoded = decode_base64_if_needed(left_qr)

        right_qr_decoded = decode_base64_if_needed(right_qr)

 

        # 解析發票品項

        invoice_items = parse_invoice_items(right_qr_decoded)

 

        # 輸出 JSON 結果

        invoice_json = json.dumps({"品項": invoice_items}, indent=4, ensure_ascii=False)

        print("📄 發票品項解析結果：")

        print(invoice_json)
        
 
