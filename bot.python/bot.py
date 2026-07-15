import asyncio
import aiohttp
import json
import os
from playwright.async_api import async_playwright

ARQUIVO_JSON = 'canaisgringos.html/canais.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

def carregar_dados_existentes():
    if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
    if os.path.exists(ARQUIVO_JSON):
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

async def testar_link(session, url):
    try:
        async with session.get(url, timeout=8, headers=HEADERS) as response:
            return response.status in [200, 206, 301, 302]
    except: return False

async def run():
    dados_finais = carregar_dados_existentes()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(">>> Acessando o site para extrair a lista completa...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Extração direta da lista virtualizada (pega todos os países de uma vez)
        codigos = await page.evaluate('''() => {
            const itens = document.querySelectorAll('li.sidebar-entry.country-item');
            return Array.from(itens).map(li => li.getAttribute('data-country-code'));
        }''')
        
        print(f">>> Total de países detectados: {len(codigos)}")
        
        async with aiohttp.ClientSession() as session:
            for code in codigos:
                if not code: continue
                code_upper = code.upper()
                
                # Checkpoint: Pula se já tiver sido processado
                if code_upper in dados_finais: continue
                    
                print(f"-> Processando País: {code_upper}")
                await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
                
                # Coleta canais dentro do país
                canais_encontrados = await page.evaluate('''async () => {
                    let todosCanais = new Map();
                    // Rola para garantir que os canais internos carreguem
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(r => setTimeout(r, 1000));
                    
                    let itens = document.querySelectorAll('li.sidebar-entry');
                    itens.forEach(li => {
                        let btn = li.querySelector('button');
                        if (btn) {
                            let nome = li.getAttribute('data-channel-name');
                            let url = btn.getAttribute('data-video-url');
                            if (nome && url) todosCanais.set(nome, url);
                        }
                    });
                    return Array.from(todosCanais.entries()).map(([nome, url]) => ({nome, url}));
                }''')
                
                lista_valida = {}
                for canal in canais_encontrados:
                    if await testar_link(session, canal['url']):
                        lista_valida[canal['nome']] = canal['url']
                
                if lista_valida:
                    dados_finais[code_upper] = lista_valida
                    with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
                        json.dump(dados_finais, f, indent=4, ensure_ascii=False)
                    print(f"   [OK] {len(lista_valida)} canais salvos para {code_upper}.")

        print(">>> Varredura concluída.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
