"""Verifica navegación y geometría del HTML y exporta el PDF local."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto((OUT/'Neifit_presentacion_animada.html').as_uri())
    assert page.locator('.slide').count()==18
    assert page.locator('img').evaluate('(img)=>img.complete && img.naturalWidth>0')
    overflow=[]
    for index in range(18):
        page.evaluate('(i)=>show(i)',index)
        page.wait_for_timeout(570)
        assert page.locator('.slide:visible').count()==1
        issues=page.locator('.slide.active').evaluate('''slide=>{
          const bottom=slide.querySelector('footer').getBoundingClientRect().top;
          return [...slide.querySelectorAll('header,article,table,pre,.takeaway,.diagram')]
            .filter(e=>e.getBoundingClientRect().bottom>bottom-5 || e.scrollHeight>e.clientHeight+3)
            .map(e=>({tag:e.tagName,class:e.className,text:e.innerText?.slice(0,45)}));
        }''')
        if issues:overflow.append((index+1,issues))
        if index in (0,5,7,12):page.screenshot(path=str(OUT/f'vista_{index+1:02}.png'))
    assert not overflow,overflow
    page.keyboard.press('Home');assert page.locator('#counter').inner_text()=='1 / 18'
    page.keyboard.press('ArrowRight');assert page.locator('#counter').inner_text()=='2 / 18'
    page.keyboard.press('n');assert page.locator('#notes').is_visible()
    page.keyboard.press('Escape');assert not page.locator('#notes').is_visible()
    page.keyboard.press('o');assert page.locator('#overview').is_visible()
    page.locator('#overviewGrid button').nth(7).click();assert page.locator('#counter').inner_text()=='8 / 18'
    assert not errors,errors
    page.emulate_media(media='print',reduced_motion='reduce')
    page.pdf(path=str(OUT/'Neifit_presentacion_consultas.pdf'),prefer_css_page_size=True,print_background=True)
    browser.close()
print('OK: 18 diapositivas sin desbordamiento, navegación, guion, índice e imagen local; PDF generado.')
