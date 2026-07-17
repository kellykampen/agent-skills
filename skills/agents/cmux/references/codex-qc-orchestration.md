# Multi-Agent Orchestration via cmux

How to orchestrate coding and QC agents via cmux. The **orchestrator** (whichever agent is in this role — could be Claude, another Claude instance, or any other agent) routes all work to specialist panes and never does the work itself.

## cmux socket

`/Users/greg/.local/state/cmux/cmux-501.sock`

## Roles — never mix up

- **Orchestrator** = planner and router ONLY. Writes specs, sends to the right agent, reads results, reports to user. Never writes code. Never does browser QC.
- **Coding agent pane** = the agent doing implementation. Could be Codex, Claude Code CLI (`ccc`), or any other agent. Writes code, runs `pnpm astro check`, pushes Convex schema.
- **QC agent pane** = the agent doing verification. Checks the browser, design quality, reports PASS/FAIL per item.

The agent *type* in each pane is determined by what the user says at session start, or by reading the pane tail to identify it. The orchestrator adapts — it doesn't assume Codex is always coding.

## Discovering surface IDs

Never assume surface IDs are the same across sessions — they can change on restart. Discover at session start:

```python
import socket, json, time

SOCK = '/Users/greg/.local/state/cmux/cmux-501.sock'

def call(method, params):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.sendall((json.dumps({'id':'1','method':method,'params':params})+'\n').encode())
    time.sleep(0.5)
    chunks = []
    s.settimeout(2)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            chunks.append(chunk)
    except: pass
    s.close()
    return json.loads(b''.join(chunks))

# List surfaces to identify which pane is which
surfaces = call('surface.list', {})
for s in surfaces['result']['surfaces']:
    tail = call('surface.read_text', {'surface_id': s['surface_id']}).get('result',{}).get('text','')[-200:]
    print(s['surface_id'], ':', tail.replace('\n',' '))
```

Known surface IDs for current SIP session (verify on new session):

| Role                 | Surface ID                             |
| -------------------- | -------------------------------------- |
| Coding agent (Codex) | `21914308-0823-4B80-8D7A-11A7E44853EE` |
| QC agent             | `C4E3431A-3A54-47A1-9F45-CEFBCCC50BE2` |

## The Orchestration Loop

1. Orchestrator writes a clear spec → sends to coding agent (`surface.send_text` + `surface.send_key enter`)
2. Monitor coding agent until idle OR it sends a completion notification
3. If agent hits a permission prompt → send `"p"` + enter to approve
4. Read coding agent output — confirm what was built, confirm 0 errors
5. Send strict QC brief to QC pane
6. Monitor QC until it produces a PASS/FAIL report
7. If **all PASS** → report to user, done
8. If **any FAIL** → send specific fix instructions to coding agent (not the orchestrator), go back to step 2
9. Repeat until all PASS

## Reading panes (chunked — avoid JSON truncation)

```python
def call(method, params):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.sendall((json.dumps({'id':'1','method':method,'params':params})+'\n').encode())
    time.sleep(0.5)
    chunks = []
    s.settimeout(2)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            chunks.append(chunk)
    except: pass
    s.close()
    return json.loads(b''.join(chunks))

text = call('surface.read_text', {'surface_id': SURFACE_ID}).get('result',{}).get('text','')
tail = text[-2000:]
```

## Detecting idle vs working

| State                 | Indicators in tail                                                    |
| --------------------- | --------------------------------------------------------------------- |
| **Idle**              | Contains `❯` or `›`, does NOT contain `esc to interrupt` or `Working` |
| **Permission prompt** | Contains `confirm or esc to cancel`                                   |
| **Still working**     | Anything else                                                         |

Approve permission prompts by sending `"p"` + enter.

## Sending to a pane (two-step — mandatory)

```python
call('surface.send_text', {'surface_id': SURFACE, 'text': 'your message here'})
time.sleep(0.3)
call('surface.send_key', {'surface_id': SURFACE, 'key': 'enter'})
```

## Agent completion notifications

Ask the coding agent to notify the orchestrator when done by appending this to every brief:

```
When you finish, run this to notify the orchestrator:

python3 -c "
import json, socket
SOCK = '/Users/greg/.local/state/cmux/cmux-501.sock'
ORCH = 'ORCHESTRATOR_SURFACE_ID'
def call(m,p):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(SOCK)
    s.sendall((json.dumps({'id':'1','method':m,'params':p})+chr(10)).encode())
    s.recv(4096); s.close()
call('surface.send_text',{'surface_id':ORCH,'text':'AGENT_DONE: one-line summary'})
call('surface.send_key',{'surface_id':ORCH,'key':'enter'})
"
```

The orchestrator's own surface ID is available as `$CMUX_SURFACE_ID` in its shell environment.

## QC brief standards

The QC agent must always:
- Test in the actual browser (claude-in-chrome tools)
- Check design quality explicitly — "does it look polished and professional" not just "does it work"
- Test mobile at 390px width
- Submit real test data (actual form submissions) to verify end-to-end flows
- Run `pnpm astro check` — confirm 0 errors
- Report **PASS or FAIL** for every item with specific observations in a table

## Hard rules for the orchestrator (regardless of which agent is orchestrating)

- **NEVER write code** — send it to the coding agent
- **NEVER do browser QC** — send it to the QC pane
- **NEVER tell the user something passed** unless the QC agent has explicitly reported PASS
- **NEVER leave agents idle** — always have the next task queued
- **ALWAYS monitor** with a polling loop — never guess at completion
- **Approve prompts** with `"p"` + enter when the coding agent waits for confirmation
