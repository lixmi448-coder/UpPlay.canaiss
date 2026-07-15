import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Lista manual (adicione aqui todas as URLs dos países que você quer)
        urls_paises = [
            'https://famelack.com/tv/us/wviGS5VGRxTxKj',
            # Adicione aqui os outros links, por exemplo:
            # 'https://famelack.com/tv/br/link-do-brasil'
        ]
        
        lista_final = {}

        for url in urls_paises:
            try:
                print(f"Tentando acessar: {url}")
                await page.goto(url, timeout=60000)
                # Espera 5 segundos para garantir que o conteúdo carregou
                await asyncio.sleep(5) 
                
                canais = await page.query_selector_all('button.video-link')
                print(f"Encontrei {len(canais)} canais em {url}")
                
                for canal in canais:
                    nome = await canal.get_attribute('data-channel-name')
                    link = await canal.get_attribute('data-video-url')
                    if nome and link:
                        lista_final[nome] = link
            except Exception as e:
                print(f"Erro ao acessar {url}: {e}")

        # Salva o arquivo
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w') as f:
            json.dump(lista_final, f, indent=4)
            
        await browser.close()

asyncio.run(run())
