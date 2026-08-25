#--------------------------------------------------
# Imports
#--------------------------------------------------

import requests
import time
from species_registry import SPECIES

#--------------------------------------------------
# Find Taxon by Scientific Name
#--------------------------------------------------

def find_taxon_by_name(scientific_name: str):

    url = "https://api.inaturalist.org/v1/taxa"

    params = {
        "q": scientific_name,
        "rank": "species"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    for taxon in data.get("results", []):

        if taxon["name"] == scientific_name:
            return taxon

    return None

#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    print("Species in registry:")
    print(len(SPECIES))

    print("\nFirst few species:")

    for key in list(SPECIES.keys())[:5]:
        print(key)

    print("\nTesting all taxa against iNaturalist...")


    #--------------------------------------------------
    # Validation Counters
    #--------------------------------------------------

    pass_count = 0
    mismatch_count = 0
    error_count = 0

    mismatched_species = []


    #--------------------------------------------------
    # Validate Species
    #--------------------------------------------------

    for key, species in SPECIES.items():

        taxon_id = species["taxon_id"]

        url = f"https://api.inaturalist.org/v1/taxa/{taxon_id}"

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        taxon = data["results"][0]

        print("\nSpecies:", species["common_name"])
        print("Registry scientific name:", species["scientific_name"])
        print("iNaturalist scientific name:", taxon["name"])

        if species["scientific_name"] == taxon["name"]:
            print("Validation result: PASS")
            pass_count += 1

        else:

            print("Validation result: MISMATCH")

            mismatch_count += 1
            mismatched_species.append(key)

            print("Searching for correct taxon...")

            suggested_taxon = find_taxon_by_name(
                species["scientific_name"]
            )

            if suggested_taxon:

                print(
                    "Suggested taxon ID:",
                    suggested_taxon["id"]
                )

            else:

                print(
                    "Suggested taxon ID: NOT FOUND"
                )

        time.sleep(1)


    #--------------------------------------------------
    # Validation Summary
    #--------------------------------------------------

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print("Species checked :", len(SPECIES))
    print("Passed          :", pass_count)
    print("Mismatches      :", mismatch_count)
    print("Errors          :", error_count)


    #--------------------------------------------------
    # Mismatched Species
    #--------------------------------------------------

    print("\nMISMATCHED SPECIES")
    print("=" * 60)

    for key in mismatched_species:
        print(key)