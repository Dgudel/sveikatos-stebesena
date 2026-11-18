"""3.1 Slaugytojai ir gydytojai 100 000 gyventojų, gydytojų amžius (Eurostat hlth_rs_prs2, hlth_rs_phys)."""
import plotly.graph_objects as go

from .bendra import SERIJOS, Rodiklis, dalis, ivertink, sk, stilius
from .eurostat_duomenys import serija
from .pagalba import eurostat_nuoroda, lentele_is, saliu_grafikas, salys

KODAS = "hlth_rs_prs2"
SLENKSTIS = 5.0     # specialistų 100 000 gyv.


def _amzius():
    """Praktikuojančių gydytojų dalis pagal amžiaus grupes, % (tik Lietuva)."""
    grupes = [("Y_LT35", "iki 35 m."), ("Y35-44", "35–44 m."), ("Y45-54", "45–54 m."),
              ("Y55-64", "55–64 m."), ("Y65-74", "65–74 m."), ("Y_GE75", "75 m. ir vyresni")]
    viso = serija("hlth_rs_phys", "LT", age="TOTAL", sex="T", unit="NR")
    return {pav: serija("hlth_rs_phys", "LT", age=k, sex="T", unit="NR") / viso * 100 for k, pav in grupes}


def rodiklis() -> Rodiklis:
    nrs = salys(KODAS, wstatus="PRACT", med_spec="NRS", unit="P_HTHAB")
    phys = salys(KODAS, wstatus="PRACT", med_spec="PHYS", unit="P_HTHAB")
    lt = nrs["LT"]
    pask, pries = lt.iloc[-1], lt.iloc[-2]
    metai, ankst = lt.index[-1].year, lt.index[-2].year
    pokytis = pask - pries
    busena = ivertink(pokytis, "didesne", SLENKSTIS)
    santykis = (nrs["LT"] / phys["LT"]).dropna()

    f1 = saliu_grafikas(nrs, "Kiek turime slaugytojų?", "Praktikuojantys slaugytojai 100 000 gyventojų",
                        "Šaltinis: Eurostat, hlth_rs_prs2", dec=0)
    f2 = saliu_grafikas(phys, "Kiek turime gydytojų?", "Praktikuojantys gydytojai 100 000 gyventojų",
                        "Šaltinis: Eurostat, hlth_rs_prs2", dec=0)
    grafikai = [f1, f2]
    papildomai = [(sk(phys["LT"].iloc[-1], False, 0), f"gydytojų 100 000 gyv., {phys['LT'].index[-1].year} m."),
                  (sk(santykis.iloc[-1], False), f"slaugytojo vienam gydytojui, {santykis.index[-1].year} m.")]
    try:
        am = _amzius()
        vyr = (am["55–64 m."] + am["65–74 m."] + am["75 m. ir vyresni"]).dropna()
        f3 = go.Figure()
        spalvos = ["#9cc3ee", "#5c9de0", SERIJOS[0], "#eda100", "#eb6834", "#b8461b"]
        for (pav, s), sp in zip(am.items(), spalvos):
            s = s[s.index.year >= 2012]
            f3.add_trace(go.Bar(x=s.index, y=s.values, name=pav, marker_color=sp,
                                hovertemplate=f"{pav}: %{{y:.1f}} %<extra></extra>"))
        f3.update_layout(barmode="stack")
        stilius(f3, "Kas gydys po 10 metų?", "Praktikuojančių gydytojų pasiskirstymas pagal amžių, % (Lietuva)",
                "Šaltinis: Eurostat, hlth_rs_phys; skaičiavimas", nulio_linija=False, metiniai=True)
        f3.update_yaxes(range=[0, 100])
        grafikai.append(f3)
        papildomai.append((f"{sk(vyr.iloc[-1], False, 0)} %", f"gydytojų yra 55 m. ir vyresni, {vyr.index[-1].year} m."))
    except (ValueError, KeyError):
        vyr = None

    lentele = (lentele_is(nrs, "slaugytojai_100k")
               .join(lentele_is(phys, "gydytojai_100k").drop(columns="metai"), how="outer"))
    _dalys = [dalis("Praktikuojantys gydytojai", phys["LT"], "didesne", SLENKSTIS, vienetai="", dec=0, slenkscio_vnt=""),
              dalis("Slaugytojų skaičius vienam gydytojui", santykis, "didesne", 0.05, vienetai="", dec=2, slenkscio_vnt="")]
    if vyr is not None:
        _dalys.append(dalis("55 m. ir vyresnių gydytojų dalis", vyr, "mazesne", 1.0))
    kryptis = "padaugėjo" if pokytis > 0 else "sumažėjo"
    return Rodiklis(
        id="medikai",
        pavadinimas="Slaugytojai 100 000 gyventojų",
        trumpas_aprasas="praktikuojančių slaugytojų",
        reiksme=pask, vienetai="", laikotarpis=str(metai), busena=busena,
        zenklas=False, dec=0, spark_nuo_nulio=False,
        vertinimo_taisykle=f"Gerėja, kai slaugytojų per metus padaugėja daugiau nei {sk(SLENKSTIS, False, 0)} "
                           f"100 000 gyventojų; prastėja, kai sumažėja daugiau nei {sk(SLENKSTIS, False, 0)}; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=(f"{metai} m. 100 000 Lietuvos gyventojų teko {sk(pask, False, 0)} praktikuojančių "
                                f"slaugytojų ({ankst} m. – {sk(pries, False, 0)}); per metus {kryptis} "
                                f"{sk(abs(pokytis), False, 0)}. Vienam gydytojui tenka {sk(santykis.iloc[-1], False)} "
                                f"slaugytojo."),
        sparkline=lt[lt.index.year >= 2010],
        grafikai=grafikai,
        dalys=_dalys,
        vadyba_trumpai="Žmogiškųjų išteklių planavimas – kiek ir kokių specialistų reikės po 10 metų.",
        vadyba=("Lietuvoje gydytojų 100 000 gyventojų yra daugiau nei vidutiniškai ES, tačiau maždaug du iš penkių jų – 55 m. "
                "ir vyresni, o slaugytojų vienam gydytojui tenka mažiau nei daugelyje šalių. Sveikatos vadybininkas "
                "planuoja personalą, organizuoja darbą komandomis, kad slaugytojai ir kiti specialistai perimtų dalį "
                "užduočių, ir kuria sąlygas, kad jauni specialistai liktų dirbti regionuose."),
        apibrezimas=("Praktikuojantys slaugytojai ir gydytojai – specialistai, tiesiogiai teikiantys paslaugas "
                     "pacientams (ne administracijoje ar moksle), 100 000 gyventojų. Slaugytojai – su ES pripažinta "
                     "kvalifikacija. Gydytojų amžiaus struktūra – Lietuvos praktikuojančių gydytojų pasiskirstymas pagal amžių."),
        pastabos=["Šalių duomenys gali būti nevisiškai palyginami dėl skirtingų registrų ir apibrėžimų.",
                  "Naujausių metų duomenys skelbiami su 1–2 metų vėlavimu."],
        saltiniai=[eurostat_nuoroda(KODAS), eurostat_nuoroda("hlth_rs_phys"),
                   ("Higienos institutas – visuomenės sveikatos specialistai (data.gov.lt)",
                    "https://get.data.gov.lt/datasets/gov/hi/specialistai/:ns")],
        papildomai=papildomai,
        lentele=lentele,
    )
