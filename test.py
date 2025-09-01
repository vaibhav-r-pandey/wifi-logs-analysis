import httpx   
import openai   
from requests.auth import HTTPBasicAuth
from configparser import ConfigParser
import requests
import os

# Global variables - will be initialized when needed
configur = None
Gpt4ifxUname = None
Gpt4ifxPassword = None
Gpt4ifxchatUrl = None
Gpt4ifxBearertoken = None
Gpt4ifxUrlBearertoken = None

def init_config():
    global configur, Gpt4ifxUname, Gpt4ifxPassword, Gpt4ifxchatUrl, Gpt4ifxBearertoken, Gpt4ifxUrlBearertoken
    
    if configur is not None:
        return  # Already initialized
    
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

    # Get config values with fallbacks - prioritize environment variables
    Gpt4ifxUname = os.getenv('GPT4IFX_USERNAME') or configur.get('gpt4ifxapi', 'username', fallback='')
    Gpt4ifxPassword = os.getenv('GPT4IFX_PASSWORD') or configur.get('gpt4ifxapi', 'password', fallback='')
    Gpt4ifxchatUrl = configur.get('gpt4ifxapi', 'chaturl', fallback='https://gpt4ifx.icp.infineon.com')
    Gpt4ifxBearertoken = configur.get('gpt4ifxapi', 'bearertoken', fallback='')
    Gpt4ifxUrlBearertoken = configur.get('gpt4ifxapi', 'url_bearertoken', fallback='https://gpt4ifx.icp.infineon.com/auth/token')

    print(f"Config loaded - Username: '{Gpt4ifxUname[:3]}***' (length: {len(Gpt4ifxUname)})")
    print(f"Password configured: {'Yes' if Gpt4ifxPassword else 'No'} (length: {len(Gpt4ifxPassword) if Gpt4ifxPassword else 0})")
    print(f"Token URL: {Gpt4ifxUrlBearertoken}")
    print(f"Environment GPT4IFX_USERNAME: {os.getenv('GPT4IFX_USERNAME', 'Not set')}")
    print(f"Environment GPT4IFX_PASSWORD: {'Set' if os.getenv('GPT4IFX_PASSWORD') else 'Not set'}")

def Gpt4ifx_get_Bearertoken():
    init_config()  # Initialize config if not done
    
    if not Gpt4ifxUname or not Gpt4ifxPassword:
        raise Exception("Username and password must be configured in config.ini or environment variables")
    
    print(f"Attempting to get token for user: {Gpt4ifxUname}")
    print(f"Using URL: {Gpt4ifxUrlBearertoken}")
    
    try:
        basic = HTTPBasicAuth(Gpt4ifxUname.strip(), Gpt4ifxPassword.strip())
        
        # Add headers that might be required
        headers = {
            'User-Agent': 'IFX-MSD-GenAI-Tool/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(Gpt4ifxUrlBearertoken, auth=basic, headers=headers, verify=False, timeout=30)
        
        print(f"Token request status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            token = response.text.strip()
            print(f"Token obtained successfully (length: {len(token)})")
            # Update config if possible
            if os.path.exists('config.ini'):
                configur.set('gpt4ifxapi','bearertoken', token)
                with open('config.ini', 'w') as f:
                    configur.write(f)
            return token
        elif response.status_code == 401:
            print(f"Auth failed - Username: '{Gpt4ifxUname}', Password length: {len(Gpt4ifxPassword)}")
            raise Exception(f"Authentication failed. Check credentials in HICP environment variables. Response: {response.text}")
        else:
            raise Exception(f"Failed to get bearer token. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error getting token: {str(e)}")



# Client will be created when needed
client = None 

def list_available_models():
    try:
        init_config()  # Initialize config if not done
        # Get fresh token and create client
        token = Gpt4ifx_get_Bearertoken()
        headers = {'Authorization': f"Bearer {token}", "accept": "application/json", "Content-Type": "application/json"}
        client = openai.OpenAI(api_key=token, base_url='https://gpt4ifx.icp.infineon.com', default_headers=headers, http_client=httpx.Client(verify=False))
        
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
        init_config()  # Initialize config if not done
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
        
        # Try different model names that might work
        model_names = [
            'llama3.3-70b',
            'llama-3.3-70b', 
            'meta-llama/Llama-3.3-70B',
            'llama3.1-70b',
            'llama-3.1-70b',
            'llama3-70b',
            'gpt-4'
        ]
        
        last_error = None
        for model in model_names:
            try:
                print(f"Trying model: {model}")
                completion = client.chat.completions.create(     
                            model=model,     
                            messages=[{"role": "user", "content": input_logs}],     
                            max_tokens=2048,     
                            stream=False,     
                            temperature=0.7,       
                        )   
                print(f"Success with model: {model}")
                return completion.choices[0].message.content
            except Exception as e:
                print(f"Model {model} failed: {str(e)}")
                last_error = e
                continue
        
        # If all models failed, raise the last error
        raise Exception(f"All models failed. Last error: {str(last_error)}")
        
    except Exception as e:
        raise Exception(f"AI API call failed: {str(e)}")
