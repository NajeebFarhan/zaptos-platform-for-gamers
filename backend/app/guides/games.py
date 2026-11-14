"""Supported games and where their guide content comes from."""

GAMES: dict[str, dict] = {
    "valorant": {
        "id": "valorant",
        "name": "Valorant",
        "short": "VAL",
        "publisher": "Riot Games",
        "genre": "Tactical FPS",
        "tagline": "5v5 character-based tactical shooter. Master agents, maps and gunplay.",
        "accent": "#ff4655",
        "wiki": "valorant.fandom.com",
        "wiki_name": "VALORANT Wiki",
        "search_name": "Valorant",
        "wp_search": "valorant",
        "roster": [
            {"id": "agents", "label": "Agents", "source": "valorant", "kind": "agents"},
            {"id": "maps", "label": "Maps", "source": "valorant", "kind": "maps"},
            {"id": "weapons", "label": "Weapons", "source": "valorant", "kind": "weapons"},
        ],
        "topics": [
            {"id": "beginner", "label": "Beginner guide", "query": "beginner guide tips"},
            {"id": "tier-list", "label": "Agent tier list", "query": "agent tier list"},
            {"id": "crosshair", "label": "Best crosshair", "query": "best crosshair settings codes"},
            {"id": "economy", "label": "Economy", "query": "economy guide when to buy save"},
            {"id": "aim", "label": "Aim training", "query": "how to improve aim training routine"},
            {"id": "settings", "label": "Best settings", "query": "best settings fps graphics"},
            {"id": "ranked", "label": "Rank up", "query": "ranked tips climb"},
            {"id": "lineups", "label": "Lineups", "query": "lineups guide"},
        ],
        "search_hint": "Jett guide, Ascent defense, Sova lineups…",
    },
    "genshin-impact": {
        "id": "genshin-impact",
        "name": "Genshin Impact",
        "short": "GI",
        "publisher": "HoYoverse",
        "genre": "Open-world action RPG",
        "tagline": "Builds, teams and farming routes for Teyvat's travellers.",
        "accent": "#e0b44c",
        "wiki": "genshin-impact.fandom.com",
        "wiki_name": "Genshin Impact Wiki",
        "search_name": "Genshin Impact",
        "wp_search": "genshin impact",
        "roster": [
            {
                "id": "characters", "label": "Characters", "source": "wiki", "category": "Playable_Characters",
                "exclude": ["Traveler"],
                "tag_groups": [
                    {"label": "Element", "categories": {
                        "Pyro": "Pyro_Characters", "Hydro": "Hydro_Characters", "Anemo": "Anemo_Characters",
                        "Electro": "Electro_Characters", "Dendro": "Dendro_Characters", "Cryo": "Cryo_Characters",
                        "Geo": "Geo_Characters"}},
                    {"label": "Rarity", "categories": {"5★": "5-Star_Characters", "4★": "4-Star_Characters"}},
                ],
            },
            {
                "id": "weapons", "label": "Weapons", "source": "wiki", "category": "Weapons",
                "exclude": ["Weapon", "Sword", "Claymore", "Polearm", "Bow", "Catalyst"],
                "tag_groups": [
                    {"label": "Type", "categories": {"Sword": "Swords", "Claymore": "Claymores", "Polearm": "Polearms",
                                                     "Bow": "Bows", "Catalyst": "Catalysts"}},
                    {"label": "Rarity", "categories": {"5★": "5-Star_Weapons", "4★": "4-Star_Weapons"}},
                ],
            },
        ],
        "topics": [
            {"id": "beginner", "label": "Beginner guide", "query": "beginner guide tips"},
            {"id": "tier-list", "label": "Tier list", "query": "character tier list"},
            {"id": "teams", "label": "Best teams", "query": "best team comps"},
            {"id": "artifacts", "label": "Artifacts", "query": "artifact guide farming"},
            {"id": "primogems", "label": "Primogems", "query": "how to get primogems farming"},
            {"id": "abyss", "label": "Spiral Abyss", "query": "spiral abyss guide"},
            {"id": "f2p", "label": "F2P tips", "query": "free to play f2p guide"},
            {"id": "reroll", "label": "Rerolling", "query": "reroll guide best starter"},
        ],
        "search_hint": "Raiden Shogun build, Furina team, Natlan…",
    },
    "mobile-legends": {
        "id": "mobile-legends",
        "name": "Mobile Legends: Bang Bang",
        "short": "MLBB",
        "publisher": "Moonton",
        "genre": "Mobile MOBA",
        "tagline": "Heroes, builds, emblems and lane strategy for the Land of Dawn.",
        "accent": "#4f8cff",
        "wiki": "mobile-legends.fandom.com",
        "wiki_name": "Mobile Legends Wiki",
        "search_name": "Mobile Legends",
        "wp_search": "mobile legends",
        "roster": [
            {
                "id": "heroes", "label": "Heroes", "source": "wiki", "category": "Heroes",
                "exclude": ["Heroes", "Hero"],
                "tag_groups": [
                    {"label": "Role", "categories": {
                        "Tank": "Tank_heroes", "Fighter": "Fighter_heroes", "Assassin": "Assassin_heroes",
                        "Mage": "Mage_heroes", "Marksman": "Marksman_heroes", "Support": "Support_heroes"}},
                ],
            },
            {
                "id": "equipment", "label": "Equipment", "source": "wiki", "category": "Equipment",
                "exclude": ["Equipment"],
                "tag_groups": [
                    {"label": "Type", "categories": {
                        "Attack": "Attack_equipment", "Magic": "Magic_equipment", "Defense": "Defense_equipment"}},
                ],
            },
        ],
        "topics": [
            {"id": "beginner", "label": "Beginner guide", "query": "beginner guide tips"},
            {"id": "tier-list", "label": "Hero tier list", "query": "hero tier list meta"},
            {"id": "builds", "label": "Best builds", "query": "best build items"},
            {"id": "emblems", "label": "Emblems", "query": "emblem guide best emblems"},
            {"id": "jungle", "label": "Jungling", "query": "jungle guide rotation"},
            {"id": "ranked", "label": "Rank push", "query": "rank push tips mythic"},
            {"id": "roles", "label": "Roles & lanes", "query": "roles lanes explained"},
            {"id": "drafting", "label": "Drafting", "query": "draft pick counter guide"},
        ],
        "search_hint": "Ling build, best tank, gold lane tips…",
    },
    "csgo": {
        "id": "csgo",
        "name": "CS:GO / CS2",
        "short": "CS",
        "publisher": "Valve",
        "genre": "Tactical FPS",
        "tagline": "Smokes, sprays, economy and map control for Counter-Strike.",
        "accent": "#f59e0b",
        "wiki": "counterstrike.fandom.com",
        "wiki_name": "Counter-Strike Wiki",
        "search_name": "CS2 CS:GO",
        "wp_search": "cs2",
        "roster": [
            {
                "id": "weapons", "label": "Weapons", "source": "wiki", "category": "Weapons",
                "exclude": ["Weapons", "Weapon"],
                "tag_groups": [
                    {"label": "Type", "categories": {
                        "Pistol": "Pistols", "Rifle": "Rifles", "SMG": "Submachine_guns",
                        "Shotgun": "Shotguns", "Machine gun": "Machine_guns"}},
                ],
            },
            {
                "id": "maps", "label": "Maps", "source": "wiki",
                "titles": ["Dust II", "Mirage", "Inferno", "Nuke", "Ancient", "Anubis", "Train", "Overpass",
                           "Vertigo", "Cache", "Office", "Italy"],
            },
        ],
        "topics": [
            {"id": "beginner", "label": "Beginner guide", "query": "beginner guide tips"},
            {"id": "smokes", "label": "Smoke lineups", "query": "smoke lineups mirage inferno"},
            {"id": "crosshair", "label": "Best crosshair", "query": "best crosshair codes pros"},
            {"id": "economy", "label": "Economy", "query": "economy guide buy rounds"},
            {"id": "spray", "label": "Spray control", "query": "spray control recoil pattern ak47"},
            {"id": "settings", "label": "Best settings", "query": "best settings fps launch options"},
            {"id": "aim", "label": "Aim training", "query": "aim training workshop maps"},
            {"id": "premier", "label": "Premier & ranks", "query": "premier rank tips"},
        ],
        "search_hint": "AWP tips, Mirage A execute, best binds…",
    },
}

PUBLIC_FIELDS = ("id", "name", "short", "publisher", "genre", "tagline", "accent", "wiki_name", "search_hint")


def public(game: dict) -> dict:
    out = {k: game[k] for k in PUBLIC_FIELDS}
    out["wiki_url"] = f"https://{game['wiki']}"
    out["roster"] = [{"id": r["id"], "label": r["label"]} for r in game["roster"]]
    out["topics"] = [{"id": t["id"], "label": t["label"]} for t in game["topics"]]
    return out
