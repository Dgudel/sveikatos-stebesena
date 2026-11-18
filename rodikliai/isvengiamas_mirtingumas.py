"""1.2 Išvengiamas mirtingumas: mirtys, kurių galima išvengti prevencija ar laiku suteiktu gydymu (Eurostat hlth_cd_apr)."""
from .bendra import Rodiklis, dalis, ivertink, sk
from .pagalba import eurostat_nuoroda, lentele_is, saliu_grafikas, salys

KODAS = "hlth_cd_apr"
SLENKSTIS = 2.0     # % santykinis pokytis per metus


def rodiklis() -> Rodiklis:
    f = dict(icd10="TOTAL", sex="T", unit="RT")
    vis = salys(KODAS, mortalit="TOTAL", **f)
    prv = salys(KODAS, mortalit="PRVT", **f)
    trt = salys(KODAS, mortalit="TRT", **f)
    lt, es = vis["LT"], vis.get("EU27_2020")
    pask, pries = lt.iloc[-1], lt.iloc[-2]
    metai, ankst = lt.index[-1].year, lt.index[-2].year
    pokytis = (pask / pries - 1) * 100
    busena = ivertink(pokytis, "mazesne", SLENKSTIS)

    f1 = saliu_grafikas(vis, "Mirtys, kurių buvo galima išvengti",
                        "Jaunesnių nei 75 m. mirtys 100 000 gyventojų (standartizuotas rodiklis)",
                        "Šaltinis: Eurostat, hlth_cd_apr", dec=0)
    f2 = saliu_grafikas(prv, "…išvengiamos prevencija",
                        "Mirtys 100 000 gyv., kurių būtų išvengta sveikesne gyvensena, skiepais, saugia aplinka",
                        "Šaltinis: Eurostat, hlth_cd_apr", dec=0)
    f3 = saliu_grafikas(trt, "…išvengiamos laiku suteiktu gydymu",
                        "Mirtys 100 000 gyv., kurių būtų išvengta laiku ir kokybiškai gydant",
                        "Šaltinis: Eurostat, hlth_cd_apr", dec=0)

    lentele = (lentele_is(vis, "isvengiamas_viso_100k")
               .join(lentele_is(prv, "prevencija_100k").drop(columns="metai"), how="outer")
               .join(lentele_is(trt, "gydymas_100k").drop(columns="metai"), how="outer"))

    kryptis = "sumažėjo" if pokytis < 0 else "padidėjo"
    tekstas = (f"{metai} m. Lietuvoje {sk(pask, False, 0)} iš 100 000 gyventojų mirė nuo priežasčių, kurių buvo galima "
               f"išvengti ({ankst} m. – {sk(pries, False, 0)}). Rodiklis {kryptis} {sk(abs(pokytis), False)} %.")
    if es is not None and lt.index[-1] in es.index:
        tekstas += f" Tai {sk(pask / es.loc[lt.index[-1]], False)} karto daugiau nei ES vidurkis ({sk(es.loc[lt.index[-1]], False, 0)})."
    return Rodiklis(
        id="isvengiamas-mirtingumas",
        pavadinimas="Išvengiamas mirtingumas",
        trumpas_aprasas="mirčių 100 000 gyv.",
        reiksme=pask, vienetai="", laikotarpis=str(metai), busena=busena,
        zenklas=False, dec=0, spark_nuo_nulio=False,
        vertinimo_taisykle=f"Gerėja, kai rodiklis per metus sumažėja daugiau nei {sk(SLENKSTIS, False)} %; "
                           f"prastėja, kai padidėja daugiau nei {sk(SLENKSTIS, False)} %; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=tekstas,
        sparkline=lt[lt.index.year >= 2011],
        grafikai=[f1, f2, f3],
        dalys=[dalis("Išvengiamas prevencija", prv["LT"], "mazesne", SLENKSTIS, budas="proc", vienetai="", dec=0),
               dalis("Išvengiamas gydymu", trt["LT"], "mazesne", SLENKSTIS, budas="proc", vienetai="", dec=0)],
        vadyba_trumpai="Kiekviena šio skaičiaus dalis – sprendimas, kurį gali priimti sveikatos sistemos vadovas.",
        vadyba=("Didžioji šių mirčių dalis susijusi su prevencija: rūkymu, alkoholiu, traumomis, nepatikrinta sveikata. "
                "Vadybininkas organizuoja patikros programas, kviečia pacientus, matuoja, ar programos veikia. "
                "Likusi dalis – mirtys, kurių būtų išvengta laiku gydant: čia svarbu, kad pacientas nepasiklystų "
                "tarp šeimos gydytojo, specialisto ir ligoninės."),
        apibrezimas=("Išvengiamas mirtingumas – jaunesnių nei 75 m. asmenų mirtys nuo priežasčių, kurių daugumos būtų "
                     "galima išvengti veiksminga prevencija (pvz., plaučių vėžys, kepenų ligos, traumos) arba laiku "
                     "suteiktu kokybišku gydymu (pvz., insultas, dalis vėžio formų). EBPO ir Eurostat metodika, "
                     "rodiklis standartizuotas pagal amžių, todėl palyginamas tarp šalių."),
        pastabos=["Eurostat mirtingumo duomenys skelbiami su maždaug 2–3 metų vėlavimu.",
                  "2020–2021 m. rodiklį stipriai paveikė COVID-19 pandemija."],
        saltiniai=[eurostat_nuoroda(KODAS),
                   ("Higienos institutas – Sveikatos statistikos portalas", "https://stat.hi.lt")],
        papildomai=[(sk(prv["LT"].iloc[-1], False, 0), f"išvengiama prevencija, {prv['LT'].index[-1].year} m."),
                    (sk(trt["LT"].iloc[-1], False, 0), f"išvengiama gydymu, {trt['LT'].index[-1].year} m.")],
        lentele=lentele,
    )
