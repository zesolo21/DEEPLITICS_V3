"""
Medien-/Metadaten-Anreicherung, 18.08.2026 (v7-Vorbereitung).

Nutzerwunsch: "debug the picture, jede Story braucht ein Bild, Personen/
Konzepte brauchen auch Bilder, verlinke Wikipedia, Theme-Farben pro Story."

Ergänzt `data/stories.json` um:
- `image_url` je Story: echtes, verlinkungssicheres Wikimedia-Commons-Bild
  statt der bisherigen News-CDN-Hotlinks (npr.brightspotcdn.com,
  aljazeera.com, kesq.b-cdn.net, fortune.com), die von 10 parallelen
  Recherche-Agenten (WebSearch/WebFetch) für jede Story neu verifiziert
  wurden. Grund: diese CDN-Links konnten in der QA nicht sicher als
  ladbar bestätigt werden (Sandbox blockt jeden Fetch zu diesen Domains),
  Wikimedia Commons ist der einzige Bild-Host, der in diesem Projekt
  bereits nachweislich zuverlässig im echten Browser lädt.
- `theme_category` + damit eine feste, nicht rotierende Kategorie-Farbe
  (6 Kategorien, s. `CATEGORY_COLORS` im Frontend).
- Je Entity: `image_url` (rund, Portrait/Logo/Flagge), `context_image_url`
  (groß/quadratisch, bewusst ANDERS als das Portrait wo sinnvoll -
  Institution/Flagge/Handlungsszene statt Gesicht) und `wikipedia_url`.
  Länder werden NICHT per Agent recherchiert, sondern deterministisch über
  eine Flaggen-Datei-Namenskonvention aufgelöst (zuverlässiger als Agenten-
  Rateversuche bei 24 Ländern).

Bild-URLs nutzen durchgängig den `Special:FilePath`-Redirect-Trick
(`https://commons.wikimedia.org/wiki/Special:FilePath/<Dateiname>`), der
den exakten Hash-Bucket-Pfad nicht kennen muss und zuverlässig auf die
echte Datei umleitet, sofern der Dateiname exakt stimmt.

Ausnahmen/Vorsicht (bewusst NICHT übernommen, weil unplausibel für eine
brandneue 2025/26-Institution ohne gesichertes Logo auf Commons):
- "Board of Peace"-Logo + dessen Wikipedia-Link (Agent-Angabe wirkte
  spekulativ für ein <1 Jahr altes Gremium) -> fällt zurück auf das
  gestaltete Icon-Fallback im Frontend.
- "NSPM-7"-Wikipedia-Link (einzelne Präsidialmemoranden haben praktisch
  nie einen eigenen Artikel) -> kein Link, kein Fehlklick auf eine
  vermutlich nicht existierende Seite.
- Gaza-Story-Hero: kein Agent-Vorschlag (null zurückgegeben) UND keine
  eigene Recherche mehr möglich (WebSearch-Kontingent dieser Session
  aufgebraucht) -> bewusst OHNE Foto, nutzt im Frontend den gestalteten
  Kategorie-Farbverlauf-Fallback statt eines ungeprüft geratenen
  Dateinamens.
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
STORIES_JSON = BASE / "data" / "stories.json"


def commons_url(filename: str | None) -> str | None:
    if not filename:
        return None
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(
        filename, safe=""
    )


# Land (wie in den Entities benannt) -> (Flaggen-Dateiname auf Commons, Wikipedia-Slug DE)
COUNTRY_META = {
    "Bulgarien": ("Flag_of_Bulgaria.svg", "Bulgarien"),
    "Ecuador": ("Flag_of_Ecuador.svg", "Ecuador"),
    "El Salvador": ("Flag_of_El_Salvador.svg", "El_Salvador"),
    "Frankreich": ("Flag_of_France.svg", "Frankreich"),
    "Griechenland": ("Flag_of_Greece.svg", "Griechenland"),
    "Indonesien": ("Flag_of_Indonesia.svg", "Indonesien"),
    "Iran": ("Flag_of_Iran.svg", "Iran"),
    "Israel": ("Flag_of_Israel.svg", "Israel"),
    "Japan": ("Flag_of_Japan.svg", "Japan"),
    "Jordanien": ("Flag_of_Jordan.svg", "Jordanien"),
    "Kanada": ("Flag_of_Canada.svg", "Kanada"),
    "Katar": ("Flag_of_Qatar.svg", "Katar"),
    "Pakistan": ("Flag_of_Pakistan.svg", "Pakistan"),
    "Portugal": ("Flag_of_Portugal.svg", "Portugal"),
    "Russland": ("Flag_of_Russia.svg", "Russland"),
    "Sudan": ("Flag_of_Sudan.svg", "Sudan"),
    "Türkei": ("Flag_of_Turkey.svg", "T%C3%BCrkei"),
    "USA": ("Flag_of_the_United_States.svg", "Vereinigte_Staaten"),
    "Ukraine": ("Flag_of_Ukraine.svg", "Ukraine"),
    "Vereinigte Staaten": ("Flag_of_the_United_States.svg", "Vereinigte_Staaten"),
    "Vereinigten Arabischen Emiraten": (
        "Flag_of_the_United_Arab_Emirates.svg",
        "Vereinigte_Arabische_Emirate",
    ),
    "Ägypten": ("Flag_of_Egypt.svg", "%C3%84gypten"),
}

# Story-ID -> Themenkategorie (feste Zuordnung, KEINE rotierenden Farben,
# s. dataviz-Skill: kategoriale Farben in fester Reihenfolge je Bedeutung,
# nicht zyklisch je Story-Index vergeben).
STORY_CATEGORY = {
    "uss-lincoln-oversight-2026-08": "security",
    "afghan-siv-revocations-2026-08": "rights",
    "sudan-national-dialogue-2026-08": "conflict",
    "ukraine-long-range-strikes-2026-08": "conflict",
    "cia-ecuador-drone-strikes-2026-08": "security",
    "putin-kuril-islands-visit-2026-08": "diplomacy",
    "us-canada-section-338-tariffs-2026-08": "trade",
    "dhs-minnesota-surveillance-2026-08": "surveillance",
    "eu-21st-russia-sanctions-2026-08": "diplomacy",
    "gaza-roadmap-netanyahu-standoff-2026-08": "conflict",
}

# Story-ID -> Hero-Bild (Commons-Dateiname), von 10 parallelen
# Recherche-Agenten je Story unabhängig verifiziert (WebFetch gegen die
# echte Wikipedia-/Commons-Seite, nicht geraten).
STORY_HERO = {
    "uss-lincoln-oversight-2026-08": "USS_Abraham_Lincoln_(CVN-72)_underway_in_the_Atlantic_Ocean_on_30_January_2019_(190130-N-PW716-1312).JPG",
    "afghan-siv-revocations-2026-08": "August 19 2021 Evacuation at Hamid Karzai International Airport 2.jpg",
    "sudan-national-dialogue-2026-08": "War in Sudan (2023).svg",
    "ukraine-long-range-strikes-2026-08": "Drawing of FP-5 Flamingo, cropped.png",
    "cia-ecuador-drone-strikes-2026-08": "Galápagos Islands Aerial photograph.JPG",
    "putin-kuril-islands-visit-2026-08": "Kuril-Islands-Northern-Territories-of-Japan-Map.png",
    "us-canada-section-338-tariffs-2026-08": "Mark Carney meeting with Donald Trump 4x5.jpg",
    "dhs-minnesota-surveillance-2026-08": "Tens of thousands march against ICE in Downtown Minneapolis.jpg",
    "eu-21st-russia-sanctions-2026-08": "Europa building European Union Brussels 01.jpg",
    "gaza-roadmap-netanyahu-standoff-2026-08": None,  # bewusst kein Foto, s. Docstring
}

# story_id -> {entity_name: {portrait, context, wiki}}, aus den 10
# Agenten-Antworten übernommen (Dateinamen exakt wie von den Agenten
# gemeldet). Zwei Einträge bewusst NICHT übernommen (s. Docstring oben):
# "Board of Peace"-Logo/Wiki-Link, "NSPM-7"-Wiki-Link.
ENTITY_MEDIA = {
    "uss-lincoln-oversight-2026-08": {
        "USS Abraham Lincoln": ("USS_Abraham_Lincoln_(CVN-72)_underway_in_the_Atlantic_Ocean_on_30_January_2019_(190130-N-PW716-1312).JPG", "USS_Abraham_Lincoln_(CVN-72),_USS_George_Washington_(CVN-73),_USS_Gerald_R._Ford_(CVN-78)_and_USS_Dwight_D._Eisenhower_(CVN-69)_at_Naval_Station_Norfolk_on_22_May_2017.JPG", "https://en.wikipedia.org/wiki/USS_Abraham_Lincoln_(CVN-72)"),
        "USS George Washington": ("USS_George_Washington_(CVN-73)_LB.jpg", "USS_Abraham_Lincoln_(CVN-72),_USS_George_Washington_(CVN-73),_USS_Gerald_R._Ford_(CVN-78)_and_USS_Dwight_D._Eisenhower_(CVN-69)_at_Naval_Station_Norfolk_on_22_May_2017.JPG", "https://en.wikipedia.org/wiki/USS_George_Washington_(CVN-73)"),
        "Ruben Gallego": ("Sen._Ruben_Gallego_official_Senate_photo,_119th_Congress_(crop).jpg", "Ruben_Gallego_&_Barack_Obama_(54111343485).jpg", "https://de.wikipedia.org/wiki/Ruben_Gallego_(Politiker)"),
        "Richard Blumenthal": ("Richard_Blumenthal_Official_Portrait.jpg", "Senator_Richard_Blumenthal,_2017.jpg", "https://de.wikipedia.org/wiki/Richard_Blumenthal"),
        "Mark Kelly": ("Mark_Kelly,_Official_Portrait_117th.jpg", "Mark_Kelly_at_work_during_STS-124.jpg", "https://de.wikipedia.org/wiki/Mark_Kelly_(Politiker)"),
        "Pete Hegseth": ("Pete_Hegseth_Official_Portrait.jpg", "Secretary_of_Defense_Pete_Hegseth_visits_Fort_Benning,_Georgia_on_September_4,_2025_-_15.jpg", "https://de.wikipedia.org/wiki/Pete_Hegseth"),
        "Kongress": ("United_States_Capitol_-_west_front.jpg", "United_States_Capitol_dome_daylight.jpg", "https://de.wikipedia.org/wiki/Kongress_der_Vereinigten_Staaten"),
        "War Powers Resolution": (None, None, "https://de.wikipedia.org/wiki/War_Powers_Resolution"),
        "US-Israel-Iran-Konflikt": (None, None, None),
    },
    "afghan-siv-revocations-2026-08": {
        "Trump-Regierung": ("Official Presidential Portrait of President Donald J. Trump (2025).jpg", "White House north and south sides.jpg", "https://de.wikipedia.org/wiki/Zweite_Pr%C3%A4sidentschaft_von_Donald_Trump"),
        "USCIS": ("USCIS logo English.svg", "Department of Homeland Security's new headquarters is ceremoniously opened.jpg", "https://de.wikipedia.org/wiki/United_States_Citizenship_and_Immigration_Services"),
        "International Refugee Assistance Project (IRAP)": (None, None, "https://en.wikipedia.org/wiki/International_Refugee_Assistance_Project"),
        "AfghanEvac": (None, None, None),
        "Special Immigrant Visa (SIV) Programm": (None, None, "https://en.wikipedia.org/wiki/Special_Immigrant_Visa"),
    },
    "sudan-national-dialogue-2026-08": {
        "Abdel Fattah al-Burhan": ("Abdel Fattah al-Burhan, 2019 (cropped).jpg", None, "https://en.wikipedia.org/wiki/Abdel_Fattah_al-Burhan"),
        "Rapid Support Forces (RSF)": ("Emblem of the Rapid Support Forces.png", "Flag of the Rapid Support Forces (Sudan).png", "https://en.wikipedia.org/wiki/Rapid_Support_Forces"),
        "Mohamed Hamdan Dagalo": ("Mohamed Hamdan Dagalo 2022 (cropped).jpg", None, "https://de.wikipedia.org/wiki/Mohammed_Hamdan_Daglo"),
        "Sudanesische Armee (SAF)": ("Insignia of the Sudanese Armed Forces.svg", None, "https://de.wikipedia.org/wiki/Sudanesische_Streitkr%C3%A4fte"),
        "Demokratische Blockpartei": (None, None, None),
    },
    "ukraine-long-range-strikes-2026-08": {
        "Wolodymyr Selenskyj": ("Volodymyr Zelensky Official portrait (cropped).jpg", None, "https://de.wikipedia.org/wiki/Wolodymyr_Selenskyj"),
        "Progress-Raumfahrtzentrum": (None, None, "https://en.wikipedia.org/wiki/Progress_Rocket_Space_Centre"),
        "Flamingo-Marschflugkörper": ("Drawing of FP-5 Flamingo, cropped.png", None, "https://en.wikipedia.org/wiki/FP-5_Flamingo"),
        "Maria Sacharowa": ("Maria Zakharova (cropped).jpg", "Ministry of Foreign Affairs building in Moscow, Russian Federation.jpg", "https://de.wikipedia.org/wiki/Maria_Wladimirowna_Sacharowa"),
    },
    "cia-ecuador-drone-strikes-2026-08": {
        "CIA": ("Seal of the Central Intelligence Agency.svg", None, "https://de.wikipedia.org/wiki/Central_Intelligence_Agency"),
        "Operation Southern Spear": (None, None, "https://en.wikipedia.org/wiki/Operation_Southern_Spear"),
        "Donald Trump": ("Official Presidential Portrait of President Donald J. Trump (2025).jpg", "White House north and south sides.jpg", "https://de.wikipedia.org/wiki/Donald_Trump"),
        "Pete Hegseth": ("29th United States Secretary of Defense Pete Hegseth Official Portrait 2025.jpg", "Secretary_of_Defense_Pete_Hegseth_visits_Fort_Benning,_Georgia_on_September_4,_2025_-_15.jpg", "https://de.wikipedia.org/wiki/Pete_Hegseth"),
        "Tim Kaine": ("Tim Kaine, official portrait (119th Congress) (cropped).jpg", None, "https://de.wikipedia.org/wiki/Tim_Kaine"),
        "Daniel Noboa": ("Presidente Daniel Noboa.jpg", "President Noboa of Ecuador in April of 2024.jpg", "https://de.wikipedia.org/wiki/Daniel_Noboa"),
        "Alexandra Bravo": (None, None, None),
        "Human Rights Watch": ("Hrw logo.svg", None, "https://de.wikipedia.org/wiki/Human_Rights_Watch"),
    },
    "putin-kuril-islands-visit-2026-08": {
        "Wladimir Putin": ("Putin in 2024.png", "Kremlin Moscow.jpg", "https://de.wikipedia.org/wiki/Wladimir_Putin"),
        "Sanae Takaichi": ("Official portrait of Sanae Takaichi, Prime Minister of Japan (HD).jpg", "National Diet Building - Tokyo, Japan - DSC06736.JPG", "https://de.wikipedia.org/wiki/Sanae_Takaichi"),
        "Toshimitsu Motegi": ("Official portrait of Toshimitsu Motegi 2024 (cropped).jpg", "National Diet Building - Tokyo, Japan - DSC06736.JPG", "https://de.wikipedia.org/wiki/Toshimitsu_Motegi"),
        "Dmitri Medwedew": ("Dmitry Medvedev official large photo -1 (cropped).jpg", "Kremlin Moscow.jpg", "https://de.wikipedia.org/wiki/Dmitri_Anatoljewitsch_Medwedew"),
        "Maria Sacharowa": ("Мария Захарова (28-11-2024) (cropped).jpg", "Ministry of Foreign Affairs building in Moscow, Russian Federation.jpg", "https://de.wikipedia.org/wiki/Maria_Sacharowa"),
        "Kurilen / Nördliche Territorien": ("Columnar Basalt at Cape Stolbchaty on Kunashir Island 2011.jpg", "Kuril-Islands-Northern-Territories-of-Japan-Map.png", "https://de.wikipedia.org/wiki/Kurilen"),
    },
    "us-canada-section-338-tariffs-2026-08": {
        "Donald Trump": ("Donald Trump official portrait (cropped wide).jpg", "Mark Carney meeting with Donald Trump 4x5.jpg", "https://de.wikipedia.org/wiki/Donald_Trump"),
        "Mark Carney": ("Mark Carney portrait May 2025 (cropped).jpg", "Mark Carney meeting with Donald Trump 4x5.jpg", "https://de.wikipedia.org/wiki/Mark_Carney"),
        "Jamieson Greer": ("Official portrait of U.S. Trade Representative Jamieson Greer (cropped 1).jpg", None, "https://en.wikipedia.org/wiki/Jamieson_Greer"),
        "Doug Ford": ("Doug Ford portrait (cropped).jpg", None, "https://de.wikipedia.org/wiki/Doug_Ford"),
        "USMCA/CUSMA": (None, None, "https://de.wikipedia.org/wiki/Nordamerikanisches_Freihandelsabkommen"),
        "Section 338": (None, None, None),
    },
    "dhs-minnesota-surveillance-2026-08": {
        "U.S. Department of Homeland Security (DHS)": (None, None, "https://de.wikipedia.org/wiki/Ministerium_f%C3%BCr_Innere_Sicherheit_der_Vereinigten_Staaten"),
        "Homeland Security Investigations (HSI)": ("Badge of a U.S. Homeland Security Investigations special agent.svg", "DHS Seal and HSI Badge.png", "https://de.wikipedia.org/wiki/U.S._Immigration_and_Customs_Enforcement"),
        "Kristi Noem": (None, None, "https://de.wikipedia.org/wiki/Kristi_Noem"),
        "Operation Puppet Master": (None, None, None),
        "NSPM-7": (None, None, None),
        "ACLU of Minnesota": ("New ACLU Logo 2017.svg", None, "https://de.wikipedia.org/wiki/American_Civil_Liberties_Union"),
        "Minnesota AFL-CIO": (None, None, "https://de.wikipedia.org/wiki/AFL-CIO"),
        "Twin Cities Democratic Socialists of America": (None, "Democratic Socialists of America Logo (official) (fit&cropped).svg", "https://en.wikipedia.org/wiki/Twin_Cities_Democratic_Socialists_of_America"),
        "Kevin Riach": (None, None, None),
        "Amy Klobuchar": (None, None, "https://de.wikipedia.org/wiki/Amy_Klobuchar"),
        "Tina Smith": ("Tina Smith, official portrait, 116th congress.jpg", None, "https://de.wikipedia.org/wiki/Tina_Smith"),
        "Alex Pretti": ("Alex Pretti VA Image (official portrait by United States Department of Veterans Affairs).jpg", None, "https://de.wikipedia.org/wiki/T%C3%B6tung_von_Alex_Pretti"),
    },
    "eu-21st-russia-sanctions-2026-08": {
        "Kaja Kallas": ("Kaja Kallas, High Representative of the Union, and Vice-President of the European Commission (3x4 cropped).jpg", "Wang Yi meeting Kaja Kallas (2025-07-03).jpg", "https://de.wikipedia.org/wiki/Kaja_Kallas"),
        "Europäische Union": ("Flag of Europe.svg", "Europa building European Union Brussels 01.jpg", "https://de.wikipedia.org/wiki/Europ%C3%A4ische_Union"),
        "Europäischer Auswärtiger Dienst": ("Insignia of the European External Action Service.svg", "Flag of Europe.svg", "https://de.wikipedia.org/wiki/Europ%C3%A4ischer_Ausw%C3%A4rtiger_Dienst"),
        "Patriarch Kirill": ("Patriarch Kirill I of Moscow 02.jpg", "Vladimir Putin and Patriarch Kirill on Unity Day 2016-11-04 05.jpg", "https://de.wikipedia.org/wiki/Kyrill_I."),
    },
    "gaza-roadmap-netanyahu-standoff-2026-08": {
        "Benjamin Netanyahu": ("Benjamin_Netanyahu_2018.jpg", None, "https://de.wikipedia.org/wiki/Benjamin_Netanjahu"),
        "Donald Trump": ("Donald_Trump_official_portrait,_2025_(cropped_headshot).jpg", None, "https://de.wikipedia.org/wiki/Donald_Trump"),
        "Hamas": ("Flag_of_Hamas.svg", None, "https://de.wikipedia.org/wiki/Hamas"),
        "Jared Kushner": ("Jared_Kushner_2025.jpg", None, "https://de.wikipedia.org/wiki/Jared_Kushner"),
        "IDF": ("Badge_of_the_Israel_Defense_Forces.svg", None, "https://de.wikipedia.org/wiki/Israelische_Verteidigungsstreitkr%C3%A4fte"),
        "Board of Peace": (None, None, None),  # bewusst verworfen, s. Docstring
        "Nickolay Mladenov": (None, None, "https://de.wikipedia.org/wiki/Nikolaj_Mladenow"),
        "Israel Katz": ("Israel_Katz_on_July_3,_2024_(cropped).jpg", None, "https://de.wikipedia.org/wiki/Israel_Katz_(Politiker,_1955)"),
        "Khalil al-Hayya": ("Khalil_al-Hayya_2024_(cropped).jpg", None, "https://de.wikipedia.org/wiki/Khalil_al-Hayya"),
    },
}


def run() -> None:
    stories = json.loads(STORIES_JSON.read_text())
    n_story_img = 0
    n_ent_img = 0
    n_ent_wiki = 0

    for story in stories:
        sid = story["id"]
        story["theme_category"] = STORY_CATEGORY.get(sid, "diplomacy")

        hero_file = STORY_HERO.get(sid)
        hero = commons_url(hero_file)
        if hero:
            story["image_url"] = hero
            n_story_img += 1
        else:
            story["image_url"] = None  # gestalteter Fallback im Frontend

        media = ENTITY_MEDIA.get(sid, {})
        for ent in story.get("entities", []):
            name = ent["name"]
            if ent["type"] == "country":
                meta = COUNTRY_META.get(name)
                if meta:
                    flag_file, wiki_slug = meta
                    ent["image_url"] = commons_url(flag_file)
                    ent["context_image_url"] = ent["image_url"]
                    ent["wikipedia_url"] = f"https://de.wikipedia.org/wiki/{wiki_slug}"
                    n_ent_img += 1
                    n_ent_wiki += 1
                continue

            if name in media:
                portrait_file, context_file, wiki = media[name]
                if portrait_file:
                    ent["image_url"] = commons_url(portrait_file)
                    n_ent_img += 1
                if context_file:
                    ent["context_image_url"] = commons_url(context_file)
                elif portrait_file:
                    ent["context_image_url"] = ent["image_url"]
                if wiki:
                    ent["wikipedia_url"] = wiki
                    n_ent_wiki += 1
            # sonst: kein Treffer -> bleibt ohne image_url/wikipedia_url,
            # Frontend zeigt den gestalteten Typ-Icon-Fallback.

    STORIES_JSON.write_text(json.dumps(stories, indent=2, ensure_ascii=False))
    print(
        f"Angereichert: {n_story_img}/{len(stories)} Story-Hero-Bilder, "
        f"{n_ent_img} Entity-Bilder, {n_ent_wiki} Wikipedia-Links -> {STORIES_JSON}"
    )


if __name__ == "__main__":
    run()
