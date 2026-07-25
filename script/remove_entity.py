
#!/usr/bin/env python3
import json

from websocket import create_connection

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0NTcwOWFjNTg2Njc0YjVmOTllYmYwMjk2ZTE3MDVmNyIsImlhdCI6MTc3ODI1ODQxMCwiZXhwIjoyMDkzNjE4NDEwfQ.cOXWLGzlWjCG1ohLCb1I-2kVVCFJrvACfi5egnQ1LSA"
HOST="homeassistant.sucicada.me:8123"

WS_URL = f"ws://{HOST}/api/websocket"

ENTITIES=[
  "sensor.windows_player_volume_2",
  "sensor.media_windows_is_muted_2",
  "sensor.media_windows_status_2",
]

ws = create_connection(WS_URL)
print(ws.recv())  # auth_required
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
print(ws.recv())  # auth_ok

for i, eid in enumerate(ENTITIES, 1):
    ws.send(json.dumps({
        "id": i,
        "type": "config/entity_registry/remove",
        "entity_id": eid,
    }))
    print(eid, ws.recv())

ws.close()