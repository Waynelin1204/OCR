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
    prompt = f"Human: 以下是 OCR 從發票擷取的內容： {ocr_text} 請解析這份發票，並將結果轉換為 JSON 格式，欄位包括：- invoice_number（發票號碼）- date（日期）- total_amount（總金額）- tax（稅額）- vendor（供應商）- items（明細項目） 請用 JSON 格式輸出：Assistant:"

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
