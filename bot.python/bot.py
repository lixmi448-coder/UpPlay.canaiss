import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json
import os

async def coletar_canais_da_lista(page):
    """
    Coleta dados diretamente do elemento <li>, que é o container 
    estável da lista virtualizada.
    """
    # Espera o container da lista aparecer
    try:
        await page.wait_for_selector('ul.virtualized-list', timeout=10000)
    except:
        return []

    # Extrai os dados diretamente dos atributos do <li>
    # Isso é muito mais rápido do que esperar o botão renderizar
    return await page.evaluate('''() => {
        const itens = Array.from(document.querySelectorAll('li.sidebar-entry'));
        return itens.map(li => ({
            nome: li.getAttribute('data-channel-name'),
            url: li.querySelector('button')?.getAttribute('data-video-url')
        })).filter(item => item.nome && item.url);
    }''')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(">>> Iniciando varredura de alta velocidade...")
        await page.goto('https://famelack.com/tv/')
        
        # Coleta rápida dos países
        itens_pais = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens_pais]
        
        dados_finais = {}
        
        for code in codigos:
            if not code: continue
            print(f"-> Acessando {code.upper()}...")
            
            await page.goto(f'https://famelack.com/tv/{code}/')
            
            # Força o carregamento da lista virtualizada com um scroll rápido
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2) # Espera mínima apenas para o JS injetar os LI
            
            # Captura a lista
            canais = await coletar_canais_da_lista(page)
            
            if canais:
                dados_finais[code.upper()] = {c['nome']: c['url'] for c in canais}
                print(f"   Coletado: {len(canais)} canais.")
            
        # Salva o resultado
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        await browser.close()
        print(">>> Concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(run())
