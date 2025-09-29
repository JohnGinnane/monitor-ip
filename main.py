import requests
import configparser
import os.path
from datetime import datetime
import json

_config_file_path = "config.ini"
_config_section = "IP-MONITOR"
_log_file_path = "ip-log.txt"

_cloudflare_section = "CLOUDFLARE"

def listDNSRecords(api_token, zone_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    response = requests.get(url, headers={"Authorization": api_token})

    json_response = response.json()

    result = []
    for res in json_response["result"]:
        if res["type"] != "A":
            continue

        result.append({
            "id": res["id"],
            "type": res["type"],
            "name": res["name"],
            "content": res["content"]
        })

    return result

def updateDNSRecord(api_token, zone_id, record, new_ip):
    print(f"Updating DNS {record["name"]}: {record["content"]} -> {new_ip}")

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}"
    new_data = {
        "name": record["name"],
        "ttl": 1 if not "ttl" in record else record["ttl"],
        "type": record["type"],
        "content": new_ip
        }
    
    response = requests.put(url,
                            headers={"Authorization": api_token},
                            json=new_data)
    
    json_response = json.loads(response.content)
    
    if json_response["success"]:
        print("Done!")
    else:
        print(f"An error occured updating {record["id"]}:")

        if "errors" in json_response:
            for err in json_response["errors"]:
                print(f"Code: {err["code"]}. Message: {err["message"]}")

def getExternalIP():
    return requests.get('https://api.ipify.org').content.decode('utf8')

def logNewIP(ip):
    if not os.path.isfile(_log_file_path):
        with open(_log_file_path, "w") as log_file:
            log_file.write(f"timestamp,ip\n")
    
    with open(_log_file_path, "a") as log_file:
        log_file.write(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, {ip}\n")

_zone_id = ""
_api_token = ""
_last_ip = ""
_timestamp = datetime.now()

# Look for config file
# 1. If not there then create
# 2. If present and ill-defined
#    then populate with empty keys
# 3. Read values from config file

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
        _zone_id = config[_config_section]["zone_id"]

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

if _zone_id == "":
    print("No zone ID specified!")
    exit()

if _api_token == "":
    print("No API token specified!")
    exit()

external_ip = getExternalIP()

if _last_ip != "":
    print(f"Last IP:  {_last_ip}")

print(f"My IP is: {external_ip}")

if external_ip != _last_ip:
    # First log any changes to IP into a separate log file
    logNewIP(external_ip)

    # Get list of DNS records that have to be updated
    records = listDNSRecords(_api_token, _zone_id)

    # Iterate over each one and ignore 192.168.0.0/16
    for dns_record in records:
        # Ignore private range
        if dns_record["content"][:8] == "192.168.":
            continue

        # Update each DNS record
        updateDNSRecord(_api_token, _zone_id, dns_record, external_ip)

# Log the time we completed this task
config[_config_section]["last_ip"] = external_ip
config[_config_section]["timestamp"] = _timestamp.strftime("%Y-%m-%d %H:%M:%S")

with open(_config_file_path, "w") as config_file:
    config.write(config_file)