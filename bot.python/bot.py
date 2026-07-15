import asyncio
import aiohttp
import json
import os
from playwright.async_api import async_playwright

# Configuração de timeout e headers para evitar bloqueios
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
        
        print(">>> Iniciando varredura acumulativa...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Coleta a lista de países
        itens_pais = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens_pais if await item.get_attribute('data-country-code')]
        
        dados_finais = {}
        
        async with aiohttp.ClientSession() as session:
            for code in codigos:
                print(f"-> Processando País: {code.upper()}")
                await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
                
                # Técnica do Acumulador: Coleta enquanto rola para não perder itens descartados pelo site
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
                                if (nome && url) {
                                    todosCanais.set(nome, url);
                                }
                            }
                        });
                        
                        window.scrollBy(0, scrollStep);
                        await new Promise(r => setTimeout(r, 800)); // Espera o carregamento
                        
                        let currentHeight = document.body.scrollHeight;
                        if (currentHeight === lastHeight) break; 
                        lastHeight = currentHeight;
                    }
                    return Array.from(todosCanais.entries()).map(([nome, url]) => ({nome, url}));
                }''')
                
                print(f"   Coletados {len(canais_encontrados)} canais. Validando links...")
                
                lista_valida = {}
                for canal in canais_encontrados:
                    if await testar_link(session, canal['url']):
                        lista_valida[canal['nome']] = canal['url']
                
                if lista_valida:
                    dados_finais[code.upper()] = lista_valida
                    print(f"   [OK] {len(lista_valida)} canais ativos salvos para {code.upper()}.")

        # Salva o resultado final
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura finalizada com todos os canais capturados e validados.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
