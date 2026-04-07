"""
Pre-defined city lists for country-level searches.
When max_results > 200 and the location matches a known country,
generate_leads iterates city by city instead of using direction modifiers.

Coverage: enough cities per country to support 5 000+ leads
(each city yields ~20-60 results → 100 cities ≈ 2 000-6 000 leads).
"""

CITIES: dict[str, list[str]] = {

    "belgium": [
        "Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges",
        "Namur", "Leuven", "Mons", "Aalst", "Mechelen", "La Louvière",
        "Kortrijk", "Hasselt", "Ostend", "Sint-Niklaas", "Tournai", "Genk",
        "Seraing", "Roeselare", "Mouscron", "Verviers", "Beveren",
        "Dendermonde", "Beringen", "Turnhout", "Harelbeke", "Geel",
        "Lokeren", "Dilbeek", "Heist-op-den-Berg", "Lommel", "Waregem",
        "Maasmechelen", "Wevelgem", "Ninove", "Zemst", "Deinze", "Tongeren",
        "Mol", "Pelt", "Ronse", "Tielt", "Arlon", "Aarschot", "Ieper",
        "Halle", "Vilvoorde", "Zaventem", "Grimbergen", "Brecht", "Herentals",
        "Gent", "Liege", "Bruges", "Namur", "Sint-Truiden", "Tienen",
        "Boom", "Putte", "Puurs", "Lier", "Mortsel", "Schoten",
        "Kapellen", "Brasschaat", "Zwijndrecht", "Edegem", "Kontich",
        "Willebroek", "Bornem", "Temse", "Wetteren", "Zottegem", "Geraardsbergen",
        "Oudenaarde", "Zwevegem", "Izegem", "Menen", "Poperinge", "Veurne",
        "Diksmuide", "Torhout", "Tielt", "Diest", "Hamont-Achel", "Bree",
        "Maaseik", "Riemst", "Bilzen", "Borgloon", "Hannut", "Huy",
        "Wavre", "Ottignies", "Waterloo", "Braine-l'Alleud", "Nivelles",
        "Gembloux", "Sambreville", "Fleurus", "Thuin", "Binche", "Soignies",
        "Ath", "Lessines", "Enghien", "Tubize", "Braine-le-Comte",
        "Libramont", "Bastogne", "Marche-en-Famenne", "Dinant", "Ciney",
        "Andenne", "Jambes", "Wépion", "Salzinnes",
    ],

    "france": [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes",
        "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes", "Reims",
        "Le Havre", "Saint-Étienne", "Toulon", "Grenoble", "Dijon", "Angers",
        "Nîmes", "Villeurbanne", "Le Mans", "Aix-en-Provence", "Clermont-Ferrand",
        "Brest", "Amiens", "Limoges", "Tours", "Perpignan", "Metz", "Besançon",
        "Orléans", "Mulhouse", "Caen", "Rouen", "Nancy", "Avignon", "Poitiers",
        "Versailles", "Pau", "Cannes", "Calais", "Dunkirk", "Boulogne-sur-Mer",
        "Valenciennes", "Troyes", "Annecy", "Chambéry", "Bayonne", "Lorient",
    ],

    "netherlands": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Tilburg", "Groningen", "Almere", "Breda", "Nijmegen", "Enschede",
        "Haarlem", "Arnhem", "Zaanstad", "Amersfoort", "Apeldoorn",
        "Zwolle", "Dordrecht", "Leiden", "Maastricht", "Delft",
        "Alkmaar", "Venlo", "Deventer", "Den Bosch", "Hilversum",
        "Leeuwarden", "Middelburg", "Assen", "Lelystad",
    ],

    "germany": [
        "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart",
        "Düsseldorf", "Dortmund", "Essen", "Leipzig", "Bremen", "Dresden",
        "Hanover", "Nuremberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld",
        "Bonn", "Münster", "Karlsruhe", "Mannheim", "Augsburg", "Wiesbaden",
        "Gelsenkirchen", "Mönchengladbach", "Braunschweig", "Kiel", "Chemnitz",
        "Aachen", "Halle", "Magdeburg", "Freiburg", "Krefeld", "Lübeck",
        "Oberhausen", "Erfurt", "Mainz", "Rostock", "Kassel", "Saarbrücken",
    ],

    "united kingdom": [
        "London", "Birmingham", "Manchester", "Glasgow", "Liverpool",
        "Bristol", "Sheffield", "Leeds", "Edinburgh", "Leicester",
        "Coventry", "Bradford", "Cardiff", "Nottingham", "Kingston upon Hull",
        "Newcastle", "Stoke-on-Trent", "Southampton", "Derby", "Portsmouth",
        "Brighton", "Plymouth", "Northampton", "Reading", "Wolverhampton",
        "Bolton", "Aberdeen", "Bournemouth", "Norwich", "Swansea",
        "Milton Keynes", "Sunderland", "Luton", "Preston", "Warrington",
    ],

    "spain": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Málaga",
        "Murcia", "Palma", "Las Palmas", "Bilbao", "Alicante", "Córdoba",
        "Valladolid", "Vigo", "Gijón", "Granada", "A Coruña", "Vitoria",
        "Elche", "Santa Cruz de Tenerife", "Oviedo", "Badalona", "Cartagena",
        "Hospitalet", "Móstoles", "Sabadell", "Almería", "Fuenlabrada",
        "Santander", "Pamplona", "Castellón", "Burgos", "Albacete", "Getafe",
    ],

    "italy": [
        "Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa",
        "Bologna", "Florence", "Bari", "Catania", "Venice", "Verona",
        "Messina", "Padua", "Trieste", "Brescia", "Taranto", "Prato",
        "Reggio Calabria", "Modena", "Reggio Emilia", "Perugia", "Ravenna",
        "Livorno", "Cagliari", "Foggia", "Rimini", "Ferrara", "Salerno",
    ],

    "united states": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "Indianapolis", "San Francisco", "Seattle", "Denver", "Nashville",
        "Oklahoma City", "El Paso", "Washington", "Las Vegas", "Louisville",
        "Memphis", "Portland", "Baltimore", "Milwaukee", "Albuquerque",
        "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City",
        "Atlanta", "Omaha", "Colorado Springs", "Raleigh", "Miami",
        "Minneapolis", "Tulsa", "Tampa", "New Orleans", "Cleveland",
    ],
}

# Aliases — map alternative spellings to canonical keys
_ALIASES: dict[str, str] = {
    "be":            "belgium",
    "belgique":      "belgium",
    "belgië":        "belgium",
    "fr":            "france",
    "nl":            "netherlands",
    "holland":       "netherlands",
    "de":            "germany",
    "deutschland":   "germany",
    "uk":            "united kingdom",
    "great britain": "united kingdom",
    "england":       "united kingdom",
    "es":            "spain",
    "it":            "italy",
    "usa":           "united states",
    "us":            "united states",
    "america":       "united states",
}


def get_cities(location: str) -> list[str]:
    """
    Return the city list for a country location, or [] if unknown.
    Lookup is case-insensitive and handles common aliases.
    """
    key = location.strip().lower()
    key = _ALIASES.get(key, key)
    return CITIES.get(key, [])
