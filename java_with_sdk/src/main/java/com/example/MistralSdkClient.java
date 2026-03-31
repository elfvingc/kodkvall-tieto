package com.example;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.mistralai.MistralAiChatModel;
import io.github.cdimascio.dotenv.Dotenv;

import java.util.Arrays;

/**
 * Professional Java client using LangChain4j SDK for Mistral AI
 * Demonstrates modern AI integration patterns
 */
public class MistralSdkClient {

    // Parse command line arguments
    static class Arguments {
        String prompt;
        String model = "mistral-tiny"; // default model

        public Arguments(String[] args) {
            if (args.length < 1) {
                System.err.println("Usage: java MistralSdkClient <prompt> [--model MODEL_NAME]");
                System.err.println("Example: java MistralSdkClient \"Hello!\" --model mistral-small");
                System.exit(1);
            }

            // Parse arguments
            for (int i = 0; i < args.length; i++) {
                if (args[i].equals("--model") && i + 1 < args.length) {
                    this.model = args[i + 1];
                    i++; // skip next argument
                } else {
                    if (this.prompt == null) {
                        this.prompt = args[i];
                    } else {
                        this.prompt += " " + args[i];
                    }
                }
            }

            if (this.prompt == null || this.prompt.isEmpty()) {
                System.err.println("Error: No prompt provided");
                System.exit(1);
            }
        }
    }

    public static void main(String[] args) {
        try {
            // Parse arguments
            Arguments arguments = new Arguments(args);
            System.out.println("Sending prompt to Mistral AI (model: " + arguments.model + ")");

            // Load API key from environment
            Dotenv dotenv = Dotenv.load();
            String apiKey = dotenv.get("MISTRAL_API_KEY");

            if (apiKey == null || apiKey.isEmpty()) {
                System.err.println("Error: MISTRAL_API_KEY environment variable not set");
                System.exit(1);
            }

            // Create Mistral AI chat model using LangChain4j SDK
            ChatLanguageModel model = MistralAiChatModel.builder()
                    .apiKey(apiKey)
                    .modelName(arguments.model)
                    .build();

            // Send prompt and get response
            String response = model.generate(arguments.prompt);

            // Print the response
            System.out.println("\nMistral's response:");
            System.out.println(response);

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            if (e.getMessage().contains("400") || e.getMessage().contains("Invalid model")) {
                System.err.println("Note: The specified model might not be available.");
                System.err.println("Try common models like: mistral-tiny, mistral-small, mistral-medium");
            }
            System.exit(1);
        }
    }
}
