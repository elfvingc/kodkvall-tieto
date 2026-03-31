use std::env;
use mistralai_client::v1::client::Client;
use mistralai_client::v1::chat_completion::{ChatCompletionRequest, ChatCompletionResponse, ChatCompletionMessage, ChatCompletionMessageRole};

/// Parses command line arguments and returns (prompt, model)
fn parse_arguments() -> (String, String) {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: cargo run <your_prompt_here> [--model MODEL_NAME]");
        eprintln!("Example: cargo run \"Hello!\" --model mistral-small");
        std::process::exit(1);
    }

    let mut model = "mistral-tiny".to_string(); // default model
    let mut prompt_args = Vec::new();

    let mut i = 1;
    while i < args.len() {
        if args[i] == "--model" && i + 1 < args.len() {
            model = args[i + 1].clone();
            i += 2;
        } else {
            prompt_args.push(args[i].clone());
            i += 1;
        }
    }

    if prompt_args.is_empty() {
        eprintln!("Error: No prompt provided");
        std::process::exit(1);
    }

    (prompt_args.join(" "), model)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables from .env file if present
    dotenv::dotenv().ok();

    // Parse command line arguments
    let (prompt, model) = parse_arguments();
    println!("Sending prompt to Mistral AI (model: {}): {}", model, prompt);

    // Create Mistral client using SDK
    let client = Client::new(None, None, None, None);

    // Create chat completion request
    let request = ChatCompletionRequest {
        model,
        messages: vec![ChatCompletionMessage {
            role: ChatCompletionMessageRole::user,
            content: prompt,
        }],
        temperature: None,
        max_tokens: None,
        top_p: None,
        random_seed: None,
        stream: None,
        safe_prompt: None,
        tools: None,
    };

    // Send request using SDK
    let response: ChatCompletionResponse = client.chat(request)?;

    // Extract and print the response
    if let Some(choice) = response.choices.first() {
        println!("\nMistral's response:");
        println!("{}", choice.message.content);
    }

    Ok(())
}
