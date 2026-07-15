import asyncio
import aiohttp
import json
import os
from playwright.async_api import async_playwright

# Lista de verificação robusta
async def testar_link(session, url):
    try:
        # User-Agent de navegador para evitar bloqueios
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        async with session.get(url, timeout=10, headers=headers) as response:
            # Consideramos válido se retornar status 200 ou outros códigos de sucesso
            return response.status in [200, 206, 301, 302]
    except:
        return False

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Acessa a página principal para listar países
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        itens_pais = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens_pais if await item.get_attribute('data-country-code')]
        
        dados_finais = {}
        async with aiohttp.ClientSession() as session:
            for code in codigos:
                print(f"--- Processando País: {code.upper()} ---")
                await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
                
                # Scroll agressivo para forçar a renderização de toda a lista virtualizada
                await page.evaluate('''async () => {
                    let totalHeight = 0;
                    let distance = 2000;
                    while (totalHeight < document.body.scrollHeight) {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        await new Promise(r => setTimeout(r, 600));
                    }
                }''')
                
                # Extrai a lista completa de elementos já renderizados
                canais_elementos = await page.evaluate('''() => {
                    const itens = Array.from(document.querySelectorAll('li.sidebar-entry'));
                    return itens.map(li => {
                        const btn = li.querySelector('button');
                        if (!btn) return null;
                        return {
                            nome: li.getAttribute('data-channel-name'),
                            url: btn.getAttribute('data-video-url')
                        };
                    }).filter(item => item && item.url);
                }''')
                
                print(f"   Encontrados {len(canais_elementos)} canais. Iniciando testes...")
                
                lista_valida = {}
                for canal in canais_elementos:
                    if await testar_link(session, canal['url']):
                        lista_valida[canal['nome']] = canal['url']
                        print(f"   [OK] {canal['nome']}")
                
                if lista_valida:
                    dados_finais[code.upper()] = lista_valida

        # Salva o resultado final
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura finalizada e todos os links validados.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
