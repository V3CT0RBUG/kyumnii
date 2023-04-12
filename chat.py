import openai
import cred


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


openai.api_key = cred.openai_token
openai.api_base = 'https://api.openai.com/v1'


def gpt3_completion(prompt, engine='text-curie-001', temp=1.0, tokens=400, freq_pen=2.0, pres_pen=2.0, stop=['Kyumnii:', 'Chatter:']):
    response = openai.Completion.create(
        model=engine,
        prompt=prompt,
        temperature=temp,
        max_tokens=tokens,
        frequency_penalty=freq_pen,
        presence_penalty=pres_pen,
        stop=stop)
    text = response['choices'][0]['text'].strip()
    return text