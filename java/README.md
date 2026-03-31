# Mistral API Java Client Example

This is a simple Java example demonstrating how to connect to the Mistral AI API using an API key.

## Prerequisites

1. Java 11 or higher installed
2. Maven installed
3. Mistral API key (sign up at https://mistral.ai/)

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

First, build the project:

```bash
mvn clean package
```

Then run with your prompt:

```bash
java -jar target/mistral-client-1.0-SNAPSHOT.jar "What is the best french cheese?"
```

Or specify a different model:

```bash
java -jar target/mistral-client-1.0-SNAPSHOT.jar "What is the capital of France?" --model mistral-small
```

## Available Models

- `mistral-tiny` (default) - Fast and efficient
- `mistral-small` - More capable than tiny
- `mistral-medium` - Balanced performance

Note: Please use the smallest model for testing to conserve API credits.

## How it works

1. The program reads your `MISTRAL_API_KEY` from environment variables
2. It parses command line arguments for your prompt and optional model
3. Sends a POST request to Mistral's chat completions API
4. Prints the response from the AI

## Dependencies

- Apache HttpClient - HTTP client
- Jackson - JSON processing
- Java Dotenv - Environment variable loading

## Project Structure

- `pom.xml` - Maven build configuration
- `src/main/java/com/example/MistralClient.java` - Main application code

