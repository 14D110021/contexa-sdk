#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv('config/api_keys.env')
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-4o')

print("🔍 Testing OpenAI API Connection")
print("=" * 40)
print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")
print(f"Model: {model}")

client = OpenAI(api_key=api_key)

try:
    # First test with gpt-4o (known to work)
    print("\n🧪 Testing with gpt-4o...")
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': 'Hello, this is a test message. Please respond briefly.'}],
        max_tokens=20
    )
    print('✅ gpt-4o works!')
    print(f'Response: {response.choices[0].message.content}')
    
    # Now test with the configured model
    if model != 'gpt-4o':
        print(f"\n🧪 Testing with {model}...")
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': 'Hello, this is a test message. Please respond briefly.'}],
            max_tokens=20
        )
        print(f'✅ {model} works!')
        print(f'Response: {response.choices[0].message.content}')
    
except Exception as e:
    print(f'❌ API Error: {e}')
    if "gpt-4.1" in str(e):
        print("💡 Note: gpt-4.1 might not be a valid model name.")
        print("   Common models: gpt-4o, gpt-4, gpt-4-turbo, gpt-3.5-turbo")

print("\n🎯 API Test Complete!") 