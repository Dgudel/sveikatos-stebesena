# Sveikata skaičiais – Sveikatos vadybos studijų programos švieslentė

Statinė svetainė potencialiems studentams: 4 klausimai ir 8 pagrindiniai sveikatos sistemos rodikliai
(su sudedamosiomis dalimis – 22 vertinimai). Prie kiekvieno rodiklio – grafikai, palyginimas su ES, Latvija ir
Estija, vertinimas (gerėja / stabilu / prastėja) ir blokas „Ką čia gali pakeisti sveikatos vadybininkas?“
su nuoroda į studijų programą. Svetainę sugeneruoja Python, o GitHub Pages ją nemokamai paskelbia.

Sukurta pagal Vyriausybės veiklos stebėsenos švieslentės (`vyriausybes-veiklos-stebesena`) struktūrą.

## Rodikliai

| Sritis | Rodiklis | Šaltinis |
|---|---|---|
| 1. Ar Lietuvos žmonės sveiki? | Tikėtina gyvenimo trukmė (+ sveiko gyvenimo metai) | Eurostat `hlth_hlye` |
| | Išvengiamas mirtingumas (+ prevencija, gydymas) | Eurostat `hlth_cd_apr` |
| 2. Ar sistema pasiekia pacientą? | Negavo gydymo dėl laukimo eilių | Eurostat `hlth_silc_08` |
| | Pacientų mokėjimai iš savo kišenės | Eurostat `hlth_sha11_hf` |
| 3. Kas laiko sveikatos sistemą? | Slaugytojai, gydytojai ir jų amžius | Eurostat `hlth_rs_prs2`, `hlth_rs_phys` |
| | Sveikatos priežiūros išlaidos (◆ stebimas) | Eurostat `hlth_sha11_hf` |
| 4. Ar sveikatos srityje yra darbo? | Dirbantieji sveikatos ir globos srityje | Eurostat `lfsa_egan22d` |
| | Siūlomas atlyginimas ir laisvos darbo vietos | Užimtumo tarnyba (data.gov.lt `uzt/ldv`), Eurostat `jvs_q_nace2` |

## Prieš paskelbiant – PAKEISKITE

`generuoti.py` viršuje esančiame žodyne `PROGRAMA` įrašykite tikras nuorodas:

- `nuoroda` – Sveikatos vadybos programos puslapis MRU svetainėje;
- `registracija` – registracijos į renginį ar konsultaciją forma (pvz., MS Forms ar Google Forms).

Dabar abi nuorodos veda į `https://www.mruni.eu/`.

Taip pat verta su kolegomis peržiūrėti tekstus „Ką čia gali pakeisti sveikatos vadybininkas?“ – jie yra
kiekvieno rodiklio faile `rodikliai/*.py` (laukai `vadyba` ir `vadyba_trumpai`).

## Paskelbimas GitHub Pages (vieną kartą)

1. GitHub sukurkite naują viešą repozitoriją, pvz. `sveikatos-vadybos-svieslente`.
2. Šiame aplanke:
   ```bash
   git init -b main
   git add .
   git commit -m "Sveikatos švieslentė: pirmoji versija"
   git remote add origin https://github.com/<jūsų-vardas>/sveikatos-vadybos-svieslente.git
   git push -u origin main
   ```
3. GitHub repozitorijoje: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Po kelių minučių svetainė bus adresu `https://<jūsų-vardas>.github.io/sveikatos-vadybos-svieslente/`
   (eiga matoma skiltyje **Actions**).

## Atnaujinimas

GitHub Actions (`.github/workflows/svetaine.yml`) svetainę perkuria kiekvieną kartą įkėlus pakeitimus, **kas
pirmadienį** 5:00 UTC ir rankiniu būdu (Actions → Run workflow). Prieš tai atsisiunčiami naujausi duomenys:

- **Eurostat** – Lietuva, Latvija, Estija ir ES-27 (filtrai – `rodikliai/eurostat_duomenys.py`, `FILTRAI`);
- **Užimtumo tarnyba** per `get.data.gov.lt` – skelbimai profesijų grupėje „Sveikatos apsauga, farmacija“
  nuo 2018 m., suvedami į ketvirtinę suvestinę (`rodikliai/darbo_vietos.py`). Paskutiniai ketvirčiai rodomi tik
  praėjus 90 dienų, nes UŽT duomenys papildomi su vėlavimu.

Jei šaltinis nepasiekiamas, naudojami failai iš `duomenys/`, todėl svetainė niekada nelieka tuščia.

Savo kompiuteryje:

```bash
pip install -r requirements.txt
python generuoti.py                 # iš duomenys/ failų
ATNAUJINTI=1 python generuoti.py    # su naujausiais duomenimis
python -m http.server -d _site 8000 # peržiūra: http://localhost:8000
```

## Struktūra

```
generuoti.py              # sritys, rodiklių sąrašas, PROGRAMA nuorodos; generuoja _site/
rodikliai/
  bendra.py               # vertinimas, grafikų stilius, Rodiklis (su laukais vadyba, vadyba_trumpai)
  eurostat_duomenys.py    # Eurostat atsisiuntimas ir skaitymas
  pagalba.py              # LT / ES / LV / EE serijos ir standartinis grafikas
  gyvenimo_trukme.py, isvengiamas_mirtingumas.py     # 1 sritis
  sveikatos_eiles.py, paciento_mokejimai.py          # 2 sritis
  medikai.py, islaidos_sveikatai.py                  # 3 sritis
  uzimtieji.py, darbo_vietos.py                      # 4 sritis
sablonai/                 # HTML šablonai (Jinja)
statika/stilius.css       # išvaizda (sveikatos vadybos spalva – --vadyba)
duomenys/                 # duomenų failai (atsarginės kopijos)
```

## Ką galima pridėti vėliau

- Savivaldybių pasirinkimas (pagal `svieslente_savivaldybes`): prisirašiusieji prie PASP (`vlk/prisirase`),
  stacionaro lovos (`hi/lovos`).
- Paauglių gyvensena iš HI vaikų gyvensenos tyrimo (`hi/gyvensena/vaiku`, 2016–2024).
- Dalijimosi kortelės (PNG) Instagram / Reels'ams ir QR kodas.
