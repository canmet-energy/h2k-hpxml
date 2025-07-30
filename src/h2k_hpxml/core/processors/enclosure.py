"""
Building enclosure processing for H2K to HPXML translation.

This module handles processing of all building enclosure components including walls,
floors, ceilings, foundations, windows, doors, and air infiltration systems.
"""

from ...components.enclosure_basements import get_basements
from ...components.enclosure_ceilings import get_ceilings
from ...components.enclosure_crawlspaces import get_crawlspaces
from ...components.enclosure_floors import get_floors
from ...components.enclosure_infiltration import get_infiltration
from ...components.enclosure_slabs import get_slabs
from ...components.enclosure_walls import get_attached_walls
from ...components.enclosure_walls import get_walls
from ...exceptions import HPXMLGenerationError
from ...utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def process_enclosure_components(h2k_dict, hpxml_dict, model_data, add_test_wall):
    """
    Process all building enclosure components and update HPXML structure.

    Args:
        h2k_dict: Parsed H2K dictionary
        hpxml_dict: Parsed HPXML dictionary
        model_data: ModelData instance for tracking building information
        add_test_wall: Boolean flag for adding test walls

    Returns:
        None: Modifies hpxml_dict and model_data in place

    Raises:
        HPXMLGenerationError: If enclosure processing fails
    """
    logger.info("Processing building enclosure components")

    try:
        # ================ 7. HPXML Section: Enclosure ================
        walls = []
        floors = []
        attics = []
        roofs = []
        windows = []
        skylights = []
        doors = []
        rim_joists = []
        foundations = []
        foundation_walls = []
        slabs = []
        # Subcomponents (windows, doors, rim joists) all collected through parents

        # Walls
        wall_results = get_walls(h2k_dict, model_data)
        walls = [*walls, *wall_results["walls"]]
        windows = [*windows, *wall_results["windows"]]
        doors = [*doors, *wall_results["doors"]]
        rim_joists = [*rim_joists, *wall_results["rim_joists"]]

        # Exposed Floors
        floor_results = get_floors(h2k_dict, model_data)
        floors = [*floors, *floor_results["floors"]]

        # Ceilings
        ceiling_results = get_ceilings(h2k_dict, model_data)
        attics = [*attics, *ceiling_results["attics"]]
        roofs = [*roofs, *ceiling_results["roofs"]]
        walls = [*walls, *ceiling_results["gable_walls"]]
        skylights = [*skylights, *ceiling_results["skylights"]]
        floors = [*floors, *ceiling_results["ceiling_floors"]]

        # Basements
        basement_results = get_basements(h2k_dict, model_data)
        windows = [*windows, *basement_results["windows"]]
        doors = [*doors, *basement_results["doors"]]
        rim_joists = [*rim_joists, *basement_results["rim_joists"]]
        foundations = [*foundations, *basement_results["foundations"]]
        foundation_walls = [*foundation_walls, *basement_results["foundation_walls"]]
        slabs = [*slabs, *basement_results["slabs"]]
        walls = [*walls, *basement_results["pony_walls"]]
        floors = [*floors, *basement_results["floors"]]

        # Crawlspaces
        crawlspace_results = get_crawlspaces(h2k_dict, model_data)
        windows = [*windows, *crawlspace_results["windows"]]
        doors = [*doors, *crawlspace_results["doors"]]
        rim_joists = [*rim_joists, *crawlspace_results["rim_joists"]]
        foundations = [*foundations, *crawlspace_results["foundations"]]
        foundation_walls = [*foundation_walls, *crawlspace_results["foundation_walls"]]
        slabs = [*slabs, *crawlspace_results["slabs"]]
        floors = [*floors, *crawlspace_results["floors"]]

        # Slab-on-grades
        slab_results = get_slabs(h2k_dict, model_data)
        slabs = [*slabs, *slab_results["slabs"]]

        # Airtightness
        infiltration = get_infiltration(h2k_dict, model_data)

        # Handle attached walls for attached homes
        attached_wall_results = get_attached_walls(h2k_dict, model_data, add_test_wall)
        walls = [*walls, *attached_wall_results["walls"]]

        # xmltodict unparse handles empty dicts/lists
        # Garages between Foundations and Roofs if they are modelled
        hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["Enclosure"] = {
            "AirInfiltration": infiltration,
            **({"Attics": {"Attic": attics}} if attics != [] else {}),
            **({"Foundations": {"Foundation": foundations}} if foundations != [] else {}),
            **({"Roofs": {"Roof": roofs}} if roofs != [] else {}),
            **({"RimJoists": {"RimJoist": rim_joists}} if rim_joists != [] else {}),
            **({"Walls": {"Wall": walls}} if walls != [] else {}),
            **(
                {"FoundationWalls": {"FoundationWall": foundation_walls}}
                if foundation_walls != []
                else {}
            ),
            **({"Floors": {"Floor": floors}} if floors != [] else {}),
            **({"Slabs": {"Slab": slabs}} if slabs != [] else {}),
            **({"Windows": {"Window": windows}} if windows != [] else {}),
            **({"Skylights": {"Skylight": skylights}} if skylights != [] else {}),
            **({"Doors": {"Door": doors}} if doors != [] else {}),
        }

        # ConditionedFloorArea after components to ensure it aligns with areas provided in components
        foundation_details = model_data.get_foundation_details()
        total_foundation_area = sum([fnd["total_area"] for fnd in foundation_details])

        ag_heated_floor_area = model_data.get_building_detail("ag_heated_floor_area")
        bg_heated_floor_area = model_data.get_building_detail("bg_heated_floor_area")

        # Check here to ensure no errors in HPXML, since bg_heated_floor_area is an input in h2k that is separate from the actual component areas
        if total_foundation_area > bg_heated_floor_area:
            bg_heated_floor_area = total_foundation_area

        # Update the building construction dict with the final floor area
        building_const_dict = hpxml_dict["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"][
            "BuildingConstruction"
        ]
        building_const_dict["ConditionedFloorArea"] = ag_heated_floor_area + bg_heated_floor_area

        logger.info(f"Heated Floor Area (ft2): {building_const_dict['ConditionedFloorArea']}")
        logger.debug("Building enclosure components processed successfully")

    except Exception as e:
        raise HPXMLGenerationError(
            f"Failed to process enclosure components: {e}", component="enclosure"
        )
