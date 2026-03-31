## TypeScript examples (Mistral SDK)

This folder contains a small script that calls Mistral's chat API using the official TypeScript SDK.

### Prerequisites

- Node.js (18+ recommended)
- A Mistral API key available as `MISTRAL_API_KEY`

Example:

```bash
export MISTRAL_API_KEY="..."
```

### Install

```bash
cd typescript
npm install
```

### Run the chat completion example

```bash
npm run example:chat
```

### Notes

- If you see “Missing MISTRAL_API_KEY…”, the environment variable is not set in your shell/session.
- The example prints the whole response object first, then (if present) prints the first assistant message.

### Docs

- Mistral clients overview: https://docs.mistral.ai/getting-started/clients
- SDKs tab (TypeScript SDK): https://docs.mistral.ai/getting-started/clients?tab=typescript-sdk#explorer-tabs-sdks
- More TypeScript examples: https://github.com/mistralai/client-js/tree/main/examples
