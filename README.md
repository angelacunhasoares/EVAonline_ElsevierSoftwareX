<p align="center">
  <img src="docs/images/evaonline_logo.png" alt="EVAonline Logo" width="900">
</p>

# EVAonline: An online tool for reference EVApotranspiration estimation

EVAonline is an open-source, browser-based platform for automated calculation of reference evapotranspiration (ET₀) using the FAO-56 Penman-Monteith model. Designed for data-scarce regions like Brazil’s MATOPIBA, it supports precision agriculture and irrigation planning with global applicability. Built with a modern tech stack including **Dash**, **FastAPI**, **Celery**, **Redis**, and **Docker**, EVAonline provides a scalable, efficient, and user-friendly solution for farmers, researchers, and policymakers.

## Overview

EVAonline automates ET₀ calculations by integrating weather data from multiple sources (NASA POWER, Open-Meteo Forecast, (...) and applying a simplified Ensemble Kalman Filter for data fusion. It offers an interactive interface with real-time coordinate selection, multilingual support (Portuguese and English), and comprehensive statistical tools for analyzing ET₀ trends and water balance. The platform generates detailed tables, graphs, and statistical analyses, enabling informed decision-making for irrigation and water management in agriculture.

## Features

- **Automated Data Retrieval**: Fetches weather data from NASA POWER, Open-Meteo Archive, Open-Meteo Forecast, and (...) without manual input.
- **Data Fusion**: Uses a simplified Ensemble Kalman Filter to ensure reliable ET₀ estimates in data-scarce regions.
- **Interactive Map**: Supports real-time coordinate selection via an integrated map interface for location-specific calculations.
- **Multilingual Interface**: Available in Portuguese and English for broader accessibility.
- **Statistical Analysis**: Provides descriptive statistics, normality tests, correlation matrices, trend analysis, and seasonality tests for ET₀ and related variables.
- **Visualization Tools**: Generates interactive graphs, including:
  - ET₀ vs. Temperature, Radiation, and Precipitation
  - Heatmap of correlations
  - Water deficit and cumulative water balance charts
  - Optional: Stacked timeseries, boxplots, 3D scatter plots, and period comparisons
- **Data Export**: Supports downloading results in CSV and Excel formats.
- **Scalable Architecture**: Leverages **FastAPI** for API services, **Celery** for asynchronous processing, **Redis** for caching, and **Docker** for deployment.
- **Global Applicability**: Includes a Global Mode for calculations anywhere in the world and a MATOPIBA Mode for region-specific analysis.

## Results Generated

EVAonline produces the following outputs:
- **Daily Weather Data**: Tables with daily values for temperature (max/min), relative humidity, wind speed, solar radiation, precipitation, and ET₀.
- **Statistical Summaries**: Descriptive statistics (mean, max, min, median, standard deviation, percentiles, skewness, kurtosis, coefficient of variation) for all variables.
- **Normality and Seasonality Tests**: Shapiro-Wilk test for normality and Augmented Dickey-Fuller (ADF) test for stationarity of ET₀ time series.
- **Correlation Analysis**: Correlation matrix highlighting relationships between weather variables and ET₀.
- **Water Balance Insights**: Daily and cumulative water deficit calculations, identifying periods of water shortage or excess.
- **Interactive Visualizations**: Graphs for ET₀ trends, correlations, and water balance, with options to toggle specific charts.
- **Exportable Results**: Downloadable tables and statistical summaries in CSV or Excel formats.

## Accessing EVAonline

EVAonline is a browser-based application requiring no local installation. To access it:

1. **Run Locally**:
   ```bash
   docker-compose up
      Then visit http://localhost:8050 in a modern browser (e.g., Chrome, Firefox, Edge).

2. **Hosted Version (if available):** Access at https://angelacunhasoares.github.io/EVAonline_SoftwareX/.

3. **No API keys or manual data inputs are required.**

## Usage

**1. Select Calculation Mode:** Choose between Global Mode (map-based coordinates) or MATOPIBA Mode (predefined city coordinates).

**2. Define Parameters:** Select a location via the interactive map or by choosing a state and city, specify the data source (NASA POWER, Open-Meteo, (...)), and set the date range (7–15 days).

**3. Calculate ET₀:** Trigger asynchronous processing via Celery, retrieving and fusing data to compute ET₀.

**4. View Results:** Explore results in two tabs:
- **Table and Graphs:** View daily data tables, interactive graphs (e.g., ET₀ vs. temperature, water deficit charts), and download results.
- **Statistical Analysis:** Access descriptive statistics, normality tests, correlation matrices, water balance summaries, trend analysis, and seasonality tests.

**5. Analyze and Export:** Use statistical tools to analyze trends and export results for further use.

See the Usage Guide for detailed instructions and screenshots.

## Installation and Setup

To run EVAonline locally:

1. Clone the repository:
    ```bash
    git clone https://github.com/angelacunhasoares/EVAonline_SoftwareX.git
    cd EVAonline_SoftwareX

2. Ensure **Docker** and **Docker Compose** are installed.

3. Build and run the application:
    ```bash
    docker-compose up --build

4. Access the app at http://localhost:8050.

## Dependencies

- **Dash:** For the interactive web interface.
- **FastAPI:** For API endpoints handling data retrieval and ET₀ calculations.
- **Celery:** For asynchronous task processing.
- **Redis:** For caching MATOPIBA data and task results.
- **Docker:** For containerized deployment.
- **Python Libraries:** pandas, numpy, plotly, scipy, statsmodels, requests, pykalman, xarray, cdsapi, openmeteo-requests, openpyxl, loguru.

See requirements.txt for a complete list.

## Documentation

The full EVAonline documentation is available on GitHub Pages. It includes:

- Installation and setup instructions.
- Detailed usage guide with screenshots.
- Technical details on the FAO-56 Penman-Monteith model, data fusion, and statistical methods.
- API documentation for developers.

## Commercial Use

For commercial use of this software, please contact the original authors at [angelasilviane@alumni.usp.br (mailto:angelasilviane@alumni.usp.br)] to discuss terms of use, in accordance with the GNU Affero General Public License v3.0.

## License

- Source Code: GNU Affero General Public License v3.0 (see LICENSE.txt).
- Documentation: GNU Affero General Public License v3.0 (see Documentation License).

## How to Cite

If you use EVAonline in your research, please cite:
[Your Name], [Co-authors’ Names]. (2025). EVAonline: An online tool for reference EVApotranspiration estimation. SoftwareX, [Volume], [Pages]. DOI: [Article DOI]. Source Code: [Zenodo DOI]. 

## Contact

For questions, support, or commercial inquiries, please contact [angelasilviane@alumni.usp.br (mailto:angelasilviane@alumni.usp.br)].

## Acknowledgments

Developed as part of a doctoral dissertation at Escola Superior de Agricultura "Luiz de Queiroz" (Esalq), University of São Paulo. Thanks to [advisor/co-authors/funders, if applicable] for their support.