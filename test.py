

import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import base64
from dotenv import load_dotenv
import os

load_dotenv()  # lê o .env e preenche as variáveis de ambiente

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Defina API_TOKEN no .env antes de rodar.")



def download_image(page_url: str) -> str:
    """Faz scraping da página e baixa a imagem, suportando data URIs e URLs."""
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    img_tag = soup.find("img")
    if not img_tag or not img_tag.get("src"):
        raise RuntimeError("Nenhuma imagem encontrada na página.")

    src = img_tag["src"]
    if src.startswith("data:image"):  # Data URI
        header, b64data = src.split(',', 1)
        mime = header.split(';')[0].split(':')[1]
        ext = mime.split('/')[-1]
        filename = f"scraped_image.{ext}"
        raw = base64.b64decode(b64data)
        with open(filename, 'wb') as f:
            f.write(raw)
        print(f"[✓] Imagem decodificada e salva: {filename}")
    else:
        img_url = urljoin(page_url, src)
        filename = os.path.basename(img_url)
        img_resp = requests.get(img_url)
        img_resp.raise_for_status()
        with open(filename, "wb") as f:
            f.write(img_resp.content)
        print(f"[✓] Imagem baixada via URL: {filename}")
    return filename


def infer_image(image_path: str, api_url: str) -> dict:
    """Envia a imagem codificada em base64 via JSON para o endpoint de chat completions."""
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    payload = {
        "model": "microsoft-florence-2-large",
        "messages": [
            {"role": "user", "content": "<DETAILED_CAPTION>"}
        ],
        "image": b64
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    print("[✓] Enviando imagem para inferência...")
    resp = requests.post(api_url, headers=headers, json=payload)
    resp.raise_for_status()
    result = resp.json()
    with open("response.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("[✓] Resposta de inferência salva em response.json")
    return result


def submit_response(result: dict, submit_url: str):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    print("[✓] Submetendo resposta para o endpoint...")
    resp = requests.post(submit_url, headers=headers, json=result)
    resp.raise_for_status()
    print(f"[✓] Submissão feita com sucesso: {resp.text}")


def main():
    scrape_url = "https://intern.aiaxuropenings.com/scrape/7b0f3950-50d8-4ac0-be41-4828d2c50cc9"
    inference_url = "https://intern.aiaxuropenings.com/v1/chat/completions"
    submission_url = "https://intern.aiaxuropenings.com/api/submit-response"

    try:
        image_file = download_image(scrape_url)
        result = infer_image(image_file, inference_url)
        submit_response(result, submission_url)
        print("🎉 Parte 1 concluída com sucesso. Agora atualize a página e envie o script.")
    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
