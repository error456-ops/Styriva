from openai import OpenAI
from STYRIVA.settings import OPENAI_API_KEY

print("KEY LOADED:", bool(OPENAI_API_KEY))

client = OpenAI(api_key=OPENAI_API_KEY)

try:
    model = client.models.retrieve("gpt-5.6-terra")

    print("\nYES! GPT-5.6 Terra is available!")
    print(model)

except Exception as e:
    print("\nGPT-5.6 Terra test failed:")
    print(type(e).__name__)
    print(e)