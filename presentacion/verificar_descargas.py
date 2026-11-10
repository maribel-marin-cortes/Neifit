from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('presentacion').resolve()
with sync_playwright() as p:
 browser=p.chromium.launch(channel='msedge',headless=True)
 page=browser.new_page(accept_downloads=True)
 page.goto((out/'Neifit_presentacion_animada.html').as_uri())
 page.locator('.downloads summary').click()
 with page.expect_download() as download:
  page.locator('#downloadHtml').click()
 assert download.value.suggested_filename=='Neifit_presentacion_animada.html'
 assert download.value.failure() is None
 page.locator('.downloads summary').click()
 with page.expect_download() as download:
  page.locator('.downloads a[download]').filter(has_text='PowerPoint').click()
 assert download.value.suggested_filename.endswith('.pptx')
 assert download.value.failure() is None
 browser.close()
print('OK: descargas HTML y PowerPoint desde el boton verificados.')
