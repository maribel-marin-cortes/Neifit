from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from pypdf import PdfReader
out=Path('presentacion')
pdf=PdfReader(out/'Neifit_presentacion_consultas.pdf')
assert len(pdf.pages)==18,len(pdf.pages)
assert all((p.extract_text() or '').strip() for p in pdf.pages)
with ZipFile(out/'Neifit_presentacion_consultas.pptx') as z:
 slides=[n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
 notes=[n for n in z.namelist() if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml')]
 assert len(slides)==len(notes)==18
 for name in slides:
  root=ET.fromstring(z.read(name));assert root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}transition') is not None
with ZipFile(out/'Neifit_paquete_consultas.zip','w',ZIP_DEFLATED) as z:
 for name in ['Neifit_presentacion_animada.html','Neifit_presentacion_consultas.pptx','Neifit_presentacion_consultas.pdf','GUIA_PARA_EXPONER.md','consultas_ejemplo.sql']:
  z.write(out/name,name)
print('Verificado: PDF de 18 paginas; PPTX con 18 diapositivas, notas y transiciones; paquete ZIP listo.')
