import os
from openai import OpenAI

class queryOpenAPI:
    def __init__(self, config, logger):
        logger.info(f'OpenAPI Object Created')
        self.openAPI_key=config['openAI_API_Key']
        self.openAPI_org=config['openAi_API_OrgID']
    def summarizeSigmaRule(self, sigmaRule):
        # Create the prompt to send to ChatGPT

        client = OpenAI(
            organization=self.openAPI_org,
            #project='$PROJECT_ID',
            # This is the default and can be omitted
            api_key=self.openAPI_key
        )
        prompt = f"Summarize the following Sigma Rule:\n\n{sigmaRule}"

        # Make a request to the OpenAI API
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "max_tokens": 50,
                    "temperature": 0
                }
            ],
            model="gpt-3.5-turbo",
        )
        for choice in response.choices:
            return choice.message.content.strip()