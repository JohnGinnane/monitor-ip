import requests
import configparser
import os.path
from datetime import datetime

def listDNSRecords(api_token, zone_id):
    url = "https://api.cloudflare.com/client/v4/zones/" + zone_id + "/dns_records"
    response = requests.get(url, headers={"Authorization": api_token})
    # json_response = json.loads(response.text)
    # return json_response

    json_response = response.json()

    result = []
    for res in json_response["result"]:
        if res["type"] != "A":
            continue

        #print(f"id: {res["id"]},\ttype: {res["type"]},\tname: {res["name"]},\tcontent: {res["content"]}")
        result.append({
            "id": res["id"],
            "type": res["type"],
            "name": res["name"],
            "content": res["content"]
        })

    return result

def getExternalIP():
    return requests.get('https://api.ipify.org').content.decode('utf8')

_config_file_path = "config.ini"
_config_section = "IP-MONITOR"

_zone_id = ""
_api_token = ""
_last_ip = ""
_timestamp = datetime.now()

# Look for config file
# 1. If not there then create
# 2. If present and ill-defined
#    then populate with empty keys

config = configparser.ConfigParser()

if not os.path.isfile(_config_file_path):
    config[_config_section] = {
        "zone_id": "",
        "api_token": "",
        "last_ip": "",
        "timestamp": ""
    }

    with open(_config_file_path, "w") as config_file:
        config.write(config_file)
else:
    # Check the existing file
    config.read(_config_file_path)

if not _config_section in config.sections():
    config[_config_section] = {
        "zone_id": "",
        "api_token": "",
        "last_ip": "",
        "timestamp": ""
    }

    with open(_config_file_path, "w") as config_file:
        config.write(config_file)
else:
    # File and section exists
    # Make sure each key exists
    if not "zone_id" in config[_config_section]:
        config[_config_section]["zone_id"] = ""
    else:
        _zone_id  = config[_config_section]["zone_id"]

    if not "api_token" in config[_config_section]:
        config[_config_section]["api_token"] = ""
    else:
        _api_token = config[_config_section]["api_token"]

    if not "last_ip" in config[_config_section]:
        config[_config_section]["last_ip"] = ""
    else:
        _last_ip = config[_config_section]["last_ip"]
    
    if not "timestamp" in config[_config_section]:
        config[_config_section]["timestamp"] = ""
    else:
        if config[_config_section]["timestamp"] != "":
            try:
                _timestamp = datetime.strptime(config[_config_section]["timestamp"], "%Y-%m-%d %H:%M:%S")
            finally:
                _timestamp = datetime.now()

print(f"Zone:      {_zone_id}")
print(f"Token:     {_api_token}")
print(f"Last IP:   {_last_ip}")
print(f"Timestamp: {_timestamp.strftime("%H:%M:%S, %d/%m/%Y")}")

if _zone_id == "":
    print("No zone ID specified!")
    exit()

if _api_token == "":
    print("No API token specified!")
    exit()

external_ip = getExternalIP()
print(f"My IP is: {external_ip}")

records = listDNSRecords(_api_token, _zone_id)

for rec in records:
    print(rec)

if external_ip != _last_ip:
    # Do the work here
    # Iterate over DNS records and
    # if they are the old IP 
    # OR they are NOT the new IP 
    # then update them!
    print("IP changed!")

    # Also log any changes to IP into a separate log file

config[_config_section]["last_ip"] = external_ip
config[_config_section]["timestamp"] = _timestamp.strftime("%Y-%m-%d %H:%M:%S")

with open(_config_file_path, "w") as config_file:
    config.write(config_file)