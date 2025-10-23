import google.generativeai as genai

genai.configure(api_key="AIzaSyCqNgWqtIXCXAjEg-DUQzqbm0eu-qmmeoc")

for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)