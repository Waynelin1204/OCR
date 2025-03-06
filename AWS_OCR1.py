import boto3

textract_client = boto3.client("textract", region_name="us-east-1")

def extract_text_from_invoice(image_path):
# 讀取發票圖片

	with open(image_path, "rb") as file:
		img_bytes = file.read()

# 執行 Textract OCR

	response = textract_client.analyze_document(
		Document={"Bytes": img_bytes},
		FeatureTypes=["FORMS", "TABLES"]
	)

# 取得 OCR 文字
    # Output raw blocks to check if any Chinese text is being extracted
	for block in response["Blocks"]:
		if block["BlockType"] == "LINE":
			print(block["Text"])
            
	ocr_text = " ".join(
		[block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"]
	)
	return ocr_text
	
if __name__ == "__main__":
	image_path = "/home/pi/Downloads/發票明細(示意圖)_MF57558922_20250303184623865.pdf"
	ocr_result= extract_text_from_invoice(image_path)
	
	print(f"{ocr_result}取得 OCR 文字")
