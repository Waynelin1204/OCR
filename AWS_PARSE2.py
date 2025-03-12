import boto3
import json


bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")


# 設定 LLM 提示詞（Prompt），要求 AI 解析發票欄位
def parse_invoice_with_bedrock(ocr_text):
    """ 
    使用 Amazon Bedrock Claude AI 解析發票內容，轉換為結構化 JSON 
    :param ocr_text: 來自 Textract OCR 擷取的文字內容 
    :return: 解析後的 JSON 結果 
    """ 
    #prompt = f"Human: 以下是 OCR 擷取的發票內容：{ocr_text}\n請解析這份發票，並以 JSON 格式輸出。\n確保：\n- 'invoice_number' 僅包含發票號碼，不要添加日期。\n- 'date' 格式為 YYYY-MM-DD，例如：'2022-02-13'。\n- 'total_amount'、'tax'、'unit_price' 需保持數值格式，不要加幣別或其他符號。\n- 'items' 內的商品資訊應包含 'name', 'quantity', 'unit_price', 'tax_rate', 'net_amount'。只輸出 JSON，**不要輸出任何其他文字**, \nAssistant:"
    prompt = f"Human: 這是一張台灣電子發票的 OCR 辨識結果：{ocr_text}，請解析出結構化 JSON，包含：'發票號碼'（發票號碼）、'隨機碼'（隨機碼）、'發票日期'（發票日期 YYYY-MM-DD）、'買方統一編號'（買方統一編號）、'賣方統一編號'（賣方統一編號）、'總金額'（總金額）、'稅額'（稅額）、'品名、數量、單價、總計'（品名、數量、單價、總計）。確保 JSON 格式正確，缺失欄位填入 null，不要額外說明。Assistant:"
# 呼叫 Bedrock Claude 來解析
    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-v2",
            #modelId="amazon.titan-text-lite-v1",
            body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 1000})
        )

# 取得 AI 解析結果

        result = json.loads(response["body"].read().decode("utf-8"))
        #parsed_invoice = result["completion"]
        #parsed_invoice = response_body.get("completion","").strip()
        return result.get("completion","Failed")
    
    except Exception as e:
        print(f"Error{str(e)}")
        return (f"Error{str(e)}")
