# Mistral API Rust Client Example

This is a simple Rust example demonstrating how to connect to the Mistral API using an API key.

## Prerequisites

1. Rust installed (https://www.rust-lang.org/tools/install)
2. Mistral API key (sign up at https://mistral.ai/)

## Setup

1. Set your Mistral API key as an environment variable:

```bash
export MISTRAL_API_KEY=your_api_key_here
```

Or create a `.env` file in this directory:

```bash
echo "MISTRAL_API_KEY=your_api_key_here" > .env
```

## Usage

Run the example with your prompt:

```bash
cargo run "Hello here is my question for le chat"
```

Or specify a different model:

```bash
cargo run "What is the capital of France?" --model mistral-small
```

Available models (check Mistral API for latest):
- `mistral-tiny` (default) - Fast and efficient
- `mistral-small` - More capable than tiny
- `mistral-medium` - Balanced performance

Note: Some models like `mistral-large` may require special access or different API endpoints.

## How it works

1. The program reads your `MISTRAL_API_KEY` from environment variables
2. It takes your prompt from command line arguments
3. Optionally accepts a `--model` flag to specify different Mistral models
4. Sends a POST request to Mistral's chat completions API
5. Prints the response from the AI

## Dependencies

- `ureq` - Simple HTTP client (no native dependencies)
- `serde`/`serde_json` - JSON serialization
- `dotenv` - Environment variable loading

## Notes

- This uses the `mistral-tiny` model by default
- The example handles basic errors but you may want to add more robust error handling for production use
