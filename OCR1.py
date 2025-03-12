from google.cloud import vision
from pdf2image import convert_from_path
import json
import io

client = vision.ImageAnnotatorClient()
fields_coordinates = {
	"UUID":[(396,517),(716,537)],
	"Taxable Amount":[(1453,1006),(1521,1021)]
}

def detect_text(pdf_path):
	result_dict = {}

	images =convert_from_path(pdf_path)

	for i, image in enumerate(images):
		image_byte_array = io.BytesIO()
		image.save(image_byte_array, format='PNG')
		content = image_byte_array.getvalue()

		image = vision.Image(content=content)
		try:
			response = client.text_detection(image=image)
		except:
			print(f"Error{e}")
			return
			
		texts = response.text_annotations

		if texts:
			for text in texts:
				text_description = text.description
				vertices = text.bounding_poly.vertices
					
					
				for field, (start, end) in fields_coordinates.items():
					x1, y1 =start
					x2, y2 = end
						
					if x1 <= vertices[0].x <= x2 and y1 <= vertices[0].y <= y2:
						result_dict[field] = text_description
						break
		else:
			result_dict["text"] = "No Text"
	return result_dict			

pdf_path = '/home/pi/Downloads/Invoice ADVANTECH CO. MALAYSIA SDN BHD MY01202500953954460001'
result_dict = detect_text(pdf_path)

if result_dict:
	json_result = json.dumps(result_dict, indent=4, ensure_ascii=False)
	print(json_result)

	with open('ocr_result.json', 'w', encoding='utf-8') as json_file:
		json.dump(result_dict,json_file, ensure_ascii=False, indent=4)
