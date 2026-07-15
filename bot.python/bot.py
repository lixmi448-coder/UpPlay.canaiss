import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch com argumentos para não ser detectado como bot
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(">>> Iniciando varredura total e exaustiva...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Coleta a lista de países
        itens_pais = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens_pais if await item.get_attribute('data-country-code')]
        
        dados_finais = {}
        
        for code in codigos:
            print(f"-> Entrando no país: {code.upper()}")
            await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
            
            # Força a renderização completa da lista virtualizada
            await page.evaluate('''async () => {
                const scrollStep = 2000;
                let lastHeight = 0;
                let currentHeight = document.body.scrollHeight;
                
                while (true) {
                    window.scrollBy(0, scrollStep);
                    await new Promise(r => setTimeout(r, 600)); // Tempo para carregar novos itens
                    currentHeight = document.body.scrollHeight;
                    if (currentHeight === lastHeight) break; // Chegou ao fim
                    lastHeight = currentHeight;
                }
            }''')
            
            # Captura bruta: lê todos os atributos dos <li>
            canais_pais = await page.evaluate('''() => {
                const itens = Array.from(document.querySelectorAll('li.sidebar-entry'));
                return itens.map(li => {
                    const btn = li.querySelector('button');
                    if (!btn) return null;
                    
                    // Extrai o JSON de URLs e o link principal
                    let urls = [];
                    try {
                        const raw = btn.getAttribute('data-urls');
                        urls = raw ? JSON.parse(raw) : [];
                    } catch(e) {}
                    
                    const urlMain = btn.getAttribute('data-video-url');
                    if (urlMain && !urls.includes(urlMain)) urls.push(urlMain);
                    
                    return {
                        nome: li.getAttribute('data-channel-name'),
                        links: urls.filter(u => u && u.length > 0)
                    };
                }).filter(item => item !== null && item.links.length > 0);
            }''')
            
            if canais_pais:
                dados_finais[code.upper()] = {c['nome']: c['links'] for c in canais_pais}
                print(f"   [OK] {len(canais_pais)} canais capturados em {code.upper()}.")
            else:
                print(f"   [AVISO] Nenhum link extraído em {code.upper()}.")
            
        # Garante a pasta e salva o JSON
        if not os.path.exists('canaisgringos.html'): 
            os.makedirs('canaisgringos.html')
        
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        await browser.close()
        print(">>> Varredura finalizada com sucesso. Arquivo gerado em 'canaisgringos.html/canais.json'.")

if __name__ == "__main__":
    asyncio.run(run())
