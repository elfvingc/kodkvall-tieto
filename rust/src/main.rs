use std::env;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize)]
struct MistralRequest {
    model: String,
    messages: Vec<Message>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct MistralResponse {
    choices: Vec<Choice>,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: Message,
}

/// Parses command line arguments and returns (prompt, model)
fn parse_arguments() -> (String, String) {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: cargo run <your_prompt_here> [--model MODEL_NAME]");
        eprintln!("Example: cargo run \"Hello!\" --model mistral-small");
        std::process::exit(1);
    }

    let mut model = "mistral-tiny".to_string();
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

/// Creates the API request structure
fn create_request(prompt: String, model: String) -> MistralRequest {
    MistralRequest {
        model,
        messages: vec![
            Message {
                role: "user".to_string(),
                content: prompt,
            }
        ],
    }
}

/// Sends the request to Mistral API and handles errors
fn send_to_mistral_api(
    request: MistralRequest,
    api_key: &str,
    model: &str,
) -> Result<MistralResponse, Box<dyn std::error::Error>> {
    let response = match ureq::post("https://api.mistral.ai/v1/chat/completions")
        .set("Authorization", &format!("Bearer {}", api_key))
        .set("Content-Type", "application/json")
        .send_json(ureq::json!(request)) {
        Ok(resp) => resp,
        Err(ureq::Error::Status(code, resp)) => {
            let error_body: serde_json::Value = resp.into_json().unwrap_or_else(|_| {
                eprintln!("Failed to parse error response");
                serde_json::json!({"message": "Unknown API error"})
            });
            eprintln!("API Error {}: {}", code, error_body.get("message").unwrap_or(&serde_json::Value::String("Unknown error".to_string())));
            if code == 400 {
                eprintln!("Note: The model '{}' might not be available or requires different access.", model);
                eprintln!("Try common models like: mistral-tiny, mistral-small, mistral-medium");
            }
            std::process::exit(1);
        }
        Err(e) => return Err(e.into()),
    };

    Ok(response.into_json()?)
}

/// Prints the response from Mistral API
fn print_response(response: MistralResponse) {
    if let Some(choice) = response.choices.first() {
        println!("\nMistral's response:");
        println!("{}", choice.message.content);
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables from .env file if present
    dotenv::dotenv().ok();

    // Get API key from environment
    let api_key = env::var("MISTRAL_API_KEY")
        .expect("MISTRAL_API_KEY environment variable not set");

    // Parse command line arguments
    let (prompt, model) = parse_arguments();
    println!("Sending prompt to Mistral API (model: {}): {}", model, prompt);

    // Create and send request
    let request = create_request(prompt.clone(), model.clone());
    let response = send_to_mistral_api(request, &api_key, &model)?;

    // Print the response
    print_response(response);

    Ok(())
}
