"""4.2 Laisvos darbo vietos sveikatos srityje ir siūlomas atlyginimas (Užimtumo tarnyba, data.gov.lt)
ir laisvų darbo vietų lygis sveikatos sektoriuje (Eurostat jvs_q_nace2)."""
import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go

from .bendra import DUOMENYS, SERIJOS, Rodiklis, dalis, i_data, ivertink, linijos, sk, stilius
from .eurostat_duomenys import serija
from .pagalba import eurostat_nuoroda

FAILAS = "uzt_sveikatos_darbo_vietos.csv"
PROFESIJOS = "uzt_sveikatos_profesijos.csv"
GRUPE = "Sveikatos apsauga, farmacija"
API = "https://get.data.gov.lt/datasets/gov/uzt/ldv/Vieta"
SLENKSTIS = 2.0     # % santykinis siūlomo atlyginimo pokytis per metus


def _atsisiusk():
    """Atsisiunčia UŽT skelbimus sveikatos srityje (nuo 2018 m.) iš data.gov.lt ir sudaro ketvirtinę suvestinę."""
    import time
    import requests
    laukai = "ikelimo_data,darbo_vietu_skaicius,vid_darbo_uzmokestis,valiuta,profesijos_pareigybes_pav"
    eil = []
    for metai in range(2018, date.today().year + 1):
        for k in range(4):
            nuo = date(metai, 3 * k + 1, 1)
            iki = date(metai + (k == 3), (3 * k + 3) % 12 + 1, 1)
            if nuo > date.today():
                break
            url = (f'{API}?select({laukai})&profesijos_grupes_pav="{GRUPE}"'
                   f'&ikelimo_data>="{nuo}"&ikelimo_data<"{iki}"&limit(20000)&format(json)')
            for bandymas in range(5):
                r = requests.get(url, timeout=120)
                if r.ok and "json" in r.headers.get("content-type", ""):
                    break
                time.sleep(3 * (bandymas + 1))
            r.raise_for_status()
            eil += r.json()["_data"]
            time.sleep(0.5)
    d = pd.DataFrame(eil)
    if len(d) < 10000:
        raise RuntimeError(f"per mažai įrašų ({len(d)})")
    d["data"] = pd.to_datetime(d["ikelimo_data"])
    d["laikotarpis"] = d["data"].dt.year.astype(str) + "K" + d["data"].dt.quarter.astype(str)
    d["vietos"] = d["darbo_vietu_skaicius"].fillna(1)
    d["du"] = d["vid_darbo_uzmokestis"].where((d["valiuta"] == "EUR") & (d["vid_darbo_uzmokestis"] > 0))
    suv = d.groupby("laikotarpis").agg(skelbimai=("vietos", "size"), darbo_vietos=("vietos", "sum"),
                                       du_mediana_eur=("du", "median")).reset_index()
    suv.to_csv(DUOMENYS / FAILAS, index=False)
    nuo = d["data"].max() - pd.DateOffset(years=1)
    p = (d[d["data"] > nuo].groupby("profesijos_pareigybes_pav")
         .agg(darbo_vietos=("vietos", "sum"), du_mediana_eur=("du", "median"))
         .sort_values("darbo_vietos", ascending=False).head(12).reset_index()
         .rename(columns={"profesijos_pareigybes_pav": "profesija"}))
    p["laikotarpis_nuo"] = nuo.date().isoformat()
    p.to_csv(DUOMENYS / PROFESIJOS, index=False)
    print(f"  ↓ data.gov.lt UŽT laisvos darbo vietos: {len(d)} skelbimų")


def _duomenys():
    if os.environ.get("ATNAUJINTI") == "1":
        try:
            _atsisiusk()
        except Exception as e:
            print(f"  ⚠ UŽT duomenys neatsisiųsti ({e}); naudojamas {FAILAS}")
    d = pd.read_csv(DUOMENYS / FAILAS)
    d["data"] = d["laikotarpis"].map(i_data)
    # UŽT duomenys papildomi su vėlavimu: rodome tik ketvirčius, pasibaigusius bent prieš 90 dienų
    pabaiga = d["data"] + pd.DateOffset(months=3) + pd.Timedelta(days=90)
    d = d[pabaiga <= pd.Timestamp(date.today())]
    return d.set_index("data").sort_index(), pd.read_csv(DUOMENYS / PROFESIJOS)


def rodiklis() -> Rodiklis:
    d, prof = _duomenys()
    du, vietos = d["du_mediana_eur"].dropna(), d["darbo_vietos"]
    pask_d = du.index[-1]
    pries_d = pask_d - pd.DateOffset(years=1)
    pask, pries = du.iloc[-1], du.get(pries_d)
    pokytis = (pask / pries - 1) * 100 if pries else None
    busena = ivertink(pokytis, "didesne", SLENKSTIS)
    laik = f"{pask_d.year}K{(pask_d.month - 1) // 3 + 1}"

    f1 = go.Figure()
    linijos(f1, [("Siūlomo atlyginimo mediana", du, SERIJOS[0])], vnt=" €", zenklas=False, dec=0)
    stilius(f1, "Kiek siūloma uždirbti sveikatos srityje?",
            "Užimtumo tarnybos skelbimų sveikatos srityje siūlomo vidutinio darbo užmokesčio mediana, eur (prieš mokesčius), ketvirčiais",
            "Šaltinis: Užimtumo tarnyba, data.gov.lt (uzt/ldv); skaičiavimas", vnt=" €", nulio_linija=False)
    f1.update_yaxes(rangemode="tozero")

    f2 = go.Figure()
    f2.add_trace(go.Bar(x=vietos.index, y=vietos.values, marker_color=SERIJOS[0], name="Darbo vietos",
                        hovertemplate="%{y:.0f} darbo vietų<extra></extra>"))
    stilius(f2, "Kiek darbo vietų siūloma?", "Užimtumo tarnyboje užregistruotos laisvos darbo vietos sveikatos srityje, ketvirčiais",
            "Šaltinis: Užimtumo tarnyba, data.gov.lt (uzt/ldv); skaičiavimas", vnt="", nulio_linija=False)

    p = prof.sort_values("du_mediana_eur")
    f3 = go.Figure(go.Bar(x=p["du_mediana_eur"], y=p["profesija"], orientation="h", marker_color=SERIJOS[0],
                          customdata=p["darbo_vietos"],
                          hovertemplate="%{y}: %{x:.0f} € · %{customdata} darbo vietų<extra></extra>"))
    stilius(f3, "Dažniausiai ieškomi specialistai ir jiems siūlomas atlyginimas",
            f"12 profesijų, kurioms skelbta daugiausia darbo vietų nuo {prof['laikotarpis_nuo'].iloc[0]}; siūlomo atlyginimo mediana, eur",
            "Šaltinis: Užimtumo tarnyba, data.gov.lt (uzt/ldv); skaičiavimas", vnt=" €", nulio_linija=False, aukstis=560)
    f3.update_layout(hovermode="closest", margin=dict(l=10, r=40, t=120, b=95))
    f3.update_xaxes(ticksuffix=" €", tickformat=",.0f", showgrid=True, gridcolor="#e6e5e1")
    f3.update_yaxes(ticksuffix="", gridcolor="rgba(0,0,0,0)")
    grafikai = [f1, f2, f3]

    try:
        jv_q = serija("jvs_q_nace2", "LT", s_adj="NSA", nace_r2="Q", sizeclas="TOTAL", indic_em="JVR")
        jv_v = serija("jvs_q_nace2", "LT", s_adj="NSA", nace_r2="A-S", sizeclas="TOTAL", indic_em="JVR")
        f4 = go.Figure()
        linijos(f4, [("Sveikatos priežiūra ir socialinis darbas", jv_q[jv_q.index >= "2015"], SERIJOS[0]),
                     ("Visa ekonomika", jv_v[jv_v.index >= "2015"], SERIJOS[1])], vnt=" %", zenklas=False)
        stilius(f4, "Ar sveikatos sektoriuje sunkiau rasti darbuotojų?",
                "Laisvų darbo vietų lygis Lietuvoje, % visų darbo vietų (laisvos ir užimtos), ketvirčiais",
                "Šaltinis: Eurostat, jvs_q_nace2", vnt=" %", nulio_linija=False)
        f4.update_yaxes(rangemode="tozero")
        grafikai.append(f4)
    except (ValueError, KeyError, FileNotFoundError):
        jv_q = None

    lentele = d[["laikotarpis", "skelbimai", "darbo_vietos", "du_mediana_eur"]].copy()
    kryptis = "padidėjo" if (pokytis or 0) > 0 else "sumažėjo"
    tekstas = (f"{pask_d.year} m. {(pask_d.month - 1) // 3 + 1} ketv. Užimtumo tarnybos skelbimuose sveikatos srityje "
               f"siūlomo atlyginimo mediana buvo {sk(pask, False, 0)} € prieš mokesčius")
    tekstas += (f"; per metus ji {kryptis} {sk(abs(pokytis), False)} %." if pokytis is not None else ".")
    tekstas += f" Per ketvirtį užregistruota {sk(vietos.iloc[-1], False, 0)} laisvų darbo vietų."
    top = prof.iloc[0]
    papildomai = [(sk(vietos.iloc[-1], False, 0), f"laisvų darbo vietų, {pask_d.year} m. {(pask_d.month - 1) // 3 + 1} ketv."),
                  (f"{sk(top['du_mediana_eur'], False, 0)} €", f"siūloma pareigybei „{top['profesija']}“ (daugiausia skelbimų)")]
    vsp = prof[prof["profesija"].str.contains("Visuomenės sveikatos", na=False)]
    if len(vsp):
        papildomai.append((f"{sk(vsp['du_mediana_eur'].iloc[0], False, 0)} €", "siūloma visuomenės sveikatos specialistui"))
    _dalys = [dalis("Laisvos darbo vietos", vietos, "didesne", 5.0, budas="proc", vienetai="", dec=0)]
    if jv_q is not None:
        _dalys.append(dalis("Laisvų darbo vietų lygis sveikatos sektoriuje", jv_q, "didesne", 0.2, budas="info"))
    return Rodiklis(
        id="darbo-vietos",
        pavadinimas="Siūlomas atlyginimas sveikatos srityje",
        trumpas_aprasas="skelbimų atlyginimo mediana, prieš mokesčius",
        reiksme=pask, vienetai=" €", laikotarpis=laik, busena=busena,
        zenklas=False, dec=0, spark_nuo_nulio=False,
        vertinimo_taisykle=f"Gerėja, kai siūlomo atlyginimo mediana, lyginant su tuo pačiu ketvirčiu prieš metus, "
                           f"padidėja daugiau nei {sk(SLENKSTIS, False)} %; prastėja, kai sumažėja daugiau nei "
                           f"{sk(SLENKSTIS, False)} %; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=tekstas,
        sparkline=du,
        grafikai=grafikai,
        dalys=_dalys,
        vadyba_trumpai="Kas ketvirtį – apie tūkstantis naujų darbo vietų sveikatos srityje.",
        vadyba=("Sveikatos įstaigos nuolat ieško darbuotojų – ir medikų, ir tų, kurie organizuoja jų darbą. "
                "Sveikatos vadybos absolventai dirba skyrių vadovais, paslaugų ir pacientų srautų koordinatoriais, "
                "kokybės vadybininkais, projektų vadovais ligoninėse, ligonių kasose, savivaldybių visuomenės "
                "sveikatos biuruose ir privačiose klinikose. O tie, kurie jau dirba medikais, studijuodami vadybą "
                "gali tapti komandų vadovais."),
        apibrezimas=("Užimtumo tarnybos registruotos laisvos darbo vietos profesijų grupėje „Sveikatos apsauga, "
                     "farmacija“. Atlyginimas – darbdavio nurodytas vidutinis siūlomas mėnesinis darbo užmokestis "
                     "(prieš mokesčius); skaičiuojama skelbimų, kuriuose jis nurodytas, mediana. Laisvų darbo vietų "
                     "lygis (Eurostat) – laisvų darbo vietų dalis visose darbo vietose."),
        pastabos=["Ne visi darbdaviai skelbia laisvas vietas per Užimtumo tarnybą, todėl skaičiai rodo tendenciją, "
                  "o ne visą darbo rinką. Vadovaujančios pareigos dažnai skelbiamos kitur.",
                  "Paskutiniai ketvirčiai neberodomi, kol duomenys papildomi (90 dienų po ketvirčio pabaigos).",
                  "Skelbimuose nurodytas atlyginimas gali skirtis nuo faktiškai mokamo."],
        saltiniai=[("Užimtumo tarnyba – laisvos darbo vietos (data.gov.lt)", "https://get.data.gov.lt/datasets/gov/uzt/ldv/:ns"),
                   eurostat_nuoroda("jvs_q_nace2")],
        papildomai=papildomai,
        lentele=lentele,
    )
