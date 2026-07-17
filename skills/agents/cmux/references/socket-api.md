# cmux Socket API — Full Reference

## Connecting

Socket path: `/tmp/cmux.sock` (release) or `/tmp/cmux-debug.sock` (debug)

```bash
# One-shot call
echo '{"id":"1","method":"workspace.list","params":{}}' | nc -U /tmp/cmux.sock

# Python
import socket, json

def cmux_call(method, params=None):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect('/tmp/cmux.sock')
    req = json.dumps({"id": "1", "method": method, "params": params or {}}) + '\n'
    sock.sendall(req.encode())
    resp = b''
    while not resp.endswith(b'\n'):
        resp += sock.recv(4096)
    sock.close()
    return json.loads(resp.strip())
```

## Access Mode

Default is `cmuxOnly` — only processes spawned by cmux can connect.

To allow any local process (e.g. running from a non-cmux terminal):
```bash
export CMUX_SOCKET_MODE=allowAll
# or set in cmux.json
```

## All Methods

### system.ping
```json
Request:  {"id":"1","method":"system.ping","params":{}}
Response: {"id":"1","ok":true,"result":{"pong":true}}
```

### system.capabilities
```json
{"id":"1","method":"system.capabilities","params":{}}
```

### system.identify
Returns current window, workspace, and surface IDs.
```json
{"id":"1","method":"system.identify","params":{}}
```

### workspace.list
```json
{"id":"1","method":"workspace.list","params":{}}
```

### workspace.create
```json
{"id":"1","method":"workspace.create","params":{}}
```

### workspace.select
```json
{"id":"1","method":"workspace.select","params":{"workspace_id":"uuid-here"}}
```

### workspace.current
```json
{"id":"1","method":"workspace.current","params":{}}
```

### workspace.close
```json
{"id":"1","method":"workspace.close","params":{"workspace_id":"uuid-here"}}
```

### surface.split
Directions: `left`, `right`, `up`, `down`
```json
{"id":"1","method":"surface.split","params":{"direction":"right"}}
```

### surface.list
```json
{"id":"1","method":"surface.list","params":{}}
```

### surface.focus
```json
{"id":"1","method":"surface.focus","params":{"surface_id":"uuid-here"}}
```

### surface.send_text
```json
// Focused surface
{"id":"1","method":"surface.send_text","params":{"text":"npm run dev\n"}}

// Specific surface
{"id":"1","method":"surface.send_text","params":{"surface_id":"uuid","text":"ls\n"}}
```

### surface.send_key
Keys: `enter`, `tab`, `escape`, `backspace`, `delete`, `up`, `down`, `left`, `right`
```json
{"id":"1","method":"surface.send_key","params":{"key":"enter"}}
{"id":"1","method":"surface.send_key","params":{"surface_id":"uuid","key":"escape"}}
```

### notification.create
```json
{"id":"1","method":"notification.create","params":{"title":"Done","subtitle":"Step 3","body":"All good"}}
```

### notification.list
```json
{"id":"1","method":"notification.list","params":{}}
```

### notification.clear
```json
{"id":"1","method":"notification.clear","params":{}}
```

## Sidebar (CLI-style strings, same socket)

Sidebar commands are plain strings (not JSON), sent terminated with newline:

```bash
set_status <key> <value> [--icon=<name>] [--color=<hex>] [--priority=<n>] [--tab=<uuid>]
clear_status <key> [--tab=<uuid>]
list_status [--tab=<uuid>]
set_progress <float 0.0-1.0> [--label=<text>] [--tab=<uuid>]
clear_progress [--tab=<uuid>]
log --level=<info|progress|success|warning|error> --source=<name> [--tab=<uuid>] -- <message>
clear_log [--tab=<uuid>]
list_log [--limit=<n>] [--tab=<uuid>]
sidebar_state [--tab=<uuid>]
```
