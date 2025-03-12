import cv2
from pyzbar.pyzbar import decode
import webbrowser

def scan_invoice_qr(image_path):
	img = cv2.imread(image_path)
	
	qr_codes = decode(img)
	
	if not qr_codes:
		return
		
	qr_data_list = [qr.data.decode("utf-8") for qr in qr_codes]
	
	return qr_data_list[0] if qr_data_list else None
		
def  parse_invoice_data(qr_data):
	
	fields = qr_data.split(":")
	
	if len(fields) < 6 :
		return None
	
	item_data = fields[6:]
	items = []
	
	for i in range(0, len(item_data),2):
		if i + 1 < len(item_data):
			item = {
				"品名": fields[i],
				"單價": fields[i + 1],
				"數量": fields[i + 2]
			}
			invoice_info["品名"].append(item)
			
	return invoice_info
	
if __name__ == "__main__":
	image_path="/home/pi/Downloads/IMG_4341.jpg"
	qr_contents = scan_invoice_qr(image_path)
	
	if qr_contents:
		for idx, qr_content in enumerate(qr_contents):
			print(f"QR Code {idx+1} content:\n{qr_content}\n")
			invoice = parse_invoice_data(qr_content)
			if invoice:
				print(invoice)
