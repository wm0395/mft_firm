# IPO Pilot Event Study

## Objective

Test whether the seed IPO sample shows a repeatable pull-and-release pattern in local market data.

## Seed Sample

| company_name | symbol_after_listing | pressure_class | subscription_total_multiple | ipo_open_date | ipo_close_date | allotment_date | listing_date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rubicon Research Limited | RUBICON | extreme | 109.37 | 2025-10-09 | 2025-10-13 | 2025-10-14 | 2025-10-16 |
| Sudeep Pharma Limited | SUDEEPPHRM | extreme | 65.96 | 2025-11-21 | 2025-11-25 | 2025-11-26 | 2025-11-28 |
| Urban Company Limited | URBANCO | extreme | 60.49 | 2025-09-10 | 2025-09-12 | 2025-09-16 | 2025-09-17 |
| TruAlt Bioenergy Limited | TRUALT | extreme | 52.93 | 2025-09-25 | 2025-09-29 | 2025-09-30 | 2025-10-03 |
| LG Electronics India Limited | LGEINDIA | extreme | 38.17 | 2025-10-07 | 2025-10-09 | 2025-10-13 | 2025-10-14 |
| Lenskart Solutions Limited | LENSKART | extreme | 28.35 | 2025-10-31 | 2025-11-04 | 2025-11-06 | 2025-11-10 |
| Vishal Mega Mart Limited | VMM | high | 20.46768 | 2024-12-11 | 2024-12-13 | 2024-12-17 | 2024-12-18 |
| HDB Financial Services Limited | HDBFS | high | 17.62 | 2025-06-25 | 2025-06-27 | 2025-07-01 | 2025-07-02 |
| Medi Assist Healthcare Services Limited | MEDIASSIST | high | 11.71 | 2024-01-15 | 2024-01-17 | 2024-01-18 | 2024-01-22 |
| Canara Robeco Asset Management Company Limited | CRAMC | high | 7.12 | 2025-10-09 | 2025-10-13 | 2025-10-15 | 2025-10-16 |
| Saatvik Green Energy Limited | SAATVIK | medium | 5.14 | 2025-09-19 | 2025-09-23 | 2025-09-24 | 2025-09-26 |
| Om Freight Forwarders Limited | OMFREIGHT | medium | 3.39 | 2025-09-29 | 2025-10-03 | 2025-10-06 | 2025-10-08 |
| Brigade Hotel Ventures Limited | BRIGHOTEL | medium | 3.15 | 2025-07-24 | 2025-07-28 | 2025-07-29 | 2025-07-31 |
| Sagility India Limited | SAGILITY | medium | 3.14 | 2024-11-05 | 2024-11-07 | 2024-11-08 | 2024-11-12 |
| Schloss Bangalore Limited | THELEELA | medium | 3.06 | 2025-05-26 | 2025-05-28 | 2025-05-29 | 2025-06-02 |
| Travel Food Services Limited | TRAVELFOOD | medium | 3.04 | 2025-07-07 | 2025-07-09 | 2025-07-10 | 2025-07-14 |
| Fabtech Technologies Limited | FABTECH | medium | 2.85 | 2025-09-29 | 2025-10-01 | 2025-10-03 | 2025-10-07 |
| Afcons Infrastructure Limited | AFCONS | medium | 2.77 | 2024-10-25 | 2024-10-29 | 2024-10-30 | 2024-11-04 |
| Glottis Limited | GLOTTIS | low | 1.98 | 2025-09-29 | 2025-10-01 | 2025-10-03 | 2025-10-07 |
| One 97 Communications Limited | PAYTM | low | 1.95 | 2021-11-08 | 2021-11-10 | 2021-11-15 | 2021-11-18 |
| NTPC Green Energy Limited | NTPCGREEN | low | 1.94 | 2024-11-19 | 2024-11-22 | 2024-11-26 | 2024-11-27 |
| Canara HSBC Life Insurance Company Limited | CANHLIFE | low | 1.91 | 2025-10-10 | 2025-10-14 | 2025-10-16 | 2025-10-17 |
| Niva Bupa Health Insurance Company Limited | NIVABUPA | low | 1.9 | 2024-11-07 | 2024-11-11 | 2024-11-12 | 2024-11-14 |
| Aegis Vopak Terminals Limited | AEGISVOPAK | low | 1.66 | 2025-05-26 | 2025-05-28 | 2025-05-29 | 2025-06-02 |
| Ather Energy Limited | ATHERENERG | low | 1.5 | 2025-04-28 | 2025-04-30 | 2025-05-02 | 2025-05-06 |
| Euro Pratik Sales Limited | EUROPRATIK | low | 1.41 | 2025-09-16 | 2025-09-18 | 2025-09-19 | 2025-09-23 |
| Yatra Online Limited | YATRA | low | 1.39 | 2023-09-15 | 2023-09-20 | 2023-09-24 | 2023-09-28 |
| Delhivery Limited | DELHIVERY | low | 1.33 | 2022-05-11 | 2022-05-13 | 2022-05-19 | 2022-05-24 |

## Window Coverage

| ipo_id | company_name | symbol_after_listing | pressure_class | window_name | window_start | window_end | window_empty |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rubicon_research_2025 | Rubicon Research Limited | RUBICON | extreme | application | 2025-10-09 | 2025-10-13 | no |
| rubicon_research_2025 | Rubicon Research Limited | RUBICON | extreme | blocking | 2025-10-14 | 2025-10-13 | yes |
| rubicon_research_2025 | Rubicon Research Limited | RUBICON | extreme | release_3 | 2025-10-14 | 2025-10-17 | no |
| rubicon_research_2025 | Rubicon Research Limited | RUBICON | extreme | release_5 | 2025-10-14 | 2025-10-19 | no |
| rubicon_research_2025 | Rubicon Research Limited | RUBICON | extreme | listing_5 | 2025-10-16 | 2025-10-21 | no |
| sudeep_pharma_2025 | Sudeep Pharma Limited | SUDEEPPHRM | extreme | application | 2025-11-21 | 2025-11-25 | no |
| sudeep_pharma_2025 | Sudeep Pharma Limited | SUDEEPPHRM | extreme | blocking | 2025-11-26 | 2025-11-25 | yes |
| sudeep_pharma_2025 | Sudeep Pharma Limited | SUDEEPPHRM | extreme | release_3 | 2025-11-26 | 2025-11-29 | no |
| sudeep_pharma_2025 | Sudeep Pharma Limited | SUDEEPPHRM | extreme | release_5 | 2025-11-26 | 2025-12-01 | no |
| sudeep_pharma_2025 | Sudeep Pharma Limited | SUDEEPPHRM | extreme | listing_5 | 2025-11-28 | 2025-12-03 | no |
| urban_company_2025 | Urban Company Limited | URBANCO | extreme | application | 2025-09-10 | 2025-09-12 | no |
| urban_company_2025 | Urban Company Limited | URBANCO | extreme | blocking | 2025-09-13 | 2025-09-15 | no |
| urban_company_2025 | Urban Company Limited | URBANCO | extreme | release_3 | 2025-09-16 | 2025-09-19 | no |
| urban_company_2025 | Urban Company Limited | URBANCO | extreme | release_5 | 2025-09-16 | 2025-09-21 | no |
| urban_company_2025 | Urban Company Limited | URBANCO | extreme | listing_5 | 2025-09-17 | 2025-09-22 | no |
| trualt_bioenergy_2025 | TruAlt Bioenergy Limited | TRUALT | extreme | application | 2025-09-25 | 2025-09-29 | no |
| trualt_bioenergy_2025 | TruAlt Bioenergy Limited | TRUALT | extreme | blocking | 2025-09-30 | 2025-09-29 | yes |
| trualt_bioenergy_2025 | TruAlt Bioenergy Limited | TRUALT | extreme | release_3 | 2025-09-30 | 2025-10-03 | no |
| trualt_bioenergy_2025 | TruAlt Bioenergy Limited | TRUALT | extreme | release_5 | 2025-09-30 | 2025-10-05 | no |
| trualt_bioenergy_2025 | TruAlt Bioenergy Limited | TRUALT | extreme | listing_5 | 2025-10-03 | 2025-10-08 | no |
| lgelectronics_india_2025 | LG Electronics India Limited | LGEINDIA | extreme | application | 2025-10-07 | 2025-10-09 | no |
| lgelectronics_india_2025 | LG Electronics India Limited | LGEINDIA | extreme | blocking | 2025-10-10 | 2025-10-12 | no |
| lgelectronics_india_2025 | LG Electronics India Limited | LGEINDIA | extreme | release_3 | 2025-10-13 | 2025-10-16 | no |
| lgelectronics_india_2025 | LG Electronics India Limited | LGEINDIA | extreme | release_5 | 2025-10-13 | 2025-10-18 | no |
| lgelectronics_india_2025 | LG Electronics India Limited | LGEINDIA | extreme | listing_5 | 2025-10-14 | 2025-10-19 | no |
| lenskart_solutions_2025 | Lenskart Solutions Limited | LENSKART | extreme | application | 2025-10-31 | 2025-11-04 | no |
| lenskart_solutions_2025 | Lenskart Solutions Limited | LENSKART | extreme | blocking | 2025-11-05 | 2025-11-05 | no |
| lenskart_solutions_2025 | Lenskart Solutions Limited | LENSKART | extreme | release_3 | 2025-11-06 | 2025-11-09 | no |
| lenskart_solutions_2025 | Lenskart Solutions Limited | LENSKART | extreme | release_5 | 2025-11-06 | 2025-11-11 | no |
| lenskart_solutions_2025 | Lenskart Solutions Limited | LENSKART | extreme | listing_5 | 2025-11-10 | 2025-11-15 | no |
| vishal_mega_mart_2024 | Vishal Mega Mart Limited | VMM | high | application | 2024-12-11 | 2024-12-13 | no |
| vishal_mega_mart_2024 | Vishal Mega Mart Limited | VMM | high | blocking | 2024-12-14 | 2024-12-16 | no |
| vishal_mega_mart_2024 | Vishal Mega Mart Limited | VMM | high | release_3 | 2024-12-17 | 2024-12-20 | no |
| vishal_mega_mart_2024 | Vishal Mega Mart Limited | VMM | high | release_5 | 2024-12-17 | 2024-12-22 | no |
| vishal_mega_mart_2024 | Vishal Mega Mart Limited | VMM | high | listing_5 | 2024-12-18 | 2024-12-23 | no |
| hdb_financial_services_2025 | HDB Financial Services Limited | HDBFS | high | application | 2025-06-25 | 2025-06-27 | no |
| hdb_financial_services_2025 | HDB Financial Services Limited | HDBFS | high | blocking | 2025-06-28 | 2025-06-30 | no |
| hdb_financial_services_2025 | HDB Financial Services Limited | HDBFS | high | release_3 | 2025-07-01 | 2025-07-04 | no |
| hdb_financial_services_2025 | HDB Financial Services Limited | HDBFS | high | release_5 | 2025-07-01 | 2025-07-06 | no |
| hdb_financial_services_2025 | HDB Financial Services Limited | HDBFS | high | listing_5 | 2025-07-02 | 2025-07-07 | no |
| medi_assist_healthcare_2024 | Medi Assist Healthcare Services Limited | MEDIASSIST | high | application | 2024-01-15 | 2024-01-17 | no |
| medi_assist_healthcare_2024 | Medi Assist Healthcare Services Limited | MEDIASSIST | high | blocking | 2024-01-18 | 2024-01-17 | yes |
| medi_assist_healthcare_2024 | Medi Assist Healthcare Services Limited | MEDIASSIST | high | release_3 | 2024-01-18 | 2024-01-21 | no |
| medi_assist_healthcare_2024 | Medi Assist Healthcare Services Limited | MEDIASSIST | high | release_5 | 2024-01-18 | 2024-01-23 | no |
| medi_assist_healthcare_2024 | Medi Assist Healthcare Services Limited | MEDIASSIST | high | listing_5 | 2024-01-22 | 2024-01-27 | no |
| canara_robeco_2025 | Canara Robeco Asset Management Company Limited | CRAMC | high | application | 2025-10-09 | 2025-10-13 | no |
| canara_robeco_2025 | Canara Robeco Asset Management Company Limited | CRAMC | high | blocking | 2025-10-14 | 2025-10-14 | no |
| canara_robeco_2025 | Canara Robeco Asset Management Company Limited | CRAMC | high | release_3 | 2025-10-15 | 2025-10-18 | no |
| canara_robeco_2025 | Canara Robeco Asset Management Company Limited | CRAMC | high | release_5 | 2025-10-15 | 2025-10-20 | no |
| canara_robeco_2025 | Canara Robeco Asset Management Company Limited | CRAMC | high | listing_5 | 2025-10-16 | 2025-10-21 | no |
| saatvik_green_energy_2025 | Saatvik Green Energy Limited | SAATVIK | medium | application | 2025-09-19 | 2025-09-23 | no |
| saatvik_green_energy_2025 | Saatvik Green Energy Limited | SAATVIK | medium | blocking | 2025-09-24 | 2025-09-23 | yes |
| saatvik_green_energy_2025 | Saatvik Green Energy Limited | SAATVIK | medium | release_3 | 2025-09-24 | 2025-09-27 | no |
| saatvik_green_energy_2025 | Saatvik Green Energy Limited | SAATVIK | medium | release_5 | 2025-09-24 | 2025-09-29 | no |
| saatvik_green_energy_2025 | Saatvik Green Energy Limited | SAATVIK | medium | listing_5 | 2025-09-26 | 2025-10-01 | no |
| om_freight_forwarders_2025 | Om Freight Forwarders Limited | OMFREIGHT | medium | application | 2025-09-29 | 2025-10-03 | no |
| om_freight_forwarders_2025 | Om Freight Forwarders Limited | OMFREIGHT | medium | blocking | 2025-10-04 | 2025-10-05 | no |
| om_freight_forwarders_2025 | Om Freight Forwarders Limited | OMFREIGHT | medium | release_3 | 2025-10-06 | 2025-10-09 | no |
| om_freight_forwarders_2025 | Om Freight Forwarders Limited | OMFREIGHT | medium | release_5 | 2025-10-06 | 2025-10-11 | no |
| om_freight_forwarders_2025 | Om Freight Forwarders Limited | OMFREIGHT | medium | listing_5 | 2025-10-08 | 2025-10-13 | no |
| brigade_hotel_ventures_2025 | Brigade Hotel Ventures Limited | BRIGHOTEL | medium | application | 2025-07-24 | 2025-07-28 | no |
| brigade_hotel_ventures_2025 | Brigade Hotel Ventures Limited | BRIGHOTEL | medium | blocking | 2025-07-29 | 2025-07-28 | yes |
| brigade_hotel_ventures_2025 | Brigade Hotel Ventures Limited | BRIGHOTEL | medium | release_3 | 2025-07-29 | 2025-08-01 | no |
| brigade_hotel_ventures_2025 | Brigade Hotel Ventures Limited | BRIGHOTEL | medium | release_5 | 2025-07-29 | 2025-08-03 | no |
| brigade_hotel_ventures_2025 | Brigade Hotel Ventures Limited | BRIGHOTEL | medium | listing_5 | 2025-07-31 | 2025-08-05 | no |
| sagility_india_2024 | Sagility India Limited | SAGILITY | medium | application | 2024-11-05 | 2024-11-07 | no |
| sagility_india_2024 | Sagility India Limited | SAGILITY | medium | blocking | 2024-11-08 | 2024-11-07 | yes |
| sagility_india_2024 | Sagility India Limited | SAGILITY | medium | release_3 | 2024-11-08 | 2024-11-11 | no |
| sagility_india_2024 | Sagility India Limited | SAGILITY | medium | release_5 | 2024-11-08 | 2024-11-13 | no |
| sagility_india_2024 | Sagility India Limited | SAGILITY | medium | listing_5 | 2024-11-12 | 2024-11-17 | no |
| schloss_bangalore_2025 | Schloss Bangalore Limited | THELEELA | medium | application | 2025-05-26 | 2025-05-28 | no |
| schloss_bangalore_2025 | Schloss Bangalore Limited | THELEELA | medium | blocking | 2025-05-29 | 2025-05-28 | yes |
| schloss_bangalore_2025 | Schloss Bangalore Limited | THELEELA | medium | release_3 | 2025-05-29 | 2025-06-01 | no |
| schloss_bangalore_2025 | Schloss Bangalore Limited | THELEELA | medium | release_5 | 2025-05-29 | 2025-06-03 | no |
| schloss_bangalore_2025 | Schloss Bangalore Limited | THELEELA | medium | listing_5 | 2025-06-02 | 2025-06-07 | no |
| travel_food_services_2025 | Travel Food Services Limited | TRAVELFOOD | medium | application | 2025-07-07 | 2025-07-09 | no |
| travel_food_services_2025 | Travel Food Services Limited | TRAVELFOOD | medium | blocking | 2025-07-10 | 2025-07-09 | yes |
| travel_food_services_2025 | Travel Food Services Limited | TRAVELFOOD | medium | release_3 | 2025-07-10 | 2025-07-13 | no |
| travel_food_services_2025 | Travel Food Services Limited | TRAVELFOOD | medium | release_5 | 2025-07-10 | 2025-07-15 | no |
| travel_food_services_2025 | Travel Food Services Limited | TRAVELFOOD | medium | listing_5 | 2025-07-14 | 2025-07-19 | no |
| fabtech_technologies_2025 | Fabtech Technologies Limited | FABTECH | medium | application | 2025-09-29 | 2025-10-01 | no |
| fabtech_technologies_2025 | Fabtech Technologies Limited | FABTECH | medium | blocking | 2025-10-02 | 2025-10-02 | no |
| fabtech_technologies_2025 | Fabtech Technologies Limited | FABTECH | medium | release_3 | 2025-10-03 | 2025-10-06 | no |
| fabtech_technologies_2025 | Fabtech Technologies Limited | FABTECH | medium | release_5 | 2025-10-03 | 2025-10-08 | no |
| fabtech_technologies_2025 | Fabtech Technologies Limited | FABTECH | medium | listing_5 | 2025-10-07 | 2025-10-12 | no |
| afcons_infrastructure_2024 | Afcons Infrastructure Limited | AFCONS | medium | application | 2024-10-25 | 2024-10-29 | no |
| afcons_infrastructure_2024 | Afcons Infrastructure Limited | AFCONS | medium | blocking | 2024-10-30 | 2024-10-29 | yes |
| afcons_infrastructure_2024 | Afcons Infrastructure Limited | AFCONS | medium | release_3 | 2024-10-30 | 2024-11-02 | no |
| afcons_infrastructure_2024 | Afcons Infrastructure Limited | AFCONS | medium | release_5 | 2024-10-30 | 2024-11-04 | no |
| afcons_infrastructure_2024 | Afcons Infrastructure Limited | AFCONS | medium | listing_5 | 2024-11-04 | 2024-11-09 | no |
| glottis_2025 | Glottis Limited | GLOTTIS | low | application | 2025-09-29 | 2025-10-01 | no |
| glottis_2025 | Glottis Limited | GLOTTIS | low | blocking | 2025-10-02 | 2025-10-02 | no |
| glottis_2025 | Glottis Limited | GLOTTIS | low | release_3 | 2025-10-03 | 2025-10-06 | no |
| glottis_2025 | Glottis Limited | GLOTTIS | low | release_5 | 2025-10-03 | 2025-10-08 | no |
| glottis_2025 | Glottis Limited | GLOTTIS | low | listing_5 | 2025-10-07 | 2025-10-12 | no |
| one97_communications_2021 | One 97 Communications Limited | PAYTM | low | application | 2021-11-08 | 2021-11-10 | no |
| one97_communications_2021 | One 97 Communications Limited | PAYTM | low | blocking | 2021-11-11 | 2021-11-14 | no |
| one97_communications_2021 | One 97 Communications Limited | PAYTM | low | release_3 | 2021-11-15 | 2021-11-18 | no |
| one97_communications_2021 | One 97 Communications Limited | PAYTM | low | release_5 | 2021-11-15 | 2021-11-20 | no |
| one97_communications_2021 | One 97 Communications Limited | PAYTM | low | listing_5 | 2021-11-18 | 2021-11-23 | no |
| ntpc_green_energy_2024 | NTPC Green Energy Limited | NTPCGREEN | low | application | 2024-11-19 | 2024-11-22 | no |
| ntpc_green_energy_2024 | NTPC Green Energy Limited | NTPCGREEN | low | blocking | 2024-11-23 | 2024-11-25 | no |
| ntpc_green_energy_2024 | NTPC Green Energy Limited | NTPCGREEN | low | release_3 | 2024-11-26 | 2024-11-29 | no |
| ntpc_green_energy_2024 | NTPC Green Energy Limited | NTPCGREEN | low | release_5 | 2024-11-26 | 2024-12-01 | no |
| ntpc_green_energy_2024 | NTPC Green Energy Limited | NTPCGREEN | low | listing_5 | 2024-11-27 | 2024-12-02 | no |
| canara_hsbc_life_2025 | Canara HSBC Life Insurance Company Limited | CANHLIFE | low | application | 2025-10-10 | 2025-10-14 | no |
| canara_hsbc_life_2025 | Canara HSBC Life Insurance Company Limited | CANHLIFE | low | blocking | 2025-10-15 | 2025-10-15 | no |
| canara_hsbc_life_2025 | Canara HSBC Life Insurance Company Limited | CANHLIFE | low | release_3 | 2025-10-16 | 2025-10-19 | no |
| canara_hsbc_life_2025 | Canara HSBC Life Insurance Company Limited | CANHLIFE | low | release_5 | 2025-10-16 | 2025-10-21 | no |
| canara_hsbc_life_2025 | Canara HSBC Life Insurance Company Limited | CANHLIFE | low | listing_5 | 2025-10-17 | 2025-10-22 | no |
| niva_bupa_health_insurance_2024 | Niva Bupa Health Insurance Company Limited | NIVABUPA | low | application | 2024-11-07 | 2024-11-11 | no |
| niva_bupa_health_insurance_2024 | Niva Bupa Health Insurance Company Limited | NIVABUPA | low | blocking | 2024-11-12 | 2024-11-11 | yes |
| niva_bupa_health_insurance_2024 | Niva Bupa Health Insurance Company Limited | NIVABUPA | low | release_3 | 2024-11-12 | 2024-11-15 | no |
| niva_bupa_health_insurance_2024 | Niva Bupa Health Insurance Company Limited | NIVABUPA | low | release_5 | 2024-11-12 | 2024-11-17 | no |
| niva_bupa_health_insurance_2024 | Niva Bupa Health Insurance Company Limited | NIVABUPA | low | listing_5 | 2024-11-14 | 2024-11-19 | no |
| aegis_vopak_terminals_2025 | Aegis Vopak Terminals Limited | AEGISVOPAK | low | application | 2025-05-26 | 2025-05-28 | no |
| aegis_vopak_terminals_2025 | Aegis Vopak Terminals Limited | AEGISVOPAK | low | blocking | 2025-05-29 | 2025-05-28 | yes |
| aegis_vopak_terminals_2025 | Aegis Vopak Terminals Limited | AEGISVOPAK | low | release_3 | 2025-05-29 | 2025-06-01 | no |
| aegis_vopak_terminals_2025 | Aegis Vopak Terminals Limited | AEGISVOPAK | low | release_5 | 2025-05-29 | 2025-06-03 | no |
| aegis_vopak_terminals_2025 | Aegis Vopak Terminals Limited | AEGISVOPAK | low | listing_5 | 2025-06-02 | 2025-06-07 | no |
| ather_energy_2025 | Ather Energy Limited | ATHERENERG | low | application | 2025-04-28 | 2025-04-30 | no |
| ather_energy_2025 | Ather Energy Limited | ATHERENERG | low | blocking | 2025-05-01 | 2025-05-01 | no |
| ather_energy_2025 | Ather Energy Limited | ATHERENERG | low | release_3 | 2025-05-02 | 2025-05-05 | no |
| ather_energy_2025 | Ather Energy Limited | ATHERENERG | low | release_5 | 2025-05-02 | 2025-05-07 | no |
| ather_energy_2025 | Ather Energy Limited | ATHERENERG | low | listing_5 | 2025-05-06 | 2025-05-11 | no |
| euro_pratik_sales_2025 | Euro Pratik Sales Limited | EUROPRATIK | low | application | 2025-09-16 | 2025-09-18 | no |
| euro_pratik_sales_2025 | Euro Pratik Sales Limited | EUROPRATIK | low | blocking | 2025-09-19 | 2025-09-18 | yes |
| euro_pratik_sales_2025 | Euro Pratik Sales Limited | EUROPRATIK | low | release_3 | 2025-09-19 | 2025-09-22 | no |
| euro_pratik_sales_2025 | Euro Pratik Sales Limited | EUROPRATIK | low | release_5 | 2025-09-19 | 2025-09-24 | no |
| euro_pratik_sales_2025 | Euro Pratik Sales Limited | EUROPRATIK | low | listing_5 | 2025-09-23 | 2025-09-28 | no |
| yatra_online_2023 | Yatra Online Limited | YATRA | low | application | 2023-09-15 | 2023-09-20 | no |
| yatra_online_2023 | Yatra Online Limited | YATRA | low | blocking | 2023-09-21 | 2023-09-23 | no |
| yatra_online_2023 | Yatra Online Limited | YATRA | low | release_3 | 2023-09-24 | 2023-09-27 | no |
| yatra_online_2023 | Yatra Online Limited | YATRA | low | release_5 | 2023-09-24 | 2023-09-29 | no |
| yatra_online_2023 | Yatra Online Limited | YATRA | low | listing_5 | 2023-09-28 | 2023-10-03 | no |
| delhivery_2022 | Delhivery Limited | DELHIVERY | low | application | 2022-05-11 | 2022-05-13 | no |
| delhivery_2022 | Delhivery Limited | DELHIVERY | low | blocking | 2022-05-14 | 2022-05-18 | no |
| delhivery_2022 | Delhivery Limited | DELHIVERY | low | release_3 | 2022-05-19 | 2022-05-22 | no |
| delhivery_2022 | Delhivery Limited | DELHIVERY | low | release_5 | 2022-05-19 | 2022-05-24 | no |
| delhivery_2022 | Delhivery Limited | DELHIVERY | low | listing_5 | 2022-05-24 | 2022-05-29 | no |

## Key Reading

- Same-sector peer abnormal returns are mixed across the 28-event seed sample.
- Recent-winners abnormal returns are negative in the application window across the 28-event seed sample; the broader set is mixed.
- Cash-source abnormal returns are positive in the application window for the 28-event seed sample.
- Blocking windows are short or empty in this sample, so the data do not isolate a separate blocking-phase effect.
- Application same sector peer AR averages: extreme -0.0014, high 0.0047, medium 0.0000, low -0.0032.
- Release 5 same sector peer AR averages: extreme -0.0056, high 0.0081, medium 0.0031, low 0.0032.
- Application recent winners 60d top50 AR averages: extreme 0.0005, high -0.0027, medium 0.0053, low -0.0003.
- Release 5 recent winners 60d top50 AR averages: extreme 0.0016, high -0.0003, medium 0.0015, low 0.0049.
- Application cash source 60d top50 AR averages: extreme 0.0017, high 0.0049, medium -0.0003, low 0.0025.
- Release 5 cash source 60d top50 AR averages: extreme 0.0077, high -0.0065, medium -0.0007, low -0.0012.

## Event Detail

| company_name | symbol_after_listing | pressure_class | same_sector_peer | recent_winners_60d_top50 | cash_source_60d_top50 | smallcap250 | midcap150 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aegis Vopak Terminals Limited | AEGISVOPAK | low | 0.0893% | 0.4995% | -0.6607% | 0.3602% | -0.0268% |
| Afcons Infrastructure Limited | AFCONS | medium | 0.0230% | 0.5614% | -0.5205% | -0.0107% | 0.0194% |
| Ather Energy Limited | ATHERENERG | low | 0.6714% | -0.2791% | 1.3640% | -0.1606% | 1.3276% |
| Brigade Hotel Ventures Limited | BRIGHOTEL | medium |  | 0.6538% | -0.5691% | -0.3796% | 0.1303% |
| Canara HSBC Life Insurance Company Limited | CANHLIFE | low | 1.1668% | -0.4581% | 0.4083% | -0.3109% | 0.3082% |
| Canara Robeco Asset Management Company Limited | CRAMC | high | 1.0410% | -0.1384% | 0.4824% | -0.3160% | 0.2497% |
| Delhivery Limited | DELHIVERY | low | -0.1870% | -0.6349% | -0.7382% | -0.3364% | 0.1944% |
| Euro Pratik Sales Limited | EUROPRATIK | low |  | -1.2209% | 0.1146% | 0.0064% | 0.0695% |
| Fabtech Technologies Limited | FABTECH | medium |  | 0.8516% | 0.3574% | 0.1612% | 0.3078% |
| Glottis Limited | GLOTTIS | low |  | 0.8516% | 0.3574% | 0.1612% | 0.3078% |
| HDB Financial Services Limited | HDBFS | high | -0.5416% | -1.1220% | -0.0044% | 0.1857% | -0.6580% |
| LG Electronics India Limited | LGEINDIA | extreme | 1.0224% | 0.6299% | 0.3795% | -0.1831% | 0.3483% |
| Lenskart Solutions Limited | LENSKART | extreme | -0.3299% | 0.9630% | -1.0218% | -0.3541% | 0.0970% |
| Medi Assist Healthcare Services Limited | MEDIASSIST | high |  | -0.9551% | 0.6347% | -0.1390% | 0.7165% |
| NTPC Green Energy Limited | NTPCGREEN | low | -4.0473% | 0.8850% | 0.9876% | 0.0937% | 0.2597% |
| Niva Bupa Health Insurance Company Limited | NIVABUPA | low | 0.3367% | -0.3620% | 0.5556% | 0.0467% | -0.0946% |
| Om Freight Forwarders Limited | OMFREIGHT | medium |  | 0.8504% | 0.1778% | 0.1998% | 0.1344% |
| One 97 Communications Limited | PAYTM | low | -0.2800% | 0.0289% | -0.5437% | -0.2099% | 0.4256% |
| Rubicon Research Limited | RUBICON | extreme | 0.8231% | -0.1384% | 0.4824% | -0.3160% | 0.2497% |
| Saatvik Green Energy Limited | SAATVIK | medium |  | 0.8749% | 0.6028% | -0.3560% | -0.0030% |
| Sagility India Limited | SAGILITY | medium | 1.1451% | 0.3419% | 0.3353% | 0.5567% | -0.3946% |
| Schloss Bangalore Limited | THELEELA | medium | -2.3433% | 0.4995% | -0.6607% | 0.3602% | -0.0268% |
| Sudeep Pharma Limited | SUDEEPPHRM | extreme | -0.1964% | -0.3264% | 0.0601% | -0.0581% | 0.4654% |
| Travel Food Services Limited | TRAVELFOOD | medium | 1.1778% | -0.3756% | 0.0650% | 0.2837% | -0.1939% |
| TruAlt Bioenergy Limited | TRUALT | extreme |  | 0.4927% | 0.8456% | -0.2015% | 0.4094% |
| Urban Company Limited | URBANCO | extreme | -1.9983% | -1.3171% | 0.2898% | -0.0260% | 0.1517% |
| Vishal Mega Mart Limited | VMM | high | 0.9223% | 1.1160% | 0.8345% | -0.3683% | 0.1714% |
| Yatra Online Limited | YATRA | low |  | 0.4018% | 0.6052% | -0.0348% | 0.1851% |

| company_name | symbol_after_listing | pressure_class | same_sector_peer | recent_winners_60d_top50 | cash_source_60d_top50 | smallcap250 | midcap150 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aegis Vopak Terminals Limited | AEGISVOPAK | low | -3.7535% | 0.8258% | -0.1717% | 0.4600% | -0.2001% |
| Afcons Infrastructure Limited | AFCONS | medium | 0.9927% | 1.3244% | -2.1353% | 0.7690% | -1.4353% |
| Ather Energy Limited | ATHERENERG | low | 2.8607% | 0.8481% | 0.4404% | 0.2319% | 0.0140% |
| Brigade Hotel Ventures Limited | BRIGHOTEL | medium |  | 0.7633% | 0.5543% | -0.4348% | -0.0830% |
| Canara HSBC Life Insurance Company Limited | CANHLIFE | low | 0.3354% | -0.4195% | -0.1352% | -0.0190% | -0.5527% |
| Canara Robeco Asset Management Company Limited | CRAMC | high | 1.0823% | -0.4627% | 0.1087% | -0.0262% | -0.1160% |
| Delhivery Limited | DELHIVERY | low | -0.2662% | 0.0985% | -0.5613% | -0.3070% | 0.1739% |
| Euro Pratik Sales Limited | EUROPRATIK | low |  | 1.6927% | 0.2957% | -0.2637% | -0.1245% |
| Fabtech Technologies Limited | FABTECH | medium |  | 0.1816% | 0.4162% | 0.1078% | 0.2848% |
| Glottis Limited | GLOTTIS | low |  | 0.1816% | 0.4162% | 0.1078% | 0.2848% |
| HDB Financial Services Limited | HDBFS | high | -1.1464% | -0.1389% | -1.1890% | -0.1112% | -0.1334% |
| LG Electronics India Limited | LGEINDIA | extreme | 0.6184% | -0.1791% | 1.3457% | -0.3808% | 0.4508% |
| Lenskart Solutions Limited | LENSKART | extreme | -2.4393% | 0.5921% | 1.4767% | -0.3960% | 1.3374% |
| Medi Assist Healthcare Services Limited | MEDIASSIST | high |  | -0.0090% | -0.3585% | -0.0167% | -0.1071% |
| NTPC Green Energy Limited | NTPCGREEN | low | 3.7468% | 0.2914% | -0.8406% | 0.1529% | -0.8808% |
| Niva Bupa Health Insurance Company Limited | NIVABUPA | low | 0.0228% | 0.0414% | -0.0644% | -0.2501% | 0.1750% |
| Om Freight Forwarders Limited | OMFREIGHT | medium |  | -0.3968% | 0.5836% | -0.1447% | 0.5723% |
| One 97 Communications Limited | PAYTM | low | -0.7290% | 0.6168% | 0.3412% | 0.3025% | -0.0773% |
| Rubicon Research Limited | RUBICON | extreme | -0.0142% | -0.0300% | 0.8904% | -0.2813% | 0.3030% |
| Saatvik Green Energy Limited | SAATVIK | medium |  | 0.6562% | 0.5004% | -0.1119% | 0.2876% |
| Sagility India Limited | SAGILITY | medium | 2.6909% | -1.3090% | 1.3517% | -0.5227% | 0.8060% |
| Schloss Bangalore Limited | THELEELA | medium | -2.3861% | 0.8177% | -0.1799% | 0.4759% | -0.2082% |
| Sudeep Pharma Limited | SUDEEPPHRM | extreme | -0.5908% | 0.3309% | 0.8833% | -0.1265% | 0.1900% |
| Travel Food Services Limited | TRAVELFOOD | medium | -0.0420% | -0.8282% | -1.6272% | 0.3817% | -0.2497% |
| TruAlt Bioenergy Limited | TRUALT | extreme |  | 0.3491% | -0.1049% | 0.3224% | -0.1711% |
| Urban Company Limited | URBANCO | extreme | -0.3924% | -0.1217% | 0.1031% | -0.0977% | 0.0025% |
| Vishal Mega Mart Limited | VMM | high | 2.4925% | 0.5038% | -1.1645% | 0.3800% | 0.1190% |
| Yatra Online Limited | YATRA | low |  | 0.7316% | -0.8840% | 0.3804% | 0.0862% |

## Verdict

The 28-event seed sample does not support a simple monotonic liquidity-pull story.
Urban Company remains the clearest negative peer signal, but the broader sample does not align into a clean pressure gradient.
The current evidence is mixed and leans against a broad, mechanically repeatable pull-and-release rule.