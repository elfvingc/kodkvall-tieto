package main

import (
	"fmt"
	"log"
	"os"

	mistral "github.com/gage-technologies/mistral-go"
)

func main() {
	apiKey := os.Getenv("MISTRAL_API_KEY")
	if apiKey == "" {
		log.Fatal("Missing MISTRAL_API_KEY environment variable")
	}

	client := mistral.NewMistralClientDefault(apiKey)
	model := mistral.ModelMistralMediumLatest

	chatRes, err := client.Chat(model, []mistral.ChatMessage{
		{Role: mistral.RoleUser, Content: "What is the best French cheese?"},
	}, nil)
	if err != nil {
		log.Fatalf("Error getting chat completion: %v", err)
	}

	fmt.Printf("Chat completion (full response): %+v\n", chatRes)

	if chatRes != nil && len(chatRes.Choices) > 0 {
		fmt.Println(chatRes.Choices[0].Message.Content)
	}
}
