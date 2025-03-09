import cv2

import base64

import json
import numpy as np
from pyzbar.pyzbar import decode

def enhance_image(image, save_path="/home/pi/Downloads/enhanced.jpeg"):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
	
	enhanced = clahe.apply(gray)
	
	kernel =   np.array([[0, -1, 0],
						[-1, 5, 1],
						[0, -1, 0]])
						
	sharpened = cv2.filter2D(enhanced, -1, kernel)
	
	binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
	
	cv2.imwrite(save_path, binary)
	return binary

def scan_invoice_qr(image_path):

    """掃描發票上的 QR Code 並解析完整內容"""

    img = cv2.imread(image_path)

    enhanced_img = enhance_image(img)

    qr_codes = decode(img)

 

    if len(qr_codes) < 1:

        print("❌ 未偵測到完整的兩個 QR Code，請調整圖片或重試")

        return None, None

 
    qr_data_list = sorted(qr_codes, key=lambda qr: qr.rect.left)  # Sort by X-axis

    # 根據 QR Code 位置判斷左右（通常較左側的是發票資訊，右側是品項）


    


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

 

    return left_qr_data, right_qr_data

 

def decode_base64_if_needed(qr_data):

    """嘗試解碼 Base64，失敗則直接返回"""

    try:

        decoded_bytes = base64.b64decode(qr_data + "=" * ((4 - len(qr_data) % 4) % 4))  # 自動補齊 Base64 長度

        decoded_text = decoded_bytes.decode("utf-8")

        return decoded_text

    except Exception:

        return qr_data  # 不是 Base64，直接返回原始內容

 

def right_parse_invoice_items(qr_data):

    """解析電子發票的 QR Code 內容（右側 QR Code）"""

    cleaned_qr_data = qr_data[95:]  # Remove the first 88 characters
    fields = cleaned_qr_data.split(":")  # 以 ":" 分隔欄位
    
    print(fields)

 

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


if __name__ == "__main__":

    image_path="/home/pi/Downloads/收據_2025-03-08_120518_1.jpeg"  # 發票圖片路徑

    left_qr, right_qr = scan_invoice_qr(image_path)

        # 嘗試解碼（如果是 Base64）

    #right_qr_decoded = decode_base64_if_needed(right_qr)
    #left_qr_decoded = decode_base64_if_needed(left_qr)
        
    total_qr_decoded = f"{left_qr}{right_qr}"
        

        # 解析發票品項

    total_invoice_items = right_parse_invoice_items(total_qr_decoded)
        

 

        # JSON 格式輸出

    invoice_json = json.dumps({"品項": total_invoice_items}, indent=4, ensure_ascii=False)

    print("📄 發票品項解析結果：")

    print(invoice_json)
