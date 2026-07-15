import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Acessamos a página inicial (ajuste para a URL que lista todos os países)
        # Se a página inicial lista todos, use ela. Se não, precisaremos de uma lista de URLs.
        await page.goto('https://famelack.com/tv/') 
        
        # 2. Aqui você teria que selecionar os links de cada país primeiro
        # Exemplo hipotético (ajuste conforme o site):
        # links_paises = await page.eval_on_selector_all('.link-pais', 'elements => elements.map(e => e.href)')
        
        lista_final = {}

        # 3. Se você quiser apenas manter seu formato atual, o ideal é criar uma lista de URLs:
        urls_paises = [
            'https://famelack.com/tv/us/wviGS5VGRxTxKj',
            'https://famelack.com/tv/br/link-do-brasil-aqui',
            # Adicione aqui os links dos outros países que você quer
        ]

        for url in urls_paises:
            await page.goto(url)
            canais = await page.query_selector_all('button.video-link')
            
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                link = await canal.get_attribute('data-video-url')
                if nome and link:
                    lista_final[nome] = link

        # Salva o arquivo
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w') as f:
            json.dump(lista_final, f, indent=4)
            
        await browser.close()

asyncio.run(run())
