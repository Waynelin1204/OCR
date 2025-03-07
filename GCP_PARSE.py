from google.cloud import documentai
import json

PROJECT_ID = "pelagic-media-452803-q0"
LOCATION = "us"
PROCESSOR_ID = "1134bfc5d82d7bf6"

# 設定 LLM 提示詞（Prompt），要求 AI 解析發票欄位
def process_invoice(image_path):
    client = documentai.DocumentProcessorServiceClient()
    name =  f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    with open(image_path, 'rb') as img:
        image_content = img.read()
        
    request = documentai.ProcessRequest(
        name = name,
        raw_document = documentai.RawDocument(content=image_content, mime_type="image/jpeg"),
    )
    
    response = client.process_document(request=request)
    document = response.document
    
    parsed_data = {}
    
    for entity in document.entities:
        parsed_data[entity.type_] = entity.mention_text

    print(json.dumps(parsed_data, indent=4, ensure_ascii=False))
    return parsed_data
    
process_invoice("/home/pi/Downloads/IMG_4339.jpg")
