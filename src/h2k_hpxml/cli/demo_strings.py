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
        "demo_setup_explanation": "Demo setup: Created demo folder and copied {filename} for demonstration",
        "hourly_all_explanation": "--hourly ALL: Export ALL available hourly energy variables (comprehensive data)",
        "output_format_csv_explanation": "--output-format csv: Save results in spreadsheet-friendly CSV format",
        "cleanup": "Delete demo output folder?",
        "cleanup_done": "Demo files cleaned up.",
        "complete": "Conversion and simulation complete!",
        "press_enter": "Press Enter to continue...",
        "cancelled": "Demo cancelled.",
        "error": "An error occurred: {error}",
        "file_not_found": "File not found: {filename}",
        "size_kb": "{size} KB",
        "size_mb": "{size} MB",
        "checking_deps": "Checking dependencies...",
        "deps_missing": "Missing dependencies. Please run: h2k-deps --auto-install",
        "copying_file": "Copying {filename} to demo directory...",
        "real_simulation": "This will run an actual simulation with hourly outputs (may take 2-3 minutes)",
        "creating_demo_dir": "Created demo directory: h2k_demo_output/",
        "simulation_complete": "Simulation completed successfully!",
        "copy_file_step": "Copy {filename} to h2k_demo_output/ folder",
        "run_simulation_step": "Run full EnergyPlus annual simulation",
        "save_outputs_step": "Save all outputs in h2k_demo_output/{stem}/",
        "copied_file": "Copied {filename} to demo directory",
        "weather_file_exists": "Weather file already exists:",
        "all_files_location": "All files are in: {location}",
        "demo_files_location": "Demo files are in: {location}",
        "file_descriptions": {
            # HPXML and building model files
            "xml_general": "HPXML building energy model (standardized home energy format)",
            "in_xml": "Processed HPXML input file used by OpenStudio/EnergyPlus simulation", 
            "in_idf": "EnergyPlus Input Data File - detailed building geometry and systems",
            "in_osm": "OpenStudio Model file - 3D building geometry and HVAC systems",
            
            # Annual and summary results
            "results_annual_csv": "Annual energy totals (heating, cooling, hot water, appliances)",
            "results_annual_json": "Annual energy results in JSON format for data processing",
            
            # Time-series data
            "results_timeseries_csv": "8,760 hours of energy data (heating, cooling, electricity, gas)",
            "eplusout_hourly_msgpack": "Hourly simulation data in compressed binary format",
            "eplusout_runperiod_msgpack": "Full year simulation data in compressed format", 
            "eplusout_msgpack": "Complete EnergyPlus output data in binary format",
            
            # Financial/billing results
            "results_bills_csv": "Annual utility bills and costs breakdown by fuel type",
            "results_bills_monthly_csv": "Monthly utility bills with seasonal variations",
            
            # Design and load calculations  
            "results_design_load_details_csv": "Peak heating/cooling loads for equipment sizing",
            
            # Simulation logs and diagnostics
            "eplusout_err": "EnergyPlus warnings and errors - check for simulation issues",
            "eplusout_end": "Simulation completion status indicator",
            "run_log": "Processing log from HPXML to OpenStudio conversion",
            "stderr_energyplus_log": "EnergyPlus error messages during simulation",
            "stdout_energyplus_log": "EnergyPlus standard output during simulation",
            
            # Reports and tables
            "eplustbl_htm": "EnergyPlus HTML report with detailed tables and summaries",
            
            # Source files
            "h2k_file": "Original Hot2000 building energy model input file",
            
            # Fallbacks
            "xml_fallback": "XML building model or configuration file",
            "csv_fallback": "Energy data in spreadsheet format for analysis",
            "json_fallback": "Structured energy data in JSON format",
            "log_fallback": "Processing or simulation log with messages",
            "sql_fallback": "SQLite database with detailed simulation results",
            "err_fallback": "Error and warning messages from simulation",
            "osm_fallback": "OpenStudio building model with 3D geometry",
            "idf_fallback": "EnergyPlus input file with building definition",
            "msgpack_fallback": "Compressed binary data from energy simulation",
            "html_fallback": "HTML report with tables and charts",
            "txt_fallback": "Text file with simulation data or logs",
            "end_fallback": "Simulation completion status file",
            "default_fallback": "Energy simulation output file"
        }
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
        "demo_setup_explanation": "Configuration démo: Dossier démo créé et {filename} copié pour démonstration",
        "hourly_all_explanation": "--hourly ALL: Exporter TOUTES les variables énergétiques horaires disponibles (données complètes)",
        "output_format_csv_explanation": "--output-format csv: Sauvegarder les résultats en format CSV compatible tableur",
        "cleanup": "Supprimer le dossier de démo?",
        "cleanup_done": "Fichiers de démo nettoyés.",
        "complete": "Conversion et simulation terminées!",
        "press_enter": "Appuyez sur Entrée pour continuer...",
        "cancelled": "Démo annulée.",
        "error": "Une erreur s'est produite: {error}",
        "file_not_found": "Fichier non trouvé: {filename}",
        "size_kb": "{size} Ko",
        "size_mb": "{size} Mo",
        "checking_deps": "Vérification des dépendances...",
        "deps_missing": "Dépendances manquantes. Exécutez: h2k-deps --auto-install",
        "copying_file": "Copie de {filename} vers le répertoire de démo...",
        "real_simulation": "Ceci exécutera une vraie simulation avec sorties horaires (peut prendre 2-3 minutes)",
        "creating_demo_dir": "Répertoire de démo créé: h2k_demo_output/",
        "simulation_complete": "Simulation complétée avec succès!",
        "copy_file_step": "Copier {filename} vers le dossier h2k_demo_output/",
        "run_simulation_step": "Exécuter une simulation EnergyPlus annuelle complète",
        "save_outputs_step": "Sauvegarder toutes les sorties dans h2k_demo_output/{stem}/",
        "copied_file": "{filename} copié vers le répertoire de démo",
        "weather_file_exists": "Le fichier météo existe déjà:",
        "all_files_location": "Tous les fichiers sont dans: {location}",
        "demo_files_location": "Les fichiers de démo sont dans: {location}",
        "file_descriptions": {
            # HPXML and building model files
            "xml_general": "Modèle énergétique de bâtiment HPXML (format standard résidentiel)",
            "in_xml": "Fichier d'entrée HPXML traité pour simulation OpenStudio/EnergyPlus",
            "in_idf": "Fichier de données d'entrée EnergyPlus - géométrie et systèmes détaillés",
            "in_osm": "Fichier modèle OpenStudio - géométrie 3D et systèmes CVC",
            
            # Annual and summary results
            "results_annual_csv": "Totaux énergétiques annuels (chauffage, climatisation, eau chaude, appareils)",
            "results_annual_json": "Résultats énergétiques annuels en format JSON pour traitement",
            
            # Time-series data
            "results_timeseries_csv": "8 760 heures de données énergétiques (chauffage, climatisation, électricité, gaz)",
            "eplusout_hourly_msgpack": "Données de simulation horaires en format binaire compressé",
            "eplusout_runperiod_msgpack": "Données de simulation annuelle en format compressé",
            "eplusout_msgpack": "Données complètes de sortie EnergyPlus en format binaire",
            
            # Financial/billing results
            "results_bills_csv": "Factures et coûts annuels par type de combustible",
            "results_bills_monthly_csv": "Factures mensuelles avec variations saisonnières",
            
            # Design and load calculations
            "results_design_load_details_csv": "Charges de pointe chauffage/climatisation pour dimensionnement",
            
            # Simulation logs and diagnostics
            "eplusout_err": "Avertissements et erreurs EnergyPlus - vérifier problèmes de simulation",
            "eplusout_end": "Indicateur d'état de completion de simulation",
            "run_log": "Journal de traitement de conversion HPXML vers OpenStudio",
            "stderr_energyplus_log": "Messages d'erreur EnergyPlus durant simulation",
            "stdout_energyplus_log": "Sortie standard EnergyPlus durant simulation",
            
            # Reports and tables
            "eplustbl_htm": "Rapport HTML EnergyPlus avec tableaux et résumés détaillés",
            
            # Source files
            "h2k_file": "Fichier d'entrée original de modèle énergétique Hot2000",
            
            # Fallbacks
            "xml_fallback": "Modèle de bâtiment XML ou fichier de configuration",
            "csv_fallback": "Données énergétiques en format tableur pour analyse",
            "json_fallback": "Données énergétiques structurées en format JSON",
            "log_fallback": "Journal de traitement ou simulation avec messages",
            "sql_fallback": "Base de données SQLite avec résultats détaillés de simulation",
            "err_fallback": "Messages d'erreur et avertissements de simulation",
            "osm_fallback": "Modèle de bâtiment OpenStudio avec géométrie 3D",
            "idf_fallback": "Fichier d'entrée EnergyPlus avec définition de bâtiment",
            "msgpack_fallback": "Données binaires compressées de simulation énergétique",
            "html_fallback": "Rapport HTML avec tableaux et graphiques",
            "txt_fallback": "Fichier texte avec données ou journaux de simulation",
            "end_fallback": "Fichier d'état de completion de simulation",
            "default_fallback": "Fichier de sortie de simulation énergétique"
        }
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