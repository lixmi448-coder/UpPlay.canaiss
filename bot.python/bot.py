import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Acessa o site
        await page.goto('https://famelack.com/tv/us/wviGS5VGRxTxKj')
        
        # O bot busca todos os botões com a classe 'video-link'
        canais = await page.query_selector_all('button.video-link')
        
        lista_final = {}

        for canal in canais:
            # Pega o nome e o link dos atributos
            nome = await canal.get_attribute('data-channel-name')
            link = await canal.get_attribute('data-video-url')
            
            if nome and link:
                lista_final[nome] = link
                print(f"Coletado: {nome}")

        # Garante que a pasta existe antes de salvar
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        # Salva o arquivo dentro da pasta canaisgringos.html
        with open('canaisgringos.html/canais.json', 'w') as f:
            json.dump(lista_final, f, indent=4)
            
        await browser.close()

asyncio.run(run())
