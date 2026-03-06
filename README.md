# server👑crown 

A self-hosted control plane for managing all your servers from a single dashboard.

ServerCrown uses an **agent-based architecture**: install a lightweight agent on each server, and manage everything from a central web hub — real-time metrics, web terminal, command execution, and alerts.

## How It Works

```
                        ┌──────────────────────────────┐
                        │        ServerCrown (Crown)       │
                        │                              │
                        │  ┌────────┐  ┌────────────┐  │
                        │  │  Web   │  │  Backend    │  │
                        │  │  UI    │  │  API        │  │
                        │  └───┬────┘  └─────┬──────┘  │
                        │      │             │         │
                        │      └──────┬──────┘         │
                        │             │                │
                        │       ┌─────┴─────┐          │
                        │       │ WebSocket │          │
                        │       │  Server   │          │
                        │       └─────┬─────┘          │
                        │             │                │
                        └─────────────┼────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
              ┌─────┴─────┐    ┌─────┴─────┐     ┌─────┴─────┐
              │  Agent A  │    │  Agent B  │     │  Agent C  │
              │ (server1) │    │ (server2) │     │ (server3) │
              └───────────┘    └───────────┘     └───────────┘
```

- The **agent** is a single binary that runs on each target server. It collects system metrics, sends heartbeats, and executes commands received from the hub.
- The **hub** is a web app where you see all your servers, their health, and interact with them.

The agent connects **outbound** to the hub — no inbound ports needed on your servers.

## Features

- **Real-time dashboard** — live CPU, RAM, disk, and network metrics from all servers
- **Web terminal** — full interactive shell in the browser, no SSH client needed
- **Command execution** — run commands on one or many servers at once
- **Saved snippets** — predefined commands for common operations
- **Alerts** — get notified when a server goes down or resources hit thresholds
- **Agent enrollment** — add a server with a single command
- **Self-hosted** — your data stays on your infrastructure

## Quick Start

### 1. Deploy the Hub

```bash
docker compose up -d
```

### 2. Add a Server

Open the hub UI, create a new server, and copy the enrollment command:

```bash
curl -sSL https://your-hub/install.sh | bash -s -- --token <enrollment-token>
```

The agent installs itself, connects to the hub, and your server appears on the dashboard.

## Architecture

| Component | Tech | Role |
|-----------|------|------|
| Agent | Go | Metrics collection, command execution, PTY proxy |
| Hub Backend | Django + Django Channels | Views, WebSocket server, agent management |
| Hub Frontend | htmx + Tailwind | Reactive server-rendered UI, dashboard, administration |
| Database | SQLite / PostgreSQL | Server registry, metrics, configuration |
| Terminal | xterm.js | Browser-based interactive shell (only JS dependency) |

## Security

- Agents authenticate with the hub via API keys issued during enrollment.
- All communication is encrypted over WebSocket + TLS.
- The agent runs as an unprivileged user; sudo escalation is opt-in.
- No SSH keys are stored on the hub — the agent model eliminates that need.
- All executed commands are logged for audit.

See [WHITEPAPER.md](WHITEPAPER.md) for the full technical design.

## Roadmap

- [x] Project design and whitepaper
- [ ] Agent: heartbeat + metrics + WebSocket connection
- [ ] Hub: server registry + enrollment + dashboard
- [ ] Web terminal
- [ ] Multi-server command execution
- [ ] Alert engine + notifications
- [ ] Agent auto-update

## License

MIT
