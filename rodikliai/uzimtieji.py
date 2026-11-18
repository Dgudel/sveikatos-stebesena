"""4.1 Dirbantieji sveikatos priežiūros ir socialinės globos sektoriuje (Eurostat lfsa_egan22d, NACE Q86–Q88)."""
import plotly.graph_objects as go

from .bendra import SERIJOS, Rodiklis, dalis, ivertink, linijos, sk, stilius
from .pagalba import eurostat_nuoroda, saliu_grafikas, salys

KODAS = "lfsa_egan22d"
SLENKSTIS = 1.0     # % santykinis pokytis


def _sektorius(nace):
    return salys(KODAS, age="Y15-74", sex="T", unit="THS_PER", nace_r2=nace)


def rodiklis() -> Rodiklis:
    q86, q87, q88, viso = _sektorius("Q86"), _sektorius("Q87"), _sektorius("Q88"), _sektorius("TOTAL")
    q = {g: (q86[g] + q87[g] + q88[g]).dropna() for g in q86 if g in q87 and g in q88}
    dalis_proc = {g: (q[g] / viso[g] * 100).dropna() for g in q if g in viso}
    lt = q["LT"]
    pask, pries = lt.iloc[-1], lt.iloc[-2]
    metai, ankst = lt.index[-1].year, lt.index[-2].year
    pokytis = (pask / pries - 1) * 100
    busena = ivertink(pokytis, "didesne", SLENKSTIS)

    f1 = go.Figure()
    nuo = "2010-01-01"
    linijos(f1, [("Sveikatos priežiūra (ligoninės, poliklinikos ir kt.)", q86["LT"][q86["LT"].index >= nuo], SERIJOS[0]),
                 ("Stacionarinė globa ir slauga", q87["LT"][q87["LT"].index >= nuo], SERIJOS[2]),
                 ("Nestacionarinės socialinės paslaugos", q88["LT"][q88["LT"].index >= nuo], SERIJOS[3])],
            vnt=" tūkst.", zenklas=False, dec=1, zymekliai=True)
    stilius(f1, "Kiek žmonių dirba sveikatos ir globos srityje?", "Užimtieji Lietuvoje, tūkst. (15–74 m.)",
            "Šaltinis: Eurostat, lfsa_egan22d (darbo jėgos tyrimas)", vnt="", nulio_linija=False, metiniai=True)
    f1.update_yaxes(rangemode="tozero")
    f2 = saliu_grafikas(dalis_proc, "Kokia dalis dirbančiųjų – sveikatos ir globos srityje?",
                        "Sveikatos priežiūros ir socialinio darbo veikla (NACE Q), % visų užimtųjų",
                        "Šaltinis: Eurostat, lfsa_egan22d; skaičiavimas", vnt=" %")

    import pandas as pd
    lentele = pd.DataFrame({"LT_Q86_tukst": q86["LT"], "LT_Q87_tukst": q87["LT"], "LT_Q88_tukst": q88["LT"],
                            "LT_Q_viso_tukst": lt, **{f"{g}_Q_dalis_proc": s for g, s in dalis_proc.items()}}).sort_index()
    lentele.insert(0, "metai", lentele.index.year)
    d_lt = dalis_proc["LT"]
    es = dalis_proc.get("EU27_2020")
    kryptis = "padaugėjo" if pokytis > 0 else "sumažėjo"
    tekstas = (f"{metai} m. sveikatos priežiūros ir socialinio darbo srityje Lietuvoje dirbo {sk(pask, False)} tūkst. "
               f"žmonių – {sk(d_lt.iloc[-1], False)} % visų užimtųjų. Per metus jų {kryptis} {sk(abs(pokytis), False)} %.")
    if es is not None:
        tekstas += f" ES šioje srityje dirba {sk(es.iloc[-1], False)} % užimtųjų."
    return Rodiklis(
        id="uzimtieji-sveikatos-sektoriuje",
        pavadinimas="Dirbantieji sveikatos ir globos srityje",
        trumpas_aprasas="tūkst. užimtųjų",
        reiksme=pask, vienetai="", laikotarpis=str(metai), busena=busena,
        zenklas=False, dec=1, spark_nuo_nulio=False,
        vertinimo_taisykle=f"Gerėja, kai dirbančiųjų per metus padaugėja daugiau nei {sk(SLENKSTIS, False)} %; "
                           f"prastėja, kai sumažėja daugiau nei {sk(SLENKSTIS, False)} %; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=tekstas,
        sparkline=lt[lt.index.year >= 2010],
        grafikai=[f1, f2],
        dalys=[dalis("Dalis visų užimtųjų", d_lt, "didesne", 0.2)],
        vadyba_trumpai="Kiekvienai komandai ir įstaigai reikia vadovo, koordinatoriaus, planuotojo.",
        vadyba=("Sveikatos ir globos srityje dirba daugiau nei 100 tūkst. žmonių – ligoninėse, poliklinikose, "
                "slaugos ir globos namuose, visuomenės sveikatos biuruose, ligonių kasose. Visoms šioms įstaigoms "
                "reikia žmonių, kurie supranta ir mediciną, ir vadybą: skyrių vadovų, paslaugų koordinatorių, "
                "kokybės ir projektų vadovų. Visuomenei senstant, šios srities darbuotojų poreikis didės."),
        apibrezimas=("Užimtieji pagal ekonominę veiklą (EVRK 2 / NACE Rev. 2): Q86 – žmonių sveikatos priežiūros veikla "
                     "(ligoninės, gydytojų praktika, odontologija ir kt.), Q87 – kita stacionarinė globos veikla, "
                     "Q88 – nestacionarinės socialinio darbo paslaugos. Darbo jėgos tyrimo duomenys, 15–74 m."),
        pastabos=["Tai apklausos duomenys, todėl nedideli metiniai pokyčiai gali būti atsitiktiniai.",
                  "Į skaičių patenka visi šių įstaigų darbuotojai, ne tik medikai."],
        saltiniai=[eurostat_nuoroda(KODAS)],
        papildomai=[(f"{sk(d_lt.iloc[-1], False)} %", f"visų Lietuvos užimtųjų, {d_lt.index[-1].year} m."),
                    *([(f"{sk(es.iloc[-1], False)} %", f"ES-27, {es.index[-1].year} m.")] if es is not None else [])],
        lentele=lentele,
    )
