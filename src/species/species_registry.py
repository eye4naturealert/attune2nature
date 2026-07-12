#--------------------------------------------------
# Species Registry
#--------------------------------------------------

SPECIES = {

    "eastern_box_turtle": {

        "common_name": "Eastern Box Turtle",
        "scientific_name": "Terrapene carolina",
        "taxon_id": 39814,
        "group": "Reptiles",
        "subgroup": "Turtles",
        "active": True

    },

    "common_snapping_turtle": {

        "common_name": "Common Snapping Turtle",
        "scientific_name": "Chelydra serpentina",
        "taxon_id": 39682,
        "group": "Reptiles",
        "subgroup": "Turtles",
        "active": True

    },

    "american_black_bear": {

        "common_name": "American Black Bear",
        "scientific_name": "Ursus americanus",
        "taxon_id": 41638,
        "group": "Mammals",
        "subgroup": "Large Mammals",
        "active": True

    }

}

#--------------------------------------------------
# Helper Functions
#--------------------------------------------------

def list_species() -> list[str]:
    """
    Return a list of available species identifiers.
    """

    return list(SPECIES.keys())


def get_species(name: str) -> dict:
    """
    Return the metadata dictionary for one species.

    Parameters
    ----------
    name : str
        Species identifier, such as
        'eastern_box_turtle'.

    Returns
    -------
    dict
        Species metadata dictionary.
    """

    species = SPECIES.get(name)

    if species is None:
        raise ValueError(
            f"Unknown species '{name}'. "
            f"Available species: {', '.join(list_species())}"
        )

    return species


def get_taxon_id(name: str) -> int:
    """
    Return the iNaturalist taxon ID for one species.
    """

    species = get_species(name)

    return species["taxon_id"]


def list_active_species() -> list[str]:
    """
    Return species identifiers currently enabled
    for use in Attune2Nature.
    """

    return [
        key
        for key, species in SPECIES.items()
        if species.get("active", False)
    ]


def get_species_dropdown_options() -> list[dict]:
    """
    Return active species formatted for a website dropdown.

    Returns
    -------
    list[dict]
        Each dictionary contains the display label,
        internal species value, group, and subgroup.
    """

    return [
        {
            "label": species["common_name"],
            "value": key,
            "group": species["group"],
            "subgroup": species["subgroup"]
        }
        for key, species in SPECIES.items()
        if species.get("active", False)
    ]


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    print("Available species:")
    print(list_species())

    print("\nActive species:")
    print(list_active_species())

    print("\nTesting get_species():")
    print(get_species("eastern_box_turtle"))

    print("\nTesting get_taxon_id():")
    print(get_taxon_id("american_black_bear"))

    print("\nWebsite dropdown options:")
    print(get_species_dropdown_options())