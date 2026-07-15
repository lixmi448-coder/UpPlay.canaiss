import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Agora a lista guarda o nome do país e o link dele
        paises = {
            "Estados Unidos": "https://famelack.com/tv/us/wviGS5VGRxTxKj",
            # Adicione outros países aqui no formato: "Nome": "URL"
        }
        
        # Esta lista vai organizar tudo por país
        dados_organizados = {}

        for nome_pais, url in paises.items():
            print(f"Coletando: {nome_pais}")
            await page.goto(url, timeout=60000)
            await asyncio.sleep(5) 
            
            canais = await page.query_selector_all('button.video-link')
            lista_canais = {}
            
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                link = await canal.get_attribute('data-video-url')
                if nome and link:
                    lista_canais[nome] = link
            
            dados_organizados[nome_pais] = lista_canais

        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w') as f:
            json.dump(dados_organizados, f, indent=4)
            
        await browser.close()

asyncio.run(run())
