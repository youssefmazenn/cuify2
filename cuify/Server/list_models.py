import google.generativeai as genai

genai.configure(api_key="AIzaSyDsjsEvhKWlX80EFWM91L9_s2lxQRr15CY")

for model in genai.list_models():
    print(model.name, model.supported_generation_methods)
