import asyncio
from playwright.async_api import async_playwright
import json
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Acessa a página principal onde ficam os links dos países
        await page.goto('https://famelack.com/tv/') 
        
        # 2. Busca todos os links de países (ajuste o seletor se necessário)
        # Supondo que os links dos países estejam em elementos 'a' com uma classe específica
        # Se você não souber a classe, podemos tentar pegar todos os links que levam para /tv/
        links_paises = await page.eval_on_selector_all('a[href*="/tv/"]', 'elements => elements.map(e => e.href)')
        
        # Remove duplicatas e a própria página inicial da lista
        urls_paises = list(set([l for l in links_paises if '/tv/' in l and len(l.split('/')) > 5]))
        
        lista_final = {}

        for url in urls_paises:
            print(f"Acessando país: {url}")
            await page.goto(url)
            
            # Espera pelos botões dos canais
            await page.wait_for_selector('button.video-link', timeout=5000)
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
