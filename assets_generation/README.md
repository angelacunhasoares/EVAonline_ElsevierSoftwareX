# Assets Generation Scripts

This folder contains scripts used to generate static assets for EVAonline.

## Structure

- `maps/`: Scripts for static map generation
  - `matopiba_map.py`: Generates static map of the MATOPIBA region

## How to Use

The scripts in this folder are auxiliary tools that generate static assets for EVAonline. Generated assets are saved in the project's `frontend/assets/images/` directory.

### Generating Maps

1. To generate the MATOPIBA map:
   ```bash
   python maps/matopiba_map.py
   ```
   The map will be saved to `../../frontend/assets/images/matopiba_map.png`

Directory structure:
```
EVAonline_ElsevierSoftwareX/
├── frontend/
│   └── assets/
│       └── images/          # All project image assets
│           ├── logo_c4ai.png
│           ├── logo_esalq.png
│           └── matopiba.png # Generated map
├── assets_generation/
│   └── maps/           
│       └── matopiba_map.py  # Generator script
```

The script is configured to save the map in the `frontend/assets/images/` folder, where all EVAonline project images are stored.

## Notes

- These scripts are not part of EVAonline's core functionality
- They are used only to generate static assets that will be included in the project
- May have additional dependencies not required for EVAonline itself
