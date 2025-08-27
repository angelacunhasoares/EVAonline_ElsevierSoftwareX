<p align="center">
  <img src="frontend/assets/images/evaonline_logo.png" alt="EVAonline Logo" width="900">
</p>

## 🌿 Overview

EVAonline is a comprehensive web application for calculating reference evapotranspiration (ET₀) using the FAO-56 Penman-Monteith method. It employs a sophisticated data fusion approach, integrating real-time meteorological data from multiple global sources (NASA POWER, MET Norway API, National Weather Service API, and NOAA Climate Data Online). The system features real-time ET₀ heat maps for the MATOPIBA region (powered by Open-Meteo Forecast), updated three times daily. Built with modern technologies, it provides interactive dashboards, real-time data processing, and advanced geospatial visualization capabilities.

## 🏗️ Architecture

### Tech Stack

**Frontend & Visualization:**
- **Dash**: Interactive dashboards and data visualization
- **Dash Bootstrap Components**: Responsive UI components
- **dash-leaflet**: Interactive maps with GeoJSON layers and heatmaps

**Backend & APIs:**
- **FastAPI**: High-performance API server with WebSocket support
- **Celery**: Asynchronous task processing
- **Redis**: Caching and message broker (Pub/Sub)

**Database & Storage:**
- **PostgreSQL + PostGIS**: Geospatial data management
- **Redis**: High-performance caching layer

**Infrastructure:**
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy and static file serving
- **Prometheus + Grafana**: Monitoring and metrics
- **Render**: Cloud deployment platform

## 📁 Project Structure

```
EVAonline_ElsevierSoftwareX/
├── api/                    # FastAPI backend services
│   ├── main.py            # Main API application
│   ├── data_service.py    # Data processing endpoints
│   ├── websocket_service.py # WebSocket connections
│   └── services/          # Service modules
├── assets_generation/     # Scripts for generating static assets
│   └── maps/             # Map generation scripts
├── components/            # Reusable Dash components
├── database/              # Database configuration and models
│   ├── connection.py      # Database connection setup
│   ├── models/           # SQLAlchemy models
│   └── migrations/       # Database migration scripts
├── frontend/             # Frontend application
│   └── assets/          # Static assets (images, styles)
│       └── images/      # Image assets
├── pages/                # Dash page components
├── src/                  # Core business logic
├── utils/                # Utility functions
├── monitoring/           # Prometheus configuration
├── docker-compose.yml    # Multi-service orchestration
└── requirements.txt      # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/angelacunhasoares/EVAonline_ElsevierSoftwareX.git
   cd EVAonline_ElsevierSoftwareX
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - **Dashboard:** http://localhost:8050
   - **API Documentation:** http://localhost:8000/docs
   - **Prometheus:** http://localhost:9090
   - **Grafana:** http://localhost:3000

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

- `POSTGRES_*`: PostgreSQL database settings
- `REDIS_*`: Redis cache and broker settings
- `FASTAPI_*`: API server configuration
- `DASH_*`: Dashboard application settings

## 📊 Features

### Data Sources and Processing

#### Real-Time Data Integration
EVAonline integrates multiple real-time weather data sources through RESTful APIs:

- **Global Coverage**:
  - **NASA POWER**: Primary meteorological satellite data
  - **Open-Meteo Forecast**: Global weather forecasting and historical data
  - **Open-Meteo Elevation API**: High-precision global elevation data

- **Regional Specialized Sources**:
  - **MET Norway API**: High-resolution European weather data
  - **National Weather Service API**: Detailed USA meteorological data
  - **Open-Meteo Forecast**: MATOPIBA region data (updated 3x daily)

#### Data Fusion and Processing
- **Multi-Source Integration**: 
  - Real-time data fusion from all available APIs
  - Weighted ensemble approach for robust estimates
  - Automated quality control and cross-validation

#### Quality Assurance
- **Global Validation**:
  - AgERA5 (ECMWF) dataset used for worldwide ET₀ validation
  - Comprehensive validation across different climate zones
  - Regular accuracy assessments against reference data

- **Brazilian Regional Validation**:
  - Validation against Xavier's Brazilian Daily Weather Gridded Dataset
  - High-resolution (0.25° x 0.25°) meteorological data covering Brazil
  - Extensive ground-truth validation using weather station data
  - Reference dataset specifically developed for Brazilian conditions

#### Automated Features
- **MATOPIBA Heat Maps**: 
  - Dynamic ET₀ visualization updated three times daily
  - High-resolution spatial coverage of the region

- **Global Elevation Integration**:
  - Automated elevation retrieval for any location
  - Ensures accurate ET₀ calculations worldwide

*Note: EVAonline employs sophisticated data fusion algorithms to combine multiple real-time data sources, with AgERA5 serving as an independent validation dataset to ensure calculation accuracy.*

### Visualization
- **Interactive Maps**: GeoJSON layers with OpenStreetMap tiles
- **Heatmaps**: Kernel density estimation for city distribution
- **Real-time Updates**: WebSocket-powered live data refresh
- **Statistical Analysis**: Correlation matrices, trend analysis

### Performance
- **Redis Caching**: Sub-second response times for repeated queries
- **Async Processing**: Celery workers for heavy computations
- **Spatial Indexing**: PostGIS GIST indices for fast geospatial queries

## 🛠️ Development

### Local Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run services locally:**
   ```bash
   # Start database and cache
   docker-compose up postgres redis -d
   
   # Run API server
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   
   # Run Dash app
   python pages/main.py
   
   # Run Celery worker
   celery -A api.celery_config worker --loglevel=info
   ```

### API Endpoints

- `GET /api/geo_data`: Retrieve GeoJSON data
- `WebSocket /ws/geo_data`: Real-time data updates
- `POST /api/calculate_eto`: Calculate evapotranspiration

## 📈 Monitoring

The application includes comprehensive monitoring:

- **Prometheus Metrics**: API response times, database queries, cache hit rates
- **Grafana Dashboards**: Visual monitoring of system performance
- **Application Logs**: Structured logging with Loguru

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.

## 🎯 Citation

If you use EVAonline in your research, please cite:

```bibtex
@article{evaonline2024,
  title={EVAonline: An online tool for reference evapotranspiration estimation},
  author={Your Name},
  journal={SoftwareX},
  year={2024}
}
```

## 📞 Support

For questions and support:
- Create an issue in this repository
- Contact: [your-email@domain.com]

---

Built with ❤️ for the agricultural and environmental research community.

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