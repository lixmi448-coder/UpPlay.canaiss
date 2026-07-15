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

async def rolar_ate_o_fim(page, selector):
    ultima_altura = 0
    while True:
        await page.evaluate(f"document.querySelector('{selector}').scrollTop += 1000")
        await asyncio.sleep(1.5)
        nova_altura = await page.evaluate(f"document.querySelector('{selector}').scrollTop")
        if nova_altura == ultima_altura: break
        ultima_altura = nova_altura

async def run():
    dados_finais = carregar_dados_existentes()
    alterado = False
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(">>> Acessando o site...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        # Rola o menu lateral de países
        await rolar_ate_o_fim(page, '.sidebar-content')
        
        codigos = await page.evaluate('''() => {
            const itens = document.querySelectorAll('li.sidebar-entry.country-item');
            return Array.from(itens).map(li => li.getAttribute('data-country-code'));
        }''')
        
        print(f">>> Total de países detectados: {len(codigos)}")
        
        async with aiohttp.ClientSession() as session:
            for code in codigos:
                if not code or code.upper() in dados_finais: continue
                
                print(f"-> Processando País: {code.upper()}")
                await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
                
                # Rola para carregar canais do país
                await rolar_ate_o_fim(page, '.sidebar-content')
                
                canais_encontrados = await page.evaluate('''() => {
                    let itens = document.querySelectorAll('li.sidebar-entry');
                    return Array.from(itens).map(li => {
                        let btn = li.querySelector('button');
                        return btn ? {nome: li.getAttribute('data-channel-name'), url: btn.getAttribute('data-video-url')} : null;
                    }).filter(c => c && c.nome && c.url);
                }''')
                
                lista_valida = {}
                for canal in canais_encontrados:
                    if await testar_link(session, canal['url']):
                        lista_valida[canal['nome']] = canal['url']
                
                if lista_valida:
                    dados_finais[code.upper()] = lista_valida
                    alterado = True
                    print(f"   [OK] {len(lista_valida)} canais salvos.")
        
        if alterado:
            with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
                json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            print(">>> Arquivo JSON atualizado.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
