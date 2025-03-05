import json
from AWS_OCR import extract_text_from_invoice
from AWS_PARSE import parse_invoice_with_bedrock
import os

def process_invoice(image_path):
	ocr_text = extract_text_from_invoice(image_path)
	structured_invoice = parse_invoice_with_bedrock(ocr_text)
	
	return structured_invoice
	
if __name__ == "__main__":
	invoice_path = "/home/pi/Downloads/Invoice ADVANTECH CO. MALAYSIA SDN BHD MY01202500953954460001.pdf"
	invoice_json = process_invoice(invoice_path)
	
	invoice_name = os.path.splitext(os.path.basename(invoice_path))[0]
	output_path = f"/home/pi/Downloads/{invoice_name}.json"
	
	with open(output_path, "w", encoding="utf-8") as json_file:
		json.dump(invoice_json, json_file, ensure_ascii=False, indent=4)
	
