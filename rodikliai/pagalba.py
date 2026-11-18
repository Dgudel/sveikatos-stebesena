"""Bendros priemonės sveikatos švieslentės rodikliams: Lietuvos, kaimynių ir ES serijos, standartinis grafikas."""
import plotly.graph_objects as go

from .bendra import SERIJOS, linijos, stilius
from .eurostat_duomenys import serija

# Spalvos: Lietuva visada mėlyna, ES – oranžinė, kaimynės – žalia ir geltona
SALYS = [("LT", "Lietuva", SERIJOS[0]), ("EU27_2020", "ES-27", SERIJOS[1]),
         ("LV", "Latvija", SERIJOS[2]), ("EE", "Estija", SERIJOS[3])]


def salys(kodas: str, **filtrai) -> dict:
    """{geo: serija} visoms SALYS; jei kurios nors šalies duomenų nėra – ji praleidžiama (Lietuva privaloma)."""
    rez = {}
    for geo, _, _ in SALYS:
        try:
            s = serija(kodas, geo, **filtrai)
        except ValueError:
            if geo == "LT":
                raise
            continue
        if len(s):
            rez[geo] = s
    return rez


def saliu_grafikas(serijos: dict, pavadinimas: str, paantraste: str, saltinis: str, vnt: str = "",
                   dec: int = 1, nuo: str | None = "2010-01-01", nuo_nulio: bool = True, metiniai: bool = True):
    """Linijinis grafikas: Lietuva, ES-27, Latvija, Estija (kurios yra)."""
    f = go.Figure()
    eil = []
    for geo, vardas, spalva in SALYS:
        if geo in serijos:
            s = serijos[geo]
            if nuo:
                s = s[s.index >= nuo]
            if len(s):
                eil.append((vardas, s, spalva))
    linijos(f, eil, vnt=vnt, zenklas=False, dec=dec, zymekliai=metiniai, nuo_nulio=nuo_nulio)
    stilius(f, pavadinimas, paantraste, saltinis, vnt=vnt, nulio_linija=False, metiniai=metiniai)
    # Lietuvos linija – storesnė, kad išsiskirtų
    for tr in f.data:
        if tr.name == "Lietuva":
            tr.line.width = 3.5
    if nuo_nulio:
        f.update_yaxes(rangemode="tozero")
    return f


def lentele_is(serijos: dict, pavadinimas: str):
    """CSV lentelė: metai × šalys."""
    import pandas as pd
    d = pd.DataFrame({f"{geo}_{pavadinimas}": s for geo, s in serijos.items()})
    d = d.sort_index()
    d.insert(0, "metai", d.index.year)
    return d


def eurostat_nuoroda(kodas: str) -> tuple[str, str]:
    return (f"Eurostat – {kodas}", f"https://ec.europa.eu/eurostat/databrowser/view/{kodas}/default/table?lang=en")
