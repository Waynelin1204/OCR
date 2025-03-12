import cv2

import base64

import json
import numpy as np
from pyzbar.pyzbar import decode

def scan_invoice_qr(image_path):

    """掃描發票上的 QR Code 並解析完整內容"""

    img = cv2.imread(image_path)

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
    
    total_qr_decoded = f"{left_qr_data}{right_qr_data}"
 


    cleaned_qr_data = total_qr_decoded[95:]  # Remove the first 88 characters
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
