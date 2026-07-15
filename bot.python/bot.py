import asyncio
import aiohttp
import json
import os
from playwright.async_api import async_playwright

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

async def testar_link(session, url):
    try:
        async with session.get(url, timeout=8, headers=HEADERS) as response:
            return response.status in [200, 206, 301, 302]
    except:
        return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(">>> Iniciando varredura com mecanismo de persistência...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        dados_finais = {}
        
        # Loop de varredura: continua enquanto novos países forem encontrados
        while True:
            # 1. Scroll forçado para garantir que novos países apareçam
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(3000) 
            
            # Coleta todos os países presentes no momento
            itens_pais = await page.query_selector_all('.country-item')
            codigos = [await item.get_attribute('data-country-code') for item in itens_pais if await item.get_attribute('data-country-code')]
            
            novos_paises = [c for c in codigos if c.upper() not in dados_finais]
            
            if not novos_paises:
                print(">>> Todos os países foram processados.")
                break
                
            print(f">>> Encontrados {len(novos_paises)} novos países para processar...")

            async with aiohttp.ClientSession() as session:
                for code in novos_paises:
                    print(f"-> Processando País: {code.upper()}")
                    await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
                    
                    canais_encontrados = await page.evaluate('''async () => {
                        let todosCanais = new Map();
                        let scrollStep = 1000;
                        let lastHeight = 0;
                        while (true) {
                            let itens = document.querySelectorAll('li.sidebar-entry');
                            itens.forEach(li => {
                                let btn = li.querySelector('button');
                                if (btn) {
                                    let nome = li.getAttribute('data-channel-name');
                                    let url = btn.getAttribute('data-video-url');
                                    if (nome && url) todosCanais.set(nome, url);
                                }
                            });
                            window.scrollBy(0, scrollStep);
                            await new Promise(r => setTimeout(r, 800));
                            let currentHeight = document.body.scrollHeight;
                            if (currentHeight === lastHeight) break; 
                            lastHeight = currentHeight;
                        }
                        return Array.from(todosCanais.entries()).map(([nome, url]) => ({nome, url}));
                    }''')
                    
                    lista_valida = {}
                    for canal in canais_encontrados:
                        if await testar_link(session, canal['url']):
                            lista_valida[canal['nome']] = canal['url']
                    
                    if lista_valida:
                        dados_finais[code.upper()] = lista_valida
                        # Salva progressivamente para não perder dados se o bot parar
                        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
                        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
                            json.dump(dados_finais, f, indent=4, ensure_ascii=False)

        print(">>> Varredura finalizada com sucesso.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
