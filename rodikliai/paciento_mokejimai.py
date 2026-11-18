"""2.2 Kiek už sveikatos priežiūrą pacientai moka iš savo kišenės (Eurostat hlth_sha11_hf, HF3)."""
from .bendra import Rodiklis, dalis, ivertink, sk
from .pagalba import eurostat_nuoroda, lentele_is, saliu_grafikas, salys

KODAS = "hlth_sha11_hf"
SLENKSTIS = 0.5     # proc. punkto


def rodiklis() -> Rodiklis:
    dalis_proc = salys(KODAS, icha11_hf="HF3", unit="PC_CHE")
    eur = salys(KODAS, icha11_hf="HF3", unit="EUR_HAB")
    lt, es = dalis_proc["LT"], dalis_proc.get("EU27_2020")
    pask, pries = lt.iloc[-1], lt.iloc[-2]
    metai, ankst = lt.index[-1].year, lt.index[-2].year
    pokytis = pask - pries
    busena = ivertink(pokytis, "mazesne", SLENKSTIS)

    f1 = saliu_grafikas(dalis_proc, "Kiek pacientai sumoka patys",
                        "Namų ūkių tiesioginiai mokėjimai, % visų einamųjų sveikatos priežiūros išlaidų",
                        "Šaltinis: Eurostat, hlth_sha11_hf", vnt=" %")
    f2 = saliu_grafikas(eur, "Pacientų mokėjimai eurais",
                        "Namų ūkių tiesioginiai mokėjimai už sveikatos priežiūrą, eur vienam gyventojui per metus",
                        "Šaltinis: Eurostat, hlth_sha11_hf", vnt=" €", dec=0)

    lentele = lentele_is(dalis_proc, "is_kisenes_proc").join(
        lentele_is(eur, "is_kisenes_eur_gyv").drop(columns="metai"), how="outer")
    kryptis = "sumažėjo" if pokytis < 0 else "padidėjo"
    tekstas = (f"{metai} m. Lietuvos gyventojai patys sumokėjo {sk(pask, False)} % visų sveikatos priežiūros išlaidų "
               f"({ankst} m. – {sk(pries, False)} %). Dalis {kryptis} {sk(abs(pokytis), False)} proc. punkto.")
    if es is not None:
        tekstas += f" ES vidurkis – {sk(es.iloc[-1], False)} % ({es.index[-1].year} m.)."
    return Rodiklis(
        id="paciento-mokejimai",
        pavadinimas="Pacientų mokėjimai iš savo kišenės",
        trumpas_aprasas="visų sveikatos priežiūros išlaidų",
        reiksme=pask, vienetai="%", laikotarpis=str(metai), busena=busena,
        zenklas=False, dec=1, spark_nuo_nulio=True,
        vertinimo_taisykle=f"Gerėja, kai dalis per metus sumažėja daugiau nei {sk(SLENKSTIS, False)} proc. punkto; "
                           f"prastėja, kai padidėja daugiau nei {sk(SLENKSTIS, False)} proc. punkto; kitu atveju – stabilu.",
        vertinimo_paaiskinimas=tekstas,
        sparkline=lt[lt.index.year >= 2012],
        grafikai=[f1, f2],
        dalys=[dalis("Mokėjimai eurais vienam gyventojui", eur["LT"], "info", 0, budas="info", vienetai=" €", dec=0)],
        vadyba_trumpai="Kas už ką moka – sveikatos finansų vadybos klausimas.",
        vadyba=("Didelę dalį savo kišenės išlaidų pacientai skiria vaistams ir odontologo paslaugoms. "
                "Sveikatos vadybininkas, dirbantis ligonių kasoje, ministerijoje ar įstaigoje, sprendžia, kokios "
                "paslaugos ir vaistai kompensuojami, kaip sudaromos sutartys ir kaip pinigai pasiekia pacientą. "
                "Nuo šių sprendimų priklauso, ar gydymas lieka prieinamas ir mažas pajamas gaunantiems."),
        apibrezimas=("Namų ūkių tiesioginiai mokėjimai (angl. out-of-pocket) – pinigai, kuriuos gyventojai patys sumoka "
                     "už vaistus, odontologo, privačių klinikų paslaugas, priemokas ir pan., neskaičiuojant privalomojo "
                     "sveikatos draudimo įmokų. Rodoma kaip dalis visų einamųjų sveikatos priežiūros išlaidų "
                     "(Sveikatos sąskaitų sistema, SHA 2011)."),
        pastabos=["PSO laiko, kad kai tiesioginiai mokėjimai viršija 15–20 % visų išlaidų, dalis gyventojų dėl kainos "
                  "atsisako gydymo arba patiria finansinių sunkumų.",
                  "Naujausių metų duomenys gali būti preliminarūs."],
        saltiniai=[eurostat_nuoroda(KODAS)],
        papildomai=[(f"{sk(eur['LT'].iloc[-1], False, 0)} €", f"vienam gyventojui per metus, {eur['LT'].index[-1].year} m."),
                    *([(f"{sk(es.iloc[-1], False)} %", f"ES-27 vidurkis, {es.index[-1].year} m.")] if es is not None else [])],
        lentele=lentele,
    )
