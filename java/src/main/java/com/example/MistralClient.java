package com.example;

import io.github.cdimascio.dotenv.Dotenv;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Simple Java client for Mistral AI API
 */
public class MistralClient {

    // Request structure
    static class MistralRequest {
        public String model;
        public List<Message> messages;

        public MistralRequest(String model, String prompt) {
            this.model = model;
            this.messages = List.of(new Message("user", prompt));
        }
    }

    // Message structure
    static class Message {
        public String role;
        public String content;

        public Message(String role, String content) {
            this.role = role;
            this.content = content;
        }
    }

    // Parse command line arguments
    static class Arguments {
        String prompt;
        String model;

        public Arguments(String[] args) {
            if (args.length < 1) {
                System.err.println("Usage: java MistralClient <prompt> [--model MODEL_NAME]");
                System.err.println("Example: java MistralClient \"Hello!\" --model mistral-small");
                System.exit(1);
            }

            this.model = "mistral-tiny"; // default model
            List<String> promptParts = new ArrayList<>();

            for (int i = 0; i < args.length; i++) {
                if (args[i].equals("--model") && i + 1 < args.length) {
                    this.model = args[i + 1];
                    i++; // skip next argument
                } else {
                    promptParts.add(args[i]);
                }
            }

            if (promptParts.isEmpty()) {
                System.err.println("Error: No prompt provided");
                System.exit(1);
            }

            this.prompt = String.join(" ", promptParts);
        }
    }

    public static void main(String[] args) {
        try {
            // Parse arguments
            Arguments arguments = new Arguments(args);
            System.out.println("Sending prompt to Mistral API (model: " + arguments.model + ")");

            // Load API key from environment
            Dotenv dotenv = Dotenv.load();
            String apiKey = dotenv.get("MISTRAL_API_KEY");

            if (apiKey == null || apiKey.isEmpty()) {
                System.err.println("Error: MISTRAL_API_KEY environment variable not set");
                System.exit(1);
            }

            // Create request
            MistralRequest request = new MistralRequest(arguments.model, arguments.prompt);

            // Convert to JSON
            ObjectMapper mapper = new ObjectMapper();
            String requestJson = mapper.writeValueAsString(request);

            // Send request to Mistral API
            try (CloseableHttpClient httpClient = HttpClients.createDefault()) {
                HttpPost httpPost = new HttpPost("https://api.mistral.ai/v1/chat/completions");
                httpPost.setHeader("Authorization", "Bearer " + apiKey);
                httpPost.setHeader("Content-Type", "application/json");
                httpPost.setEntity(new StringEntity(requestJson));

                HttpResponse response = httpClient.execute(httpPost);
                int statusCode = response.getStatusLine().getStatusCode();

                if (statusCode == 200) {
                    String responseBody = EntityUtils.toString(response.getEntity());
                    JsonNode rootNode = mapper.readTree(responseBody);

                    // Extract and print the response
                    JsonNode choices = rootNode.path("choices");
                    if (choices.isArray() && choices.size() > 0) {
                        JsonNode firstChoice = choices.get(0);
                        JsonNode message = firstChoice.path("message");
                        String content = message.path("content").asText();

                        System.out.println("\nMistral's response:");
                        System.out.println(content);
                    }
                } else {
                    String errorBody = EntityUtils.toString(response.getEntity());
                    JsonNode errorNode = mapper.readTree(errorBody);
                    String errorMessage = errorNode.path("message").asText("Unknown API error");

                    System.err.println("API Error " + statusCode + ": " + errorMessage);
                    if (statusCode == 400) {
                        System.err.println("Note: The model '" + arguments.model + "' might not be available or requires different access.");
                        System.err.println("Try common models like: mistral-tiny, mistral-small, mistral-medium");
                    }
                    System.exit(1);
                }
            }

        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            System.exit(1);
        }
    }
}
