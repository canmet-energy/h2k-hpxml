"""
Bilingual string resources for the H2K to HPXML interactive demo.

This module contains all user-facing strings in both English and French
to support the interactive demo feature.
"""

DEMO_STRINGS = {
    "en": {
        "welcome_title": "H2K to HPXML Interactive Demo",
        "welcome_subtitle": "Learn how to use h2k2hpxml",
        "language_prompt": "Select language",
        "file_selection": "Choose an example file",
        "command_preview": "Here's the command we'll run:",
        "command_explanation": "This command will:",
        "convert_explanation": "• Convert {filename} to HPXML format",
        "output_explanation": "• Save output to demo_output/ folder",
        "debug_explanation": "• Include debug information for learning",
        "confirm_run": "Would you like to run this command?",
        "converting": "Converting H2K to HPXML...",
        "parsing": "Parsing building envelope",
        "hvac": "Converting HVAC systems",
        "weather": "Mapping weather data",
        "writing": "Writing HPXML output",
        "simulation": "Running EnergyPlus simulation",
        "initializing": "Initializing simulation",
        "running_model": "Running annual energy model",
        "generating_results": "Generating results",
        "output_tour": "Output Files Created",
        "file_header": "File",
        "size_header": "Size",
        "description_header": "Description",
        "file_description": {
            "xml": "HPXML format building model",
            "sql": "SQLite database with simulation results",
            "csv": "Annual energy summary",
            "timeseries": "Hourly energy data (8760 hours)"
        },
        "file_details": {
            "xml": "Contains: envelope, systems, schedules",
            "sql": "Contains: hourly energy data, loads",
            "csv": "Contains: fuel use, emissions, costs",
            "timeseries": "Use for: detailed time-series analysis"
        },
        "explore_file": "Would you like to explore any file?",
        "view_file": "Viewing: {filename}",
        "sample_content": "Sample content (first few lines):",
        "next_steps": "🎉 Demo Complete!",
        "learned": "You've learned how to:",
        "learned_points": [
            "✓ Convert H2K files to HPXML",
            "✓ Run EnergyPlus simulations",
            "✓ Understand output files"
        ],
        "try_next": "Try these commands next:",
        "commands": [
            "# Convert your own H2K file:",
            "h2k2hpxml your_file.h2k",
            "",
            "# Process a folder of files:",
            "h2k2hpxml /path/to/h2k/folder/",
            "",
            "# Add hourly outputs:",
            "h2k2hpxml file.h2k --hourly ALL",
            "",
            "# Skip simulation (convert only):",
            "h2k2hpxml file.h2k --do-not-sim"
        ],
        "help_command": "Need help? Run: h2k2hpxml --help",
        "cleanup": "Clean up demo files?",
        "cleanup_done": "Demo files cleaned up.",
        "complete": "Conversion complete!",
        "press_enter": "Press Enter to continue...",
        "cancelled": "Demo cancelled.",
        "error": "An error occurred: {error}",
        "file_not_found": "File not found: {filename}",
        "size_kb": "{size} KB",
        "size_mb": "{size} MB"
    },
    "fr": {
        "welcome_title": "Démo Interactive H2K vers HPXML",
        "welcome_subtitle": "Apprenez à utiliser h2k2hpxml",
        "language_prompt": "Sélectionner la langue",
        "file_selection": "Choisissez un fichier exemple",
        "command_preview": "Voici la commande que nous allons exécuter:",
        "command_explanation": "Cette commande va:",
        "convert_explanation": "• Convertir {filename} au format HPXML",
        "output_explanation": "• Sauvegarder la sortie dans demo_output/",
        "debug_explanation": "• Inclure les informations de débogage",
        "confirm_run": "Voulez-vous exécuter cette commande?",
        "converting": "Conversion H2K vers HPXML...",
        "parsing": "Analyse de l'enveloppe du bâtiment",
        "hvac": "Conversion des systèmes CVC",
        "weather": "Cartographie des données météo",
        "writing": "Écriture de la sortie HPXML",
        "simulation": "Exécution de la simulation EnergyPlus",
        "initializing": "Initialisation de la simulation",
        "running_model": "Exécution du modèle énergétique annuel",
        "generating_results": "Génération des résultats",
        "output_tour": "Fichiers de Sortie Créés",
        "file_header": "Fichier",
        "size_header": "Taille",
        "description_header": "Description",
        "file_description": {
            "xml": "Modèle de bâtiment au format HPXML",
            "sql": "Base de données SQLite avec résultats",
            "csv": "Résumé énergétique annuel",
            "timeseries": "Données énergétiques horaires (8760 heures)"
        },
        "file_details": {
            "xml": "Contient: enveloppe, systèmes, horaires",
            "sql": "Contient: données énergétiques horaires, charges",
            "csv": "Contient: consommation, émissions, coûts",
            "timeseries": "Pour: analyse détaillée des séries temporelles"
        },
        "explore_file": "Voulez-vous explorer un fichier?",
        "view_file": "Affichage: {filename}",
        "sample_content": "Contenu d'exemple (premières lignes):",
        "next_steps": "🎉 Démo Terminée!",
        "learned": "Vous avez appris à:",
        "learned_points": [
            "✓ Convertir des fichiers H2K vers HPXML",
            "✓ Exécuter des simulations EnergyPlus",
            "✓ Comprendre les fichiers de sortie"
        ],
        "try_next": "Essayez ces commandes ensuite:",
        "commands": [
            "# Convertir votre propre fichier H2K:",
            "h2k2hpxml votre_fichier.h2k",
            "",
            "# Traiter un dossier de fichiers:",
            "h2k2hpxml /chemin/vers/dossier/h2k/",
            "",
            "# Ajouter des sorties horaires:",
            "h2k2hpxml fichier.h2k --hourly ALL",
            "",
            "# Ignorer la simulation (conversion seulement):",
            "h2k2hpxml fichier.h2k --do-not-sim"
        ],
        "help_command": "Besoin d'aide? Exécutez: h2k2hpxml --help",
        "cleanup": "Nettoyer les fichiers de démo?",
        "cleanup_done": "Fichiers de démo nettoyés.",
        "complete": "Conversion terminée!",
        "press_enter": "Appuyez sur Entrée pour continuer...",
        "cancelled": "Démo annulée.",
        "error": "Une erreur s'est produite: {error}",
        "file_not_found": "Fichier non trouvé: {filename}",
        "size_kb": "{size} Ko",
        "size_mb": "{size} Mo"
    }
}


def get_string(key, lang="en"):
    """
    Get localized string with fallback to English.
    
    Args:
        key (str): String key, can use dot notation for nested keys (e.g., "file_description.xml")
        lang (str): Language code ("en" or "fr")
        
    Returns:
        str: Localized string or key if not found
    """
    # Handle nested keys like "file_description.xml"
    keys = key.split('.')
    
    # Get the language dict with fallback to English
    lang_dict = DEMO_STRINGS.get(lang, DEMO_STRINGS["en"])
    fallback_dict = DEMO_STRINGS["en"]
    
    # Navigate through nested keys
    try:
        value = lang_dict
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        # Try fallback to English
        try:
            value = fallback_dict
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Return the key if not found
            return key


def get_list(key, lang="en"):
    """
    Get localized list with fallback to English.
    
    Args:
        key (str): List key
        lang (str): Language code ("en" or "fr")
        
    Returns:
        list: Localized list or empty list if not found
    """
    result = get_string(key, lang)
    return result if isinstance(result, list) else []