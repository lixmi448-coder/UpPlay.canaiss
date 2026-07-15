import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json
import os

# Função para testar link com mais tolerância
async def testar_link(session, url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}
        async with session.get(url, timeout=15, headers=headers) as response:
            return response.status in [200, 206]
    except:
        return False

async def run():
    async with async_playwright() as p:
        # Aumentamos o tempo de espera do navegador (browser launch)
        browser = await p.chromium.launch(headless=True)
        # Contexto com timeout maior para páginas pesadas
        context = await browser.new_context(navigation_timeout=60000)
        page = await context.new_page()
        
        print("Acessando site principal...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Garante que a lista de países carregue
        await page.wait_for_selector('.country-item', timeout=30000)
        items = await page.query_selector_all('.country-item')
        codigos_paises = [await item.get_attribute('data-country-code') for item in items]
        
        dados_organizados = {}
        connector = aiohttp.TCPConnector(limit=3) # Limitado para não bloquear o IP
        
        async with aiohttp.ClientSession(connector=connector) as session:
            for code in codigos_paises:
                url_pais = f"https://famelack.com/tv/{code}/"
                print(f"--- Processando país: {code.upper()} ---")
                
                # Nova tentativa (Retry) para cada país caso falhe
                for tentativa in range(3):
                    try:
                        await page.goto(url_pais, wait_until='networkidle')
                        # Espera extra garantida para elementos dinâmicos
                        await asyncio.sleep(8) 
                        
                        canais = await page.query_selector_all('button.video-link')
                        if not canais and tentativa < 2:
                            continue # Tenta de novo se não achar nada
                        
                        lista_canais = {}
                        for canal in canais:
                            nome = await canal.get_attribute('data-channel-name')
                            link = await canal.get_attribute('data-video-url')
                            
                            if nome and link:
                                # Verifica o link com mais calma
                                if await testar_link(session, link):
                                    lista_canais[nome] = link
                                    print(f"  [OK] {nome}")
                        
                        if lista_canais:
                            dados_organizados[code.upper()] = lista_canais
                        break # Sai do loop de tentativa se deu certo
                    except Exception as e:
                        print(f"Erro no país {code}: {e}. Tentativa {tentativa+1}")
                        await asyncio.sleep(10)

        # Salvando
        if not os.path.exists('canaisgringos.html'):
            os.makedirs('canaisgringos.html')

        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_organizados, f, indent=4, ensure_ascii=False)
            
        print("Varredura concluída com sucesso!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
