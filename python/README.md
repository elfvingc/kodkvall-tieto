## Python examples (Mistral SDK)

This folder contains two small scripts that call Mistral's chat API. The scripts are split by **major version** of the `mistralai` Python SDK.

### Prerequisites

- Python (any reasonably recent 3.x)
- A Mistral API key available as `MISTRAL_API_KEY`

Optional but recommended: use a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

Example:

```bash
export MISTRAL_API_KEY="..."
```

### Choose the SDK version

Pick **one** of the options below (the imports differ between major versions):

#### Option A: SDK v2 (preferred)

```bash
pip install mistralai
python example_v2.py
```

#### Option B: SDK v1

```bash
pip install "mistralai<2"
python example_v1.py
```

### Notes

- If you see `KeyError: 'MISTRAL_API_KEY'`, the environment variable is not set in your shell/session.
- The examples currently create a response object; to display the answer, print the relevant field(s) from `chat_response`.

### Docs

- Mistral clients overview: https://docs.mistral.ai/getting-started/clients
- SDKs tab (incl. third-party SDKs): https://docs.mistral.ai/getting-started/clients?tab=third-party-sdks#explorer-tabs-sdks
- More Python examples: https://github.com/mistralai/client-python/tree/main/examples