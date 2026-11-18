"""3.2 Sveikatos priežiūros išlaidos, % BVP ir eur gyventojui (Eurostat hlth_sha11_hf)."""
from .bendra import Rodiklis, dalis, sk
from .pagalba import eurostat_nuoroda, lentele_is, saliu_grafikas, salys

KODAS = "hlth_sha11_hf"


def rodiklis() -> Rodiklis:
    bvp = salys(KODAS, icha11_hf="TOT_HF", unit="PC_GDP")
    eur = salys(KODAS, icha11_hf="TOT_HF", unit="EUR_HAB")
    lt, es = bvp["LT"], bvp.get("EU27_2020")
    pask, metai = lt.iloc[-1], lt.index[-1].year

    f1 = saliu_grafikas(bvp, "Kiek šalis skiria sveikatai?", "Einamosios sveikatos priežiūros išlaidos, % BVP",
                        "Šaltinis: Eurostat, hlth_sha11_hf", vnt=" %")
    f2 = saliu_grafikas(eur, "Sveikatos išlaidos vienam gyventojui",
                        "Einamosios sveikatos priežiūros išlaidos, eur vienam gyventojui per metus",
                        "Šaltinis: Eurostat, hlth_sha11_hf", vnt=" €", dec=0)
    lentele = lentele_is(bvp, "islaidos_proc_BVP").join(
        lentele_is(eur, "islaidos_eur_gyv").drop(columns="metai"), how="outer")
    tekstas = f"{metai} m. sveikatos priežiūrai Lietuvoje išleista {sk(pask, False)} % BVP."
    if es is not None:
        tekstas += f" ES vidurkis – {sk(es.iloc[-1], False)} % ({es.index[-1].year} m.)."
    e = eur["LT"]
    tekstas += f" Vienam gyventojui teko {sk(e.iloc[-1], False, 0)} € ({e.index[-1].year} m.)."
    return Rodiklis(
        id="islaidos-sveikatai",
        pavadinimas="Sveikatos priežiūros išlaidos",
        trumpas_aprasas="BVP",
        reiksme=pask, vienetai="%", laikotarpis=str(metai), busena="info",
        zenklas=False, dec=1, spark_nuo_nulio=False,
        vertinimo_taisykle=("Informacinis rodiklis (◆ Stebimas): didesnės išlaidos savaime nereiškia geresnės "
                            "sveikatos, todėl kryptis nevertinama. Svarbu, kaip pinigai panaudojami – tai rodo kiti "
                            "švieslentės rodikliai."),
        vertinimo_paaiskinimas=tekstas,
        sparkline=lt[lt.index.year >= 2012],
        grafikai=[f1, f2],
        dalys=[dalis("Išlaidos vienam gyventojui", e, "didesne", 0, budas="info", vienetai=" €", dec=0)],
        vadyba_trumpai="Sveikatos sistemai per metus skiriama daugiau nei 5 mlrd. eurų – juos reikia valdyti.",
        vadyba=("Sveikatos sektorius – vienas didžiausių šalies biudžetų. Vadybininkai planuoja įstaigų biudžetus, "
                "derasi dėl paslaugų kainų, vertina, ar nauja technologija ar vaistas atsiperka, ir ieško būdų už tuos "
                "pačius pinigus suteikti daugiau ir geresnių paslaugų."),
        apibrezimas=("Einamosios sveikatos priežiūros išlaidos – visos per metus išleistos lėšos sveikatos priežiūros "
                     "paslaugoms ir prekėms (valstybės, privalomojo sveikatos draudimo, gyventojų ir kitos), be "
                     "investicijų į pastatus ir įrangą. Sveikatos sąskaitų sistema (SHA 2011)."),
        pastabos=["Naujausių metų duomenys gali būti preliminarūs.",
                  "Eurai vienam gyventojui – to meto kainomis, todėl dalis augimo susijusi su infliacija."],
        saltiniai=[eurostat_nuoroda(KODAS)],
        papildomai=[(f"{sk(e.iloc[-1], False, 0)} €", f"vienam gyventojui, {e.index[-1].year} m."),
                    *([(f"{sk(es.iloc[-1], False)} %", f"ES-27 vidurkis, {es.index[-1].year} m.")] if es is not None else [])],
        lentele=lentele,
    )
