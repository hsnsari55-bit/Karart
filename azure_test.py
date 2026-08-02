from openai import OpenAI
import traceback

# BURAYI DOLDUR
API_KEY = "6hV5imLEiPKx72PbGJ3tA3EBvoz4tAypffbydJfsMGgIW8o9E7zsJQQJ99CGACfhMk5XJ3w3AAAAACOGrO5l"

# Azure Resource URL (deployment ekleme!)
BASE_URL = "https://hasans-5146-resource.openai.azure.com/openai/v1"

# Azure Deployment Name
MODEL = "gpt-5"

print("=" * 60)
print("Azure GPT-5 Test Başlıyor")
print("=" * 60)
print("Base URL :", BASE_URL)
print("Model    :", MODEL)
print("=" * 60)

try:
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    response = client.responses.create(
        model=MODEL,
        input="Sadece 'Test başarılı.' yaz."
    )

    print("\n✅ BAŞARILI\n")
    print(response.output_text)

except Exception as e:
    print("\n❌ HATA\n")
    traceback.print_exc()