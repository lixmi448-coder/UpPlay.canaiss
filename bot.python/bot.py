import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        # Iniciando o navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Lista com as URLs que você quer coletar
        urls_paises = [
            'https://famelack.com/tv/us/wviGS5VGRxTxKj',
            # Adicione aqui as outras URLs conforme você for pegando
        ]
        
        lista_final = {}

        for url in urls_paises:
            print(f"Acessando: {url}")
            await page.goto(url)
            
            # ESPERA: Garantimos que pelo menos um botão apareça antes de continuar
            try:
                await page.wait_for_selector('button.video-link', timeout=10000)
            except:
                print(f"Tempo esgotado ou nada encontrado em: {url}")
                continue

            # Agora busca todos os botões
            canais = await page.query_selector_all('button.video-link')
            
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                link = await canal.get_attribute('data-video-url')
                
                if nome and link:
                    lista_final[nome] = link
            
            print(f"Coletados {len(canais)} canais nesta página.")

        # Salva o arquivo
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w') as f:
            json.dump(lista_final, f, indent=4)
            
        await browser.close()

asyncio.run(run())
