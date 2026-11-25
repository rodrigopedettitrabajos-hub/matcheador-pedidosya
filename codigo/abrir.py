"""Matcheador.exe: abre la pantalla del matcheador en el navegador. No necesita Python ni planillas al lado."""
import shutil, sys, tempfile, webbrowser
from pathlib import Path

origen = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent / "Para tecnicos")) / "Matcheador.html"
# Se copia afuera: la carpeta interna del .exe se borra al cerrarse, antes de que el navegador termine de leerla
destino = Path(tempfile.gettempdir()) / "Matcheador.html"
shutil.copyfile(origen, destino)
webbrowser.open(destino.as_uri())
