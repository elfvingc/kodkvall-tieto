# Browser Chat with Mistral API

This is a simple browser-based chat application that demonstrates how to interact with the Mistral API using pure JavaScript.

## Features

- Simple HTML/CSS/JavaScript implementation
- No framework dependencies
- Clean, responsive UI
- Typing indicators for better UX
- Easy to extend and modify

## Getting Started

1. **Replace the API key**: Open `chat.js` and replace `YOUR_MISTRAL_API_KEY` with your actual Mistral API key.

2. **Open in browser**: Simply open the `index.html` file in any modern web browser.

3. **Start chatting**: Type your message and press Enter or click the Send button.

## Files

- `index.html` - The main HTML file with basic styling
- `chat.js` - The JavaScript file containing all the chat logic
- `README.md` - This file

## Customization

You can easily customize this chat application:

- **Change the model**: In `chat.js`, modify the `model` parameter in the API call
- **Adjust parameters**: Change `temperature`, `max_tokens`, etc. in the API call
- **Modify UI**: Edit the CSS in `index.html` to change colors, layout, etc.
- **Add features**: Extend the JavaScript to add message history, themes, or other functionality

## Important Notes

- This is a client-side application, so your API key will be visible in the JavaScript code. For production use, consider using a backend proxy.
- The application uses the browser's Fetch API to communicate with Mistral's API.
- CORS restrictions may apply depending on your environment.

## License

This example is provided as-is and is part of the kodkvall-tieto repository.