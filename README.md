# monitor-ip
Monitors my external IP and updates Cloudflare if the zone ID and API token are specified

## Configuration
Uses a config.ini file to specify the zone ID and API token
This file will store the last external IP and the date and time it was captured
If the file does not exist then it will be created automatically when running the program

### Config file layout
```
[MONITOR-IP]
last_ip = Populated by program with external IP that was fetched when run
timestamp = Contains timestamp of last execution, in the format yyyy/MM/dd hh:mm:ss

[CLOUDFLARE]
zone_id = Can be found on the overview page of a domain, on the bottom right under "API"
api_token = Uses a token generated on Cloudflare to grant permissions to specific programs. See their documentation on how to create this. Needs permission to edit a zone's DNS
```

### IP log
Will create a file called "ip-log.txt" that stores if the IP has changed since the program was last run