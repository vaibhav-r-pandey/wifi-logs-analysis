import httpx   
import openai   
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser
import requests
import os

# Initialize config with error handling
configur = ConfigParser()
config_files = ['config.ini', 'config_template.ini']
config_loaded = False

for config_file in config_files:
    if os.path.exists(config_file):
        configur.read(config_file)
        if configur.has_section('gpt4ifxapi'):
            config_loaded = True
            break

if not config_loaded:
    print("ERROR: No valid config file found")
    print("Available files:", [f for f in os.listdir('.') if f.endswith('.ini')])
    raise Exception("No valid config file found. Please create config.ini from config_template.ini")

# Get config values with fallbacks
Gpt4ifxUname = configur.get('gpt4ifxapi', 'username', fallback=os.getenv('GPT4IFX_USERNAME', ''))
Gpt4ifxPassword = configur.get('gpt4ifxapi', 'password', fallback=os.getenv('GPT4IFX_PASSWORD', ''))
Gpt4ifxchatUrl = configur.get('gpt4ifxapi', 'chaturl', fallback='https://gpt4ifx.icp.infineon.com')
Gpt4ifxBearertoken = configur.get('gpt4ifxapi', 'bearertoken', fallback='')
Gpt4ifxUrlBearertoken = configur.get('gpt4ifxapi', 'url_bearertoken', fallback='https://gpt4ifx.icp.infineon.com/auth/token')

print(f"Config loaded - Username: {Gpt4ifxUname[:3]}*** (masked)")
print(f"Token URL: {Gpt4ifxUrlBearertoken}")

def Gpt4ifx_get_Bearertoken():
    if not Gpt4ifxUname or not Gpt4ifxPassword:
        raise Exception("Username and password must be configured in config.ini or environment variables")
    
    print(f"Attempting to get token for user: {Gpt4ifxUname}")
    
    try:
        basic = HTTPBasicAuth(Gpt4ifxUname, Gpt4ifxPassword)
        response = requests.get(Gpt4ifxUrlBearertoken, auth=basic, verify=False, timeout=30)
        
        print(f"Token request status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.text.strip()
            print("Token obtained successfully")
            # Update config if possible
            if os.path.exists('config.ini'):
                configur.set('gpt4ifxapi','bearertoken', token)
                with open('config.ini', 'w') as f:
                    configur.write(f)
            return token
        elif response.status_code == 401:
            raise Exception(f"Authentication failed. Please check username/password. Response: {response.text}")
        else:
            raise Exception(f"Failed to get bearer token. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error getting token: {str(e)}")



# Client will be created when needed
client = None 

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
    try:
        # Get certificate path or disable SSL verification
        cert_path = None
        if os.path.exists('ca-bundle.crt'):
            cert_path = 'ca-bundle.crt'
        
        # Get fresh token
        token = Gpt4ifx_get_Bearertoken()
        
        # Create headers
        headers = {     
                'Authorization': f"Bearer {token}",      
                "accept": "application/json",
                "Content-Type": "application/json"}      
           
        # Create client
        client = openai.OpenAI(     
                    api_key=token,     
                    base_url='https://gpt4ifx.icp.infineon.com',      
                    default_headers=headers,     
                    http_client = httpx.Client(verify=cert_path if cert_path else False)   
                    )
        
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
    except Exception as e:
        raise Exception(f"AI API call failed: {str(e)}")