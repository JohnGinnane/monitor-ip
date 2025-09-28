# monitor-ip
Monitors my external IP and updates cloudflare accordingly

## Configuration
Uses a config.ini file to specify the zone ID and API token
This file will store the last external IP and the date and time it was capture
If the file does not exist then it will be created automatically when running the program

### Required
```
[IP-MONITOR]
zone_id = [Required] Can be found on the overview page of a domain, on the bottom right under "API"

api_token = [Required] Uses a token generated on Cloudflare to grant permissions to specific programs. See their documentation on how to create this. Needs permission to edit a zone's DNS

last_ip = Populated by program with external IP that was fetch when run

timestamp = Contains timestamp of last execution, in the format yyyy/MM/dd hh:mm:ss
```