import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://famelack.com/tv/')
        await page.wait_for_selector('.country-item')

        # Captura todos os códigos de países da lista
        items = await page.query_selector_all('.country-item')
        codigos_paises = [await item.get_attribute('data-country-code') for item in items]
        
        dados_organizados = {}

        for code in codigos_paises:
            # Constrói a URL baseada no código do país
            url_pais = f"https://famelack.com/tv/{code}/"
            print(f"Coletando país: {code}")
            
            await page.goto(url_pais)
            await asyncio.sleep(3) # Espera carregar os canais daquele país
            
            # Coleta os canais desta página específica
            canais = await page.query_selector_all('button.video-link')
            lista_canais = {}
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                link = await canal.get_attribute('data-video-url')
                if nome and link:
                    lista_canais[nome] = link
            
            if lista_canais:
                dados_organizados[code.upper()] = lista_canais
                print(f"Sucesso: {len(lista_canais)} canais em {code}")

        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_organizados, f, indent=4, ensure_ascii=False)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
