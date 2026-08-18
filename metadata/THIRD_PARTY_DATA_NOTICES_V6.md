# Third-Party Data Notices

This file must accompany any public archive that includes the approved raw or processed source tables.
The benchmark's own code and annotations may use a separate project license; that license does not
replace the source-specific terms below.

## epa_annual_aqi_county

- Release decision: INCLUDED
- Source: EPA AirData annual AQI by county, 2023 (https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_2023.zip)
- Acquisition path: https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_2023.zip
- License/terms: U.S. public domain (https://www.epa.gov/outdoor-air-quality-data/do-i-need-request-permission-use-monitoring-data-and-graphics-airdata)
- Attribution: U.S. Environmental Protection Agency, Air Quality System (AQS), annual AQI by county, 2023.
- Changes: The project retained selected AQI summary fields and normalized field names.

## epa_annual_aqi_state

- Release decision: INCLUDED
- Source: EPA AirData annual AQI by county, 2023 (https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_2023.zip)
- Acquisition path: Derived locally from epa_annual_aqi_county
- License/terms: U.S. public domain (https://www.epa.gov/outdoor-air-quality-data/do-i-need-request-permission-use-monitoring-data-and-graphics-airdata)
- Attribution: U.S. Environmental Protection Agency, Air Quality System (AQS), annual AQI by county, 2023.
- Changes: The project aggregated county-level AQI fields to state-year means.

## nasa_giss_global_temperature_monthly

- Release decision: INCLUDED
- Source: NASA GISS Surface Temperature Analysis (GISTEMP v4) (https://data.giss.nasa.gov/gistemp/)
- Acquisition path: https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv
- License/terms: CC0 / U.S. public domain unless specifically marked otherwise (https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy)
- Attribution: NASA Goddard Institute for Space Studies, GISS Surface Temperature Analysis (GISTEMP v4), global monthly temperature anomalies.
- Changes: The project reshaped the year-by-month table into long monthly records.

## owid_annual_co2_emissions

- Release decision: INCLUDED
- Source: annual-co2-emissions-per-country (https://ourworldindata.org/grapher/annual-co2-emissions-per-country)
- Acquisition path: https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0 (https://ourworldindata.org/faqs)
- Attribution: Global Carbon Budget (2025) – with major processing by Our World in Data. “Annual CO₂ emissions” [dataset]. Global Carbon Project, “Global Carbon Budget v15” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_child_mortality

- Release decision: INCLUDED
- Source: child-mortality (https://ourworldindata.org/grapher/child-mortality)
- Acquisition path: https://ourworldindata.org/grapher/child-mortality.csv
- License/terms: OWID CC BY plus upstream licenses: Copyright © UNICEF; CC BY 4.0; CC BY 4.0# License (same as origin.license, for backwards compatibility) (https://ourworldindata.org/faqs)
- Attribution: Gapminder (2015); UN Inter-agency Group for Child Mortality Estimation (2025) – processed by Our World in Data. “Child mortality rate – Gapminder; UN IGME – Long-run data” [dataset]. United Nations Inter-agency Group for Child Mortality Estimation, “United Nations Inter-agency Group for Child Mortality Estimation 2025”; Gapminder, “Child mortality rate under age five v7”; Gapminder based on UN IGME & UN WPP, “Under-five Mortality v11” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_co2_emissions_per_capita

- Release decision: INCLUDED
- Source: co-emissions-per-capita (https://ourworldindata.org/grapher/co-emissions-per-capita)
- Acquisition path: https://ourworldindata.org/grapher/co-emissions-per-capita.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0 (https://ourworldindata.org/faqs)
- Attribution: Global Carbon Budget (2025); Population based on various sources (2024) – with major processing by Our World in Data. “CO₂ emissions per capita” [dataset]. Global Carbon Project, “Global Carbon Budget v15”; Various sources, “Population” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_electricity_mix_by_source

- Release decision: INCLUDED
- Source: electricity-prod-source-stacked (https://ourworldindata.org/grapher/electricity-prod-source-stacked)
- Acquisition path: https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0; © Energy Institute 2026; Open Government Licence v3.0 (https://ourworldindata.org/faqs)
- Attribution: Ember (2026); Pinto et al. (2023); Energy Institute - Statistical Review of World Energy (2026) – with major processing by Our World in Data. “Electricity generation from other renewables” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Pinto et al., “Global historical electricity”; Energy Institute, “Statistical Review of World Energy” [original data]. | Ember (2026); Pinto et al. (2023) – with major processing by Our World in Data. “Electricity generation from bioenergy” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Pinto et al., “Global historical electricity” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023) – with major processing by Our World in Data. “Electricity generation from solar power” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023) – with major processing by Our World in Data. “Electricity generation from wind power” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Electricity generation from hydropower” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Electricity generation from nuclear” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Electricity generation from gas” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Electricity generation from oil” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data]. | Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Electricity generation from coal” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_life_expectancy

- Release decision: INCLUDED
- Source: life-expectancy (https://ourworldindata.org/grapher/life-expectancy)
- Acquisition path: https://ourworldindata.org/grapher/life-expectancy.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0; CC BY 3.0 IGO; CC0 1.0 Universal; JSTOR terms (https://ourworldindata.org/faqs)
- Attribution: Riley (2005); Zijdeman et al. (2015); HMD (2025); UN WPP (2024) – with major processing by Our World in Data. “Life expectancy – Riley; Zijdeman et al.; HMD; UN WPP – Long-run data” [dataset]. Human Mortality Database, “Human Mortality Database”; United Nations, “World Population Prospects”; United Nations, “World Population Prospects - Interim Update”; Zijdeman et al., “Life Expectancy at birth v2”; James C. Riley, “Estimates of Regional and Global Life Expectancy, 1800-2001” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_population

- Release decision: INCLUDED
- Source: population (https://ourworldindata.org/grapher/population)
- Acquisition path: https://ourworldindata.org/grapher/population.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0; CC BY 3.0 IGO (https://ourworldindata.org/faqs)
- Attribution: HYDE (2023); Gapminder (2022); UN WPP (2024) – with major processing by Our World in Data. “Population – HYDE, Gapminder, UN – Long-run data” [dataset]. PBL Netherlands Environmental Assessment Agency, “History Database of the Global Environment 3.3”; Gapminder, “Population v7”; United Nations, “World Population Prospects”; United Nations, “World Population Prospects - Interim Update”; Gapminder, “Systema Globalis” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_renewable_share_energy

- Release decision: INCLUDED
- Source: renewable-share-energy (https://ourworldindata.org/grapher/renewable-share-energy)
- Acquisition path: https://ourworldindata.org/grapher/renewable-share-energy.csv
- License/terms: OWID CC BY plus upstream licenses: © Energy Institute 2026; CC BY 4.0; Public domain (https://ourworldindata.org/faqs)
- Attribution: Energy Institute - Statistical Review of World Energy (2026); Smil (2017); U.S. Energy Information Administration (2026) – with major processing by Our World in Data. “Renewables as a share of total energy supply” [dataset]. Energy Institute, “Statistical Review of World Energy”; Smil, “Energy Transitions: Global and National Perspectives”; U.S. Energy Information Administration, “International Energy Data” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## owid_share_electricity_renewables

- Release decision: INCLUDED
- Source: share-electricity-renewables (https://ourworldindata.org/grapher/share-electricity-renewables)
- Acquisition path: https://ourworldindata.org/grapher/share-electricity-renewables.csv
- License/terms: OWID CC BY plus upstream licenses: CC BY 4.0; © Energy Institute 2026; Open Government Licence v3.0 (https://ourworldindata.org/faqs)
- Attribution: Ember (2026); Energy Institute - Statistical Review of World Energy (2026); Pinto et al. (2023); Department for Business, Energy & Industrial Strategy of the UK (2023) – with major processing by Our World in Data. “Share of electricity generated by renewables” [dataset]. Ember, “Yearly Electricity Data Europe”; Ember, “Yearly Electricity Data”; Energy Institute, “Statistical Review of World Energy”; Pinto et al., “Global historical electricity”; Department for Business, Energy & Industrial Strategy of the UK, “UK's historical electricity data” [original data].
- Changes: Downloaded through the OWID Grapher API and normalized for benchmark construction.

## uci_breast_cancer_wdbc

- Release decision: INCLUDED
- Source: Breast Cancer Wisconsin (Diagnostic) (https://archive.ics.uci.edu/dataset/17/breast-cancer-wisconsin-diagnostic)
- Acquisition path: https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data
- License/terms: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- Attribution: Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B.
- Changes: Column names were normalized for benchmark construction.

## uci_iris

- Release decision: INCLUDED
- Source: Iris (https://archive.ics.uci.edu/dataset/53/iris)
- Acquisition path: https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data
- License/terms: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- Attribution: Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C56C76.
- Changes: Column names were normalized for benchmark construction.

## uci_wine

- Release decision: INCLUDED
- Source: Wine (https://archive.ics.uci.edu/dataset/109/wine)
- Acquisition path: https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data
- License/terms: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- Attribution: Aeberhard, S. & Forina, M. (1992). Wine [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5PC7J.
- Changes: Column names were normalized for benchmark construction.

## us_agriculture_exports_2011

- Release decision: INCLUDED
- Source: USDA ERS State Agricultural Trade Data, 2011 state export estimates (https://www.ers.usda.gov/data-products/state-agricultural-trade-data)
- Acquisition path: https://raw.githubusercontent.com/plotly/datasets/master/2011_us_ag_exports.csv
- License/terms: U.S. public domain for federal data; Plotly mirror used only as acquisition path (https://www.nal.usda.gov/services/data-management-planning)
- Attribution: U.S. Department of Agriculture, Economic Research Service, State Agricultural Trade Data. Historical 2011 construction copy acquired through the Plotly Datasets mirror.
- Changes: Field names were normalized; values are in millions of U.S. dollars as supplied by the mirror.

## us_agriculture_exports_2011_long

- Release decision: INCLUDED
- Source: USDA ERS State Agricultural Trade Data, 2011 state export estimates (https://www.ers.usda.gov/data-products/state-agricultural-trade-data)
- Acquisition path: Derived locally from us_agriculture_exports_2011
- License/terms: U.S. public domain for federal data; Plotly mirror used only as acquisition path (https://www.nal.usda.gov/services/data-management-planning)
- Attribution: U.S. Department of Agriculture, Economic Research Service, State Agricultural Trade Data. Historical 2011 construction copy acquired through the Plotly Datasets mirror.
- Changes: The project reshaped commodity columns into state-product long records.

## usgs_earthquake_region_monthly

- Release decision: INCLUDED
- Source: USGS Earthquake Catalog, magnitude 5+, 2022-2024 (https://earthquake.usgs.gov/fdsnws/event/1/)
- Acquisition path: Derived locally from usgs_earthquakes_mag5_2022_2024
- License/terms: U.S. public domain / USGS open-data guidance (https://www.usgs.gov/data-management/data-licensing)
- Attribution: U.S. Geological Survey, Earthquake Hazards Program, FDSN Event Web Service, magnitude 5+ events from 2022 through 2024.
- Changes: The project aggregated event counts, magnitude, and depth by region, year, and month.

## usgs_earthquakes_mag5_2022_2024

- Release decision: INCLUDED
- Source: USGS Earthquake Catalog, magnitude 5+, 2022-2024 (https://earthquake.usgs.gov/fdsnws/event/1/)
- Acquisition path: https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2022-01-01&endtime=2024-12-31&minmagnitude=5.0&orderby=time-asc
- License/terms: U.S. public domain / USGS open-data guidance (https://www.usgs.gov/data-management/data-licensing)
- Attribution: U.S. Geological Survey, Earthquake Hazards Program, FDSN Event Web Service, magnitude 5+ events from 2022 through 2024.
- Changes: Dates and geographic region labels were normalized and selected event fields were retained.

## vega_cars

- Release decision: INCLUDED
- Source: Auto MPG / StatLib Cars (https://archive.ics.uci.edu/dataset/9/auto-mpg)
- Acquisition path: https://raw.githubusercontent.com/vega/vega-datasets/main/data/cars.json
- License/terms: CC BY 4.0 (upstream UCI Auto MPG dataset) (https://creativecommons.org/licenses/by/4.0/)
- Attribution: Quinlan, R. (1993). Auto MPG [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5859H. Data acquired through the Vega Datasets mirror.
- Changes: Vega normalized the StatLib records; this project converted JSON to CSV and normalized field names.

## vega_stocks

- Release decision: EXCLUDED FROM PUBLIC RAW-TABLE ARCHIVE
- Source: Vega monthly stock price example (https://github.com/vega/vega-datasets/blob/main/data/stocks.csv)
- Acquisition path: https://raw.githubusercontent.com/vega/vega-datasets/main/data/stocks.csv
- License/terms: Not specified for this dataset (https://github.com/vega/vega-datasets/blob/main/datapackage.md#stockscsv)
- Attribution: Vega Datasets, stocks.csv. Original market-data provider and dataset license are not identified in the repository metadata.
- Changes: Dates and field names were normalized for benchmark construction.

## vega_unemployment_industries

- Release decision: INCLUDED
- Source: Industry unemployment from the Current Population Survey (https://www.bls.gov/web/empsit/cpseea31.htm)
- Acquisition path: https://raw.githubusercontent.com/vega/vega-datasets/main/data/unemployment-across-industries.json
- License/terms: U.S. Government public domain, subject to BLS attribution and representation terms (https://www.bls.gov/developers/termsOfService.htm)
- Attribution: U.S. Bureau of Labor Statistics, Current Population Survey, Table A-31. Data acquired through the Vega Datasets mirror. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.
- Changes: Vega transformed monthly CPS/BLS records; this project converted JSON to CSV and normalized field names.

## vega_weather_seattle

- Release decision: INCLUDED
- Source: Seattle daily weather (https://www.ncei.noaa.gov/cdo-web/datatools/records)
- Acquisition path: https://raw.githubusercontent.com/vega/vega-datasets/main/data/seattle-weather.csv
- License/terms: U.S. Government public domain; NOAA/NCEI open-data policy (https://www.ncei.noaa.gov/archive)
- Attribution: National Oceanic and Atmospheric Administration, National Centers for Environmental Information. Data acquired through the Vega Datasets mirror.
- Changes: Vega converted units and synthesized the categorical weather field; this project normalized field names.

## world_bank_countries

- Release decision: INCLUDED
- Source: World Bank country metadata API (https://api.worldbank.org/v2/country?format=json&per_page=400)
- Acquisition path: https://api.worldbank.org/v2/country?format=json&per_page=400
- License/terms: CC BY 4.0 (World Bank-produced open data default) (https://datacatalog.worldbank.org/public-licenses)
- Attribution: World Bank. Country metadata, World Bank API. Licensed under CC BY 4.0; changes were made for benchmark construction.
- Changes: Selected country, region, income, capital, and coordinate fields were exported to CSV.

## world_bank_wdi_core_long

- Release decision: INCLUDED
- Source: World Development Indicators core selection (https://databank.worldbank.org/source/world-development-indicators)
- Acquisition path: https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000&page={page}
- License/terms: CC BY 4.0 (World Bank-produced open data default) (https://datacatalog.worldbank.org/public-licenses)
- Attribution: World Bank. World Development Indicators. Licensed under CC BY 4.0; changes were made for benchmark construction.
- Changes: Nine WDI indicators were joined with country metadata and reshaped into a long table.

## world_bank_wdi_core_wide

- Release decision: INCLUDED
- Source: World Development Indicators core selection (https://databank.worldbank.org/source/world-development-indicators)
- Acquisition path: https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000&page={page}
- License/terms: CC BY 4.0 (World Bank-produced open data default) (https://datacatalog.worldbank.org/public-licenses)
- Attribution: World Bank. World Development Indicators. Licensed under CC BY 4.0; changes were made for benchmark construction.
- Changes: The project pivoted the selected WDI long table into a country-year wide table.
