# ZeroTierConnector

Interactive CLI that:

- selects a configured ZeroTier account
- fetches and caches authorized, recently-seen network members
- lets you refresh or select a member
- opens an SSH session to the member's first IPv4 address
- uses `click` for command-line interaction

## Setup

Use the project script:

```bash
./ZeroTierConnector.sh
```

The script will:
- install Poetry from the official online installer if missing
- install project dependencies with Poetry if needed
- install `sshpass` if missing (via `apt-get`)
- run `poetry run zerotier-connector`

To disable menu colors:

```bash
./ZeroTierConnector.sh --no-color
```

On first run, if `var/config.json` does not exist, the app creates it and exits.
Update that file, then run the script again:

```bash
./ZeroTierConnector.sh
```

## Config

`var/config.json` is loaded as JSON and should follow this structure:

```json
{
  "zerotier_uri": "https://api.zerotier.com/api/v1",
  "member_freshness_minutes": 5,
  "cache_ttl_minutes": 5,
  "accounts": [
    {
      "network_name": "example-network",
      "network_id": "0123456789abcdef",
      "api_token": "replace-with-token",
      "ssh_username": "ubuntu",
      "ssh_password": "",
      "ssh_key_path": "~/.ssh/id_ed25519",
      "ssh_port": 22
    }
  ]
}
```

Notes:
- Set at least one of `ssh_password` or `ssh_key_path` per account.
- If both are set, key auth is used first.
- Cache files are written in `var/`.
