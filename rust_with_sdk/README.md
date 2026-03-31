# Mistral AI Rust SDK Client

Professional Rust example using the official Mistral Rust SDK.

**Documentation:** https://github.com/ivangabriele/mistralai-client-rs

## Usage

```bash
# Run with default model (mistral-tiny)
cargo run "How to say crab emoji in text"

# Run with specific model
cargo run "Give ascii art crab emoji" --model mistral-small
```

## Setup

Set your API key:
```bash
export MISTRAL_API_KEY=your_api_key_here
```

Or create `.env` file:
```bash
echo "MISTRAL_API_KEY=your_api_key_here" > .env
```
