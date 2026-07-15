import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json
import os

# Função ajustada com tempo de espera maior
async def testar_link(session, url):
    try:
        # Aumentamos o timeout para 10 segundos conforme você pediu
        # Usamos um cabeçalho (headers) para parecer um navegador real
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        async with session.head(url, timeout=10, headers=headers) as response:
            # Muitos servidores de streaming respondem com 200 (OK)
            # Alguns podem responder com 206 (Partial Content), que também indica que o link funciona
            return response.status in [200, 206]
    except Exception as e:
        return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://famelack.com/tv/')
        await page.wait_for_selector('.country-item')
        
        items = await page.query_selector_all('.country-item')
        codigos_paises = [await item.get_attribute('data-country-code') for item in items]
        
        dados_organizados = {}
        
        # Aumentamos o limite de conexões simultâneas para não travar
        connector = aiohttp.TCPConnector(limit=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            for code in codigos_paises:
                url_pais = f"https://famelack.com/tv/{code}/"
                print(f"Verificando país: {code}")
                
                await page.goto(url_pais)
                await asyncio.sleep(5) # Espera extra para renderizar a lista do país
                
                canais = await page.query_selector_all('button.video-link')
                lista_canais = {}
                
                for canal in canais:
                    nome = await canal.get_attribute('data-channel-name')
                    link = await canal.get_attribute('data-video-url')
                    
                    if nome and link:
                        if await testar_link(session, link):
                            lista_canais[nome] = link
                        else:
                            print(f"Link offline ou muito lento: {nome}")
                
                if lista_canais:
                    dados_organizados[code.upper()] = lista_canais
                    print(f"Sucesso: {len(lista_canais)} canais ativos em {code}")

        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_organizados, f, indent=4, ensure_ascii=False)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
