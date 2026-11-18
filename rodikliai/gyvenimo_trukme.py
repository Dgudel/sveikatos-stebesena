"""1.1 Tikėtina gyvenimo trukmė ir sveiko gyvenimo metai (Eurostat hlth_hlye)."""
from .bendra import Rodiklis, dalis, ivertink, sk
from .pagalba import eurostat_nuoroda, lentele_is, saliu_grafikas, salys

KODAS = "hlth_hlye"
SLENKSTIS = 0.2     # metų


def rodiklis() -> Rodiklis:
    gt = salys(KODAS, hlth_hle="LE_Y0", sex="T", unit="YR")
    sgm = salys(KODAS, hlth_hle="HLY_Y0", sex="T", unit="YR")
    lt, es = gt["LT"], gt.get("EU27_2020")
    pask, pries = lt.iloc[-1], lt.iloc[-2]
    metai, ankst = lt.index[-1].year, lt.index[-2].year
    pokytis = pask - pries
    busena = ivertink(pokytis, "didesne", SLENKSTIS)
    skirtumas = es[es.index == lt.index[-1]].iloc[0] - pask if es is not None and lt.index[-1] in es.index else None

    f1 = saliu_grafikas(gt, "Kiek vidutiniškai gyvename?", "Tikėtina gyvenimo trukmė gimus, metai",
                        "Šaltinis: Eurostat, hlth_hlye", vnt=" m.", nuo_nulio=False)
    f2 = saliu_grafikas(sgm, "Kiek metų gyvename sveiki?",
                        "Sveiko gyvenimo metai gimus – kiek metų tikimasi gyventi be veiklą ribojančių sveikatos sutrikimų",
                        "Šaltinis: Eurostat, hlth_hlye", vnt=" m.", nuo_nulio=False)

    lentele = lentele_is(gt, "gyvenimo_trukme_m").join(
        lentele_is(sgm, "sveiko_gyvenimo_metai").drop(columns="metai"), how="outer")

    tekstas = (f"{metai} m. Lietuvoje gimęs žmogus vidutiniškai gyvens {sk(pask, False)} m. "
               f"({ankst} m. – {sk(pries, False)} m.).")
    if skirtumas is not None:
        tekstas += f" Tai {sk(skirtumas, False)} m. trumpiau nei ES vidurkis ({sk(es.loc[lt.index[-1]], False)} m.)."
    return Rodiklis(
        id="gyvenimo-trukme",
        pavadinimas="Tikėtina gyvenimo trukmė",
        trumpas_aprasas="metų, gimusiems šiais metais",
        reiksme=pask, vienetai=" m.", laikotarpis=str(metai), busena=busena,
        zenklas=False, dec=1, spark_nuo_nulio=False,
        vertinimo_taisykle=f"Gerėja, kai per metus pailgėja daugiau nei {sk(SLENKSTIS, False)} m.; "
                           f"prastėja, kai sutrumpėja daugiau nei {sk(SLENKSTIS, False)} m.; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=tekstas,
        sparkline=lt[lt.index.year >= 2010],
        grafikai=[f1, f2],
        dalys=[dalis("Sveiko gyvenimo metai", sgm["LT"], "didesne", 0.5, vienetai=" m.", slenkscio_vnt=" m.")],
        vadyba_trumpai="Prevencija ir ankstyva diagnostika – vadybos sprendimai, kurie prailgina gyvenimą.",
        vadyba=("Gyvenimo trukmė priklauso ne tik nuo gydytojų. Sveikatos vadybininkas planuoja prevencines programas, "
                "organizuoja, kad pacientai laiku pasitikrintų, ir paskirsto lėšas taip, kad jos duotų daugiausia "
                "sveikų gyvenimo metų. Tarp Lietuvos ir ES vidurkio vis dar – keleri metai: tai darbas ateities "
                "sveikatos sistemos vadovams."),
        apibrezimas=("Tikėtina gyvenimo trukmė gimus – kiek metų vidutiniškai gyventų gimęs žmogus, jei visą gyvenimą "
                     "mirtingumas pagal amžių išliktų toks, koks yra dabar. Sveiko gyvenimo metai – kiek iš jų "
                     "tikimasi pragyventi be ilgalaikių veiklą ribojančių sveikatos sutrikimų (pagal EU-SILC apklausą)."),
        pastabos=["2020–2021 m. gyvenimo trukmę sumažino COVID-19 pandemija.",
                  "Sveiko gyvenimo metai skaičiuojami iš apklausos duomenų, todėl jų pokyčiai tarp metų gali būti atsitiktiniai."],
        saltiniai=[eurostat_nuoroda(KODAS),
                   ("Higienos institutas – Mirties priežastys", "https://www.hi.lt")],
        papildomai=[(f"{sk(sgm['LT'].iloc[-1], False)} m.", f"sveiko gyvenimo metai, {sgm['LT'].index[-1].year} m."),
                    *([(f"{sk(es.iloc[-1], False)} m.", f"ES-27 vidurkis, {es.index[-1].year} m.")] if es is not None else [])],
        lentele=lentele,
    )
