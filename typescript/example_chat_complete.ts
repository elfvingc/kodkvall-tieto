import { Mistral } from '@mistralai/mistralai';

const apiKey = process.env.MISTRAL_API_KEY;

if (!apiKey) {
    console.error('Missing MISTRAL_API_KEY environment variable.');
    console.error('Example: export MISTRAL_API_KEY="..."');
    process.exit(1);
}

const client = new Mistral({ apiKey });

const chatResponse = await client.chat.complete({
    model: 'mistral-medium-latest',
    messages: [{ role: 'user', content: 'What is the best French cheese?' }],
});

// The response shape may evolve across SDK versions; printing the full object is the most robust.
console.dir(chatResponse, { depth: null });

// If the SDK returns OpenAI-like choices, this prints the first assistant message.
const firstChoiceContent = (chatResponse as any)?.choices?.[0]?.message?.content;
if (typeof firstChoiceContent === 'string') {
    console.log('\n---\n');
    console.log(firstChoiceContent);
}
