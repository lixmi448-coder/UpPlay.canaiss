import asyncio
import json
import os
from playwright.async_api import async_playwright

contexto_canal = {"nome": ""}

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        links_coletados = {}

        # O MÁGICO: Agora capturamos TUDO que é identificado como recurso de mídia ou fetch dinâmico
        async def interceptar_rede(request):
            # Filtramos por tipos de recurso de mídia ou requisições que pareçam streams
            resource_type = request.resource_type
            url = request.url
            
            # Captura se for um recurso de mídia (vídeo/áudio) ou se a URL contiver 'stream' ou 'playlist'
            # Isso pega m3u8, mpd, transmissões de youtube, etc.
            if resource_type in ["media", "fetch", "xhr"] and any(x in url for x in ["stream", "playlist", "m3u8", "mpd", "video"]):
                nome = contexto_canal["nome"]
                if nome and nome not in links_coletados:
                    links_coletados[nome] = url
                    print(f"   [CAPTURA TOTAL] {nome}: {url}")

        page.on("request", interceptar_rede)

        print(">>> Iniciando varredura universal de streams...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')
        
        itens_pais = await page.query_selector_all('.country-item')
        codigos = [await item.get_attribute('data-country-code') for item in itens_pais if await item.get_attribute('data-country-code')]
        
        resultado_final = {}

        for code in codigos:
            print(f"-> Analisando país: {code.upper()}")
            await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
            
            # Força o scroll para renderizar a lista
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2) 
            
            canais = await page.query_selector_all('li.sidebar-entry button')
            
            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                contexto_canal["nome"] = nome
                
                try:
                    await canal.click()
                    # Aguarda um pouco mais para garantir que a rede dispare o stream
                    await asyncio.sleep(2.0)
                except:
                    continue
            
            resultado_final[code.upper()] = links_coletados.copy()
            links_coletados.clear()

        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/lista_universal.json', 'w', encoding='utf-8') as f:
            json.dump(resultado_final, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura finalizada. Todos os streams capturados.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
