import asyncio
import json
import os
from playwright.async_api import async_playwright

# Armazenará os links encontrados: {codigo_pais: {nome_canal: url_stream}}
dados_finais = {}

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Contexto para capturar a rede
        context = await browser.new_context()
        page = await context.new_page()

        # Dicionário temporário para armazenar o link do canal atual sendo processado
        # Usamos uma lista para poder modificar dentro da função de callback
        canal_atual_info = {"url": None}

        # Função que intercepta requisições de rede
        def intercept_request(request):
            # Filtra por formatos comuns de streaming
            if any(ext in request.url for ext in [".m3u8", "/manifest", "playlist"]):
                canal_atual_info["url"] = request.url

        page.on("request", intercept_request)

        await page.goto('https://famelack.com/tv/', wait_until='networkidle')

        # 1. Coleta a lista de países
        print(">>> Iniciando varredura...")
        paises = await page.query_selector_all('.country-item')
        codigos = [await p.get_attribute('data-country-code') for p in paises if await p.get_attribute('data-country-code')]

        for code in codigos:
            print(f"-> Processando País: {code.upper()}")
            await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
            await page.wait_for_timeout(2000) # Aguarda renderizar

            # 2. Coleta todos os canais do país
            canais = await page.query_selector_all('li.sidebar-entry')
            
            dados_pais = {}
            for canal in canais:
                nome_canal = await canal.get_attribute('data-channel-name')
                if not nome_canal: continue
                
                # Reseta o link capturado antes de clicar
                canal_atual_info["url"] = None
                
                # Clica no canal
                btn = await canal.query_selector('button')
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(3000) # Tempo vital para o link aparecer na rede
                    
                    if canal_atual_info["url"]:
                        dados_pais[nome_canal] = canal_atual_info["url"]
            
            if dados_pais:
                dados_finais[code.upper()] = dados_pais
                print(f"   Salvou {len(dados_pais)} canais para {code.upper()}.")

        # 3. Salva no arquivo
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura concluída com sucesso.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
