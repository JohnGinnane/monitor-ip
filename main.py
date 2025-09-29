import requests
import configparser
import os.path
from datetime import datetime
import json

_config_file_path = "config.ini"
_config_section = "MONITOR-IP"
_log_file_path = "ip-log.txt"

_cloudflare_section = "CLOUDFLARE"
_cloudflare_zone_id = ""
_cloudflare_api_token = ""

def Cloudflare_ListDNSRecords(api_token, zone_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    response = requests.get(url, headers={"Authorization": api_token})

    json_response = response.json()

    result = []
    for res in json_response['result']:
        if res['type'] != "A":
            continue

        result.append({
            "id": res['id'],
            "type": res['type'],
            "name": res['name'],
            "content": res['content']
        })

    return result

def Cloudflare_UpdateDNSRecord(api_token, zone_id, record, new_ip):
    print(f"Updating DNS {record['name']}: {record['content']} -> {new_ip}")

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
    new_data = {
        "name": record['name'],
        "ttl": 1 if not "ttl" in record else record['ttl'],
        "type": record['type'],
        "content": new_ip
        }
    
    response = requests.put(url,
                            headers={"Authorization": api_token},
                            json=new_data)
    
    json_response = json.loads(response.content)
    
    if json_response['success']:
        print("Done")
    else:
        print(f"An error occured updating {record['id']}:")

        if "errors" in json_response:
            for err in json_response['errors']:
                print(f"Code: {err['code']}. Message: {err['message']}")

def getExternalIP():
    return requests.get('https://api.ipify.org').content.decode('utf8')

def logNewIP(ip):
    if not os.path.isfile(_log_file_path):
        with open(_log_file_path, "w") as log_file:
            log_file.write(f"timestamp,ip\n")
    
    with open(_log_file_path, "a") as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {ip}\n")

_last_ip = ""
_timestamp = datetime.now()

# Look for config file
config = configparser.ConfigParser()

# 1. If not there then create
if not os.path.isfile(_config_file_path):
    config[_config_section] = {
        "ip": "",
        "timestamp": ""
    }

    with open(_config_file_path, "w") as config_file:
        config.write(config_file)

config.read(_config_file_path)

# 2. If present and ill-defined
#    then populate with empty keys
if not _config_section in config.sections():
    config[_config_section] = {
        "ip": "",
        "timestamp": ""
    }

    with open(_config_file_path, "w") as config_file:
        config.write(config_file)

# 3. Read values from config file
config.read(_config_file_path)

# File and section exists
# Make sure each key exists
if not "ip" in config[_config_section]:
    config[_config_section]['ip'] = ""
else:
    _last_ip = config[_config_section]['ip']

if not "timestamp" in config[_config_section]:
    config[_config_section]['timestamp'] = ""
else:
    if config[_config_section]['timestamp'] != "":
        try:
            _timestamp = datetime.strptime(config[_config_section]['timestamp'], "%Y-%m-%d %H:%M:%S")
        finally:
            _timestamp = datetime.now()

# Cloudflare support
if _cloudflare_section in config:
    _cloudflare_zone_id = "" if not "zone_id" in config[_cloudflare_section] else config[_cloudflare_section]['zone_id']
    _cloudflare_api_token = "" if not "api_token" in config[_cloudflare_section] else config[_cloudflare_section]['api_token']

external_ip = getExternalIP()

print(f"Last IP:  {_last_ip}")
print(f"My IP is: {external_ip}")

if external_ip != _last_ip and external_ip != "":
    # First log any changes to IP into a separate log file
    logNewIP(external_ip)

    # Get list of DNS records that have to be updated
    if _cloudflare_api_token != "" and _cloudflare_zone_id != "":
        print("Cloudflare details found, updating DNS records...")
        records = Cloudflare_ListDNSRecords(_cloudflare_api_token, _cloudflare_zone_id)

        # Iterate over each one and ignore 192.168.0.0/16
        for dns_record in records:
            if dns_record['content'][:8] == "192.168.":
                continue
            
            # Update each DNS record only if the IP for the
            # DNS is old OR we don't have record of old IP
            # AND the IP needs to be updated

            # This prevents unnecesary updates to DNS if it
            # was already updated to new IP
            if (dns_record['content'] == _last_ip or _last_ip == "") and dns_record['content'] != external_ip:
                Cloudflare_UpdateDNSRecord(_cloudflare_api_token, _cloudflare_zone_id, dns_record, external_ip)

        print("All Cloudflare DNS records up to date!")

# Log the time we completed this task
config[_config_section]['ip'] = external_ip
config[_config_section]['timestamp'] = _timestamp.strftime("%Y-%m-%d %H:%M:%S")

with open(_config_file_path, "w") as config_file:
    config.write(config_file)