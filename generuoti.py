"""Sugeneruoja sveikatos rodiklių švieslentės svetainę į aplanką _site/.

    python generuoti.py              # iš duomenys/ aplanko failų
    ATNAUJINTI=1 python generuoti.py # prieš tai atsisiunčia naujausius duomenis (Eurostat, data.gov.lt)

Peržiūra kompiuteryje:  python -m http.server -d _site 8000  ->  http://localhost:8000
"""
import os

import pandas as pd
import shutil
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from rodikliai import (darbo_vietos, gyvenimo_trukme, islaidos_sveikatai, isvengiamas_mirtingumas, medikai,
                       paciento_mokejimai, sveikatos_eiles, uzimtieji)
from rodikliai.bendra import (slugas, papildomas_grafikas, sk, sparkline_svg, zmoniu_laikotarpis, palyginimo_tekstas,
                              nustatyk_kalba, en, t)

SAKNIS = Path(__file__).resolve().parent
ISVESTIS = SAKNIS / "_site"

# Studijų programos puslapis ir registracija – PAKEISKITE į tikras nuorodas
PROGRAMA = {
    "pavadinimas": "Sveikatos vadyba",
    "aprasas": "Bakalauro studijų programa Mykolo Romerio universitete",
    "nuoroda": "https://www.mruni.eu/",            # programos puslapis
    "registracija": "https://www.mruni.eu/",       # registracija į renginį / konsultaciją
}

# Sudedamosios dalys, rodomos kaip atskiros kortelės: (tėvinio rodiklio id, dalies pavadinimo pradžia, pavadinimas,
# aprašas, EN pavadinimas, EN aprašas). Pirmoje versijoje nenaudojama.
ISKELTI = {}

SRITYS = [
    {"nr": 1, "trumpai": ("Sveikata", "Health"),
     "pavadinimas": ("Ar Lietuvos žmonės sveiki?", "Are people in Lithuania healthy?"),
     "klausimas": ("Kiek gyvename, kiek metų – sveiki, ir kiek mirčių būtų galima išvengti.",
                   "How long we live, how many years in good health, and how many deaths could be avoided."),
     "rodikliai": [gyvenimo_trukme, isvengiamas_mirtingumas]},
    {"nr": 2, "trumpai": ("Prieinamumas", "Access"),
     "pavadinimas": ("Ar sistema pasiekia pacientą?", "Does the system reach the patient?"),
     "klausimas": ("Ar pacientas laiku gauna pagalbą ir ar gali už ją susimokėti – tai paciento kelio klausimas.",
                   "Do patients get care on time and can they afford it?"),
     "rodikliai": [sveikatos_eiles, paciento_mokejimai]},
    {"nr": 3, "trumpai": ("Ištekliai", "Resources"),
     "pavadinimas": ("Kas laiko sveikatos sistemą?", "What keeps the health system running?"),
     "klausimas": ("Kiek turime medikų, kas juos pakeis ir kiek pinigų skiriame sveikatai.",
                   "How many health workers we have, who will replace them and how much we spend on health."),
     "rodikliai": [medikai, islaidos_sveikatai]},
    {"nr": 4, "trumpai": ("Karjera", "Careers"),
     "pavadinimas": ("Ar sveikatos srityje yra darbo?", "Are there jobs in health?"),
     "klausimas": ("Kiek žmonių dirba sveikatos ir globos srityje, kiek darbo vietų siūloma ir už kokį atlyginimą.",
                   "How many people work in health and care, how many jobs are offered and at what pay."),
     "rodikliai": [uzimtieji, darbo_vietos]},
]

BUSENOS_LT = {
    "gereja":   {"zodis": "Gerėja",   "ikona": "▲"},
    "stabilu":  {"zodis": "Stabilu",  "ikona": "■"},
    "prasteja": {"zodis": "Prastėja", "ikona": "▼"},
    "info":     {"zodis": "Stebimas", "ikona": "◆"},
    "nera":     {"zodis": "Nėra duomenų", "ikona": "○"},
}
BUSENOS_EN = {
    "gereja":   {"zodis": "Improving", "ikona": "▲"},
    "stabilu":  {"zodis": "Stable",    "ikona": "■"},
    "prasteja": {"zodis": "Worsening", "ikona": "▼"},
    "info":     {"zodis": "Monitored", "ikona": "◆"},
    "nera":     {"zodis": "No data",   "ikona": "○"},
}
BUSENOS = BUSENOS_LT


def rodikliu(n: int) -> str:
    """Skaičius su taisyklinga daugiskaita: 1 rodiklis, 3 rodikliai, 10 rodiklių, 21 rodiklis."""
    if en():
        return f"{n} indicator" if n == 1 else f"{n} indicators"
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} rodiklis"
    if 2 <= n % 10 <= 9 and not 11 <= n % 100 <= 19:
        return f"{n} rodikliai"
    return f"{n} rodiklių"


def saugus_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Apsauga nuo CSV formulių injekcijos: tekstinis langelis, prasidedantis =, +, -, @, tab ar CR
    (ir nesantis skaičiumi), gauna priekyje apostrofą, kad Excel jo nevykdytų kaip formulės."""
    import re
    pavojinga = re.compile(r"^[=+\-@\t\r]")
    skaicius = re.compile(r"^[+-]?\d+([.,]\d+)?([eE][+-]?\d+)?$")
    df = df.copy()
    df.columns = [("'" + c) if isinstance(c, str) and pavojinga.match(c) else c for c in df.columns]
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) in ("string", "str"):
            df[c] = df[c].map(lambda v: "'" + v if isinstance(v, str) and pavojinga.match(v) and not skaicius.match(v) else v)
    return df


def pirma_didzioji(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def saugiai(modulis):
    """Apskaičiuoja rodiklį. Jei nepavyksta su naujai atsisiųstais duomenimis – bando su saugyklos failais;
    jei ir tai nepavyksta – rodiklis praleidžiamas, bet svetainė vis tiek sugeneruojama."""
    try:
        return modulis.rodiklis()
    except Exception as e:
        print(f"  ⚠ {modulis.__name__}: {type(e).__name__}: {e}")
    if os.environ.get("ATNAUJINTI") == "1":
        import subprocess
        from rodikliai import eurostat_duomenys
        subprocess.run(["git", "checkout", "--", "duomenys/"], cwd=SAKNIS, capture_output=True)
        os.environ["ATNAUJINTI"] = "0"
        eurostat_duomenys.lentele.cache_clear()
        try:
            r = modulis.rodiklis()
            print(f"  ↺ {modulis.__name__}: naudoti saugyklos duomenys")
            return r
        except Exception as e:
            print(f"  ⚠ {modulis.__name__} vis tiek nepavyko: {e}")
        finally:
            os.environ["ATNAUJINTI"] = "1"
            eurostat_duomenys.lentele.cache_clear()
    print(f"  ✗ {modulis.__name__} praleistas")
    return None


def generuok(kalba: str, isvestis: Path, bendra_info: dict):
    """Sugeneruoja vienos kalbos svetainę. bendra_info – LT praėjime nustatyti dalių id ir iškeltos dalys,
    kad EN puslapiai turėtų tuos pačius failų vardus."""
    nustatyk_kalba(kalba)
    busenos = BUSENOS_EN if en() else BUSENOS_LT
    (isvestis / "rodikliai").mkdir(parents=True)
    (isvestis / "duomenys").mkdir()
    shutil.copytree(SAKNIS / "statika", isvestis / "statika")
    # Grafikų biblioteka laikoma pačioje svetainėje (ne iš išorinio CDN) – ta pati versija, kurią naudoja plotly paketas
    import plotly
    plotly_js = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
    shutil.copy(plotly_js, isvestis / "statika" / "plotly.min.js")

    env = Environment(loader=FileSystemLoader(SAKNIS / "sablonai"), autoescape=True)
    env.filters["sk"] = sk
    env.filters["laikotarpis"] = zmoniu_laikotarpis
    env.filters["rodikliu"] = rodikliu
    env.filters["pirma_didzioji"] = pirma_didzioji
    env.globals["t"] = t
    from plotly.offline import get_plotlyjs_version
    import hashlib
    css_versija = hashlib.md5((SAKNIS / "statika" / "stilius.css").read_bytes()).hexdigest()[:8]
    grafiko_cfg = {"displaylogo": False, "responsive": True, "toImageButtonOptions": {"format": "png", "scale": 2}}
    bendri = {"busenos": busenos, "atnaujinta": date.today().strftime("%Y-%m-%d"), "css_versija": css_versija,
              "metai": date.today().year, "kalba": kalba, "en": en(),
              "plotlyjs_versija": get_plotlyjs_version(), "programa": PROGRAMA,
              "plotly_hash": hashlib.md5(plotly_js.read_bytes()).hexdigest()[:8],
              # MRU logotipas: įdėkite statika/mru-logo.svg (arba .png) – bus rodomas apačioje
              "mru_logo": next((f"statika/{f.name}" for f in sorted((SAKNIS / "statika").glob("mru-logo.*"))), None)}

    def rasyk(kelias: str, sablonas: str, **kint):
        (isvestis / kelias).write_text(env.get_template(sablonas).render(puslapis=kelias, **kint, **bendri),
                                       encoding="utf-8")

    sritys = []
    for sritis in SRITYS:
        i = 1 if en() else 0
        sritis = {**sritis, "trumpai": sritis["trumpai"][i], "pavadinimas": sritis["pavadinimas"][i],
                  "klausimas": sritis["klausimas"][i]}
        rodikliai = []
        for modulis in sritis["rodikliai"]:
            print(f"• [{kalba}] {modulis.__name__}")
            r = saugiai(modulis)
            if r is None:
                continue
            if r.palyginimas is None:
                r.palyginimas = palyginimo_tekstas(r.laikotarpis)
            r.spark = sparkline_svg(r.sparkline, nuo_nulio=r.spark_nuo_nulio) if r.sparkline is not None else ""
            id_sar = bendra_info.setdefault("dalys", {}).get(r.id)
            for j, x in enumerate(r.dalys):
                x.id = id_sar[j] if id_sar and len(id_sar) == len(r.dalys) else f"{r.id}--{slugas(x.pavadinimas)}"
                x.tevas = r
                x.spark = sparkline_svg(x.serija, nuo_nulio=False) if x.serija is not None and len(x.serija) > 1 else ""
            if not en():
                bendra_info["dalys"][r.id] = [x.id for x in r.dalys]
            r.grafiku_html = [f.to_html(full_html=False, include_plotlyjs=False,
                                        config={**grafiko_cfg, **({} if en() else {"locale": "lt"})})
                              for f in r.grafikai]
            if r.lentele is not None:
                saugus_csv(r.lentele.round(2)).to_csv(isvestis / "duomenys" / f"{r.id}.csv", index=False,
                                                      encoding="utf-8-sig")
            rodikliai.append(r)
        for r in rodikliai:
            r.visos_busenos = [r.busena] + [x.busena for x in r.dalys]
            r.nesutampa = [x for x in r.dalys if x.busena in ("gereja", "stabilu", "prasteja") and x.busena != r.busena]
        suvestine = {k: sum(b == k for r in rodikliai for b in r.visos_busenos) for k in busenos}
        sritys.append({**sritis, "rodikliai": rodikliai, "suvestine": suvestine})

    bendri["meniu_sritys"] = sritys
    visi = [(s, r) for s in sritys for r in s["rodikliai"]]
    bendra = {k: sum(b == k for _, r in visi for b in r.visos_busenos) for k in busenos}
    pagrindiniai = {k: sum(r.busena == k for _, r in visi) for k in busenos}
    daliu_sk = sum(len([x for x in r.dalys if x.busena in ("gereja", "stabilu", "prasteja")]) for _, r in visi)
    vertinti = sum(bendra[k] for k in ("gereja", "stabilu", "prasteja"))

    for sritis in sritys:
        visos_dalys = [x for r in sritis["rodikliai"] for x in r.dalys if x.busena != "nera"]
        iskeltos = []
        for tevas, pradzia, pav_lt, apr_lt, pav_en, apr_en in ISKELTI.get(sritis["nr"], []):
            if en():      # EN – pagal LT praėjime rastą dalies id
                x_id = bendra_info.get("iskeltos", {}).get((tevas, pradzia))
                x = next((d for d in visos_dalys if d.id == x_id), None)
            else:
                x = next((d for d in visos_dalys if d.tevas.id == tevas and d.pavadinimas.startswith(pradzia)), None)
                if x is not None:
                    bendra_info.setdefault("iskeltos", {})[(tevas, pradzia)] = x.id
            if x is None:
                print(f"  ⚠ iškelti nepavyko: {tevas} / {pradzia}")
                continue
            x.pavadinimas, x.trumpas_aprasas = (pav_en, apr_en) if en() else (pav_lt, apr_lt)
            x.nesutampa = []
            iskeltos.append(x)
        for r in sritis["rodikliai"]:          # iškeltos dalys turi savo kortelę – tėvo kortelėje jų nekartojame
            r.nesutampa = [d for d in r.nesutampa if d not in iskeltos]
        sritis["pagrindines"] = list(sritis["rodikliai"]) + iskeltos
        sritis["kitos"] = [x for x in visos_dalys if x not in iskeltos]
        for x in iskeltos + sritis["kitos"]:      # puslapiai – ir iškeltoms, ir likusioms dalims
            s = x.serija.dropna() if x.serija is not None else None
            if s is not None and len(s) > 1:
                if len(s) > 40 and (s.index[-1] - s.index[0]).days > 365 * 15:
                    s = s[s.index >= s.index[-1] - pd.DateOffset(years=15)]
                vnt = " %" if x.vienetai.strip() == "%" else x.vienetai
                f = papildomas_grafikas(
                    x.pavadinimas,
                    t(f"Lietuva · rodiklio „{x.tevas.pavadinimas}“ sudedamoji dalis",
                      f"Lithuania · component of the indicator “{x.tevas.pavadinimas}”"),
                    t("Šaltiniai – žr. pagrindinį rodiklį", "Sources – see the main indicator"),
                    [(t("Lietuva", "Lithuania"), s)], vnt=vnt, dec=x.dec, nuo_nulio=False, zenklas=x.zenklas)
                x.grafiko_html = f.to_html(full_html=False, include_plotlyjs=False,
                                           config={**grafiko_cfg, **({} if en() else {"locale": "lt"})})
                x.lentele_eil = [(d, v) for d, v in zip(s.index, s.values)][::-1][:12]
                x.metine = all(d.month == 1 and d.day == 1 for d in s.index)
            else:
                x.grafiko_html, x.lentele_eil = "", []
            rasyk(f"rodikliai/{x.id}.html", "dalis.html", x=x, r=x.tevas, sritis=sritis)
    rasyk("index.html", "index.html", sritys=sritys, bendra=bendra, vertinti=vertinti,
          pagrindiniai=pagrindiniai, daliu_sk=daliu_sk, is_viso=len(visi),
          pagr_sk=sum(len(s["pagrindines"]) for s in sritys), kitu_sk=sum(len(s["kitos"]) for s in sritys))
    rasyk("metodika.html", "metodika.html", sritys=sritys)
    for i, (sritis, r) in enumerate(visi):
        ankstesnis = visi[i - 1][1] if i > 0 else None
        kitas = visi[i + 1][1] if i + 1 < len(visi) else None
        rasyk(f"rodikliai/{r.id}.html", "rodiklis.html", r=r, sritis=sritis, ankstesnis=ankstesnis, kitas=kitas)


def main():
    if ISVESTIS.exists():
        shutil.rmtree(ISVESTIS)
    generuok("lt", ISVESTIS, {})
    (ISVESTIS / ".nojekyll").touch()   # GitHub Pages: neapdoroti per Jekyll
    # Patikra: visos vidinės nuorodos turi vesti į esamus puslapius
    import re as _re
    truksta = sorted({(f.relative_to(ISVESTIS).as_posix(), h) for f in ISVESTIS.rglob("*.html")
                      for h in _re.findall(r'href="([^"#:]+\.html)', f.read_text(encoding="utf-8"))
                      if not (f.parent / h).resolve().exists()})
    if truksta:
        for puslapis, nuoroda in truksta[:20]:
            print(f"  ✗ neveikianti nuoroda: {puslapis} → {nuoroda}")
        raise SystemExit(f"Rasta neveikiančių nuorodų: {len(truksta)}")
    print(f"✅ Svetainė sugeneruota: {ISVESTIS}")


if __name__ == "__main__":
    main()
