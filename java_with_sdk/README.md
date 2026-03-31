# Mistral AI Java SDK Client

Java example using LangChain4j SDK for Mistral AI API.

**Documentation:** https://github.com/langchain4j/langchain4j

## Usage

```bash
# Build
mvn clean package

# Run with default model (mistral-tiny)
java -jar target/mistral-sdk-client-1.0-SNAPSHOT.jar "Your prompt here"

# Run with specific model
java -jar target/mistral-sdk-client-1.0-SNAPSHOT.jar "Your prompt here" --model mistral-small
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
