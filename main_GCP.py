import json
from AWS_OCR import extract_text_from_invoice
from AWS_PARSE import parse_invoice_with_bedrock
from OCR import detect_text
import os

def process_invoice(image_path):
	#ocr_text = extract_text_from_invoice(image_path)
	ocr_text = detect_text(image_path)
	structured_invoice = parse_invoice_with_bedrock(ocr_text)
	
	return structured_invoice
	
	
if __name__ == "__main__":
	invoice_path = "/home/pi/Downloads/影像 (10).png"
	invoice_json = process_invoice(invoice_path)
	print(invoice_json)
	
	invoice_name = os.path.splitext(os.path.basename(invoice_path))[0]
	output_path = f"/home/pi/Downloads/{invoice_name}.json"
    
    # Save the JSON string to a file directly
	with open(output_path, "w", encoding="utf-8") as json_file:
		json_file.write(invoice_json)  # Write the JSON string to the file
	
