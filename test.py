import httpx   
import openai   
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser
import requests
import os

configur = ConfigParser()
configur.read('config_template.ini')

Gpt4ifxUname = configur.get('gpt4ifxapi','username')
Gpt4ifxPassword = configur.get('gpt4ifxapi','password')
Gpt4ifxchatUrl = configur.get('gpt4ifxapi','chaturl')
Gpt4ifxBearertoken = configur.get('gpt4ifxapi','bearertoken')
Gpt4ifxUrlBearertoken = configur.get('gpt4ifxapi','url_bearertoken')

def Gpt4ifx_get_Bearertoken():
    basic = HTTPBasicAuth(Gpt4ifxUname, Gpt4ifxPassword)
    response = requests.get(Gpt4ifxUrlBearertoken, auth=basic, verify=False)
    print(response.text)
    
    if response.status_code == 200:
        Gpt4ifxBearertoken = response.text
        configur.set('gpt4ifxapi','bearertoken', Gpt4ifxBearertoken)

        return response.text

    else:
        print("Error:", response.status_code)



# Get certificate path or disable SSL verification
cert_path = None
if os.path.exists('ca-bundle.crt'):
    cert_path = 'ca-bundle.crt'

token = Gpt4ifx_get_Bearertoken()
headers = {     
        'Authorization': f"Bearer {token}",      
        "accept": "application/json",
        "Content-Type": "application/json"}      
   
client = openai.OpenAI(     
            api_key=token,     
            base_url='https://gpt4ifx.icp.infineon.com',      
            default_headers=headers,     
            http_client = httpx.Client(verify=cert_path if cert_path else False)   
            ) 

def list_available_models():
    try:
        models = client.models.list()
        print("Available models:")
        for model in models.data:
            print(f"- {model.id}")
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def test_chat_completion_api(input_logs):     
    model = configur.get('gpt4ifxapi', 'model', fallback='llama3-70b')
    user_message = input_logs       
    completion = client.chat.completions.create(     
                    model=model,     
                    messages=[{"role": "user", "content": user_message}],     
                    max_tokens=2048,     
                    stream=False,     
                    temperature=0.7,       
                )   
    return completion.choices[0].message.content
