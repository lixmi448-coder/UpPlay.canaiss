import asyncio
import json
import os
from playwright.async_api import async_playwright

dados_finais = {}

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = await context.new_page()

        canal_link = {"url": None}

        def intercept_request(request):
            if any(x in request.url for x in ["m3u8", "manifest", ".m3u"]):
                canal_link["url"] = request.url

        page.on("request", intercept_request)

        print(">>> Acessando site e carregando lista completa...")
        await page.goto('https://famelack.com/tv/', wait_until='networkidle')

        # Lógica para rolar até o fim da lista de países
        last_count = 0
        while True:
            # Rola a página ou container principal. Ajustamos para rolar a página toda
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000) 
            
            paises_atuais = await page.query_selector_all('.country-item')
            if len(paises_atuais) == last_count:
                break
            last_count = len(paises_atuais)
            print(f"   Carregando países... {last_count} encontrados.")

        # Agora coletamos os códigos com a lista completa
        paises = await page.query_selector_all('.country-item')
        codigos = []
        for p in paises:
            code = await p.get_attribute('data-country-code')
            if code: codigos.append(code)

        for code in codigos:
            print(f"-> Processando: {code.upper()}")
            await page.goto(f'https://famelack.com/tv/{code}/', wait_until='networkidle')
            await page.wait_for_selector('li.sidebar-entry')

            canais = await page.query_selector_all('li.sidebar-entry')
            dados_pais = {}

            for canal in canais:
                nome = await canal.get_attribute('data-channel-name')
                if not nome: continue
                
                canal_link["url"] = None
                try:
                    btn = await canal.query_selector('button')
                    if btn:
                        await btn.scroll_into_view_if_needed()
                        await btn.click()
                        await page.wait_for_timeout(3500) # Espera o player carregar o link
                        
                        if canal_link["url"]:
                            dados_pais[nome] = canal_link["url"]
                            print(f"   [OK] {nome}")
                except Exception as e:
                    print(f"   [Erro] {nome}: {e}")

            if dados_pais:
                dados_finais[code.upper()] = dados_pais

        # Salva o arquivo
        if not os.path.exists('canaisgringos.html'): os.makedirs('canaisgringos.html')
        with open('canaisgringos.html/canais.json', 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
            
        print(">>> Varredura finalizada com todos os países.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
