## Go example (mistral-go)

This folder contains a small Go program that calls Mistral's chat completion API using the third-party SDK `mistral-go`.

### Prerequisites

- Go 1.20+
- A Mistral API key available as `MISTRAL_API_KEY`

Example:

```bash
export MISTRAL_API_KEY="..."
```

### Install deps

```bash
cd go
go mod tidy
```

### Run

```bash
go run example.go
```

### Notes

- If you see “Missing MISTRAL_API_KEY…”, the environment variable is not set in your shell/session.
- The examples default to `mistral-medium-latest`; for cheaper testing you can switch the model to `mistral-small-latest`.

### Docs

- mistral-go: https://github.com/Gage-Technologies/mistral-go
- Mistral clients overview: https://docs.mistral.ai/getting-started/clients
- SDKs tab (incl. third-party SDKs): https://docs.mistral.ai/getting-started/clients?tab=third-party-sdks#explorer-tabs-sdks
