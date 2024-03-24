# -*- coding: utf-8 -*-
"""Homophily-Dissimilarity.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1141aQCDIV5mPOCRF_1ZFAUiLy8z7R7Bc
"""

import pandas as pd
import requests
import numpy as np

lang_tract = pd.read_csv("/content/drive/MyDrive/H08-ResilienceIndex/data/homophily/raw/lang-S1601-2020-tract.csv")
lang_cnty = pd.read_csv("/content/drive/MyDrive/H08-ResilienceIndex/data/homophily/raw/lang-S1601-2020-county.csv")
race_tract = pd.read_csv("/content/drive/MyDrive/H08-ResilienceIndex/data/homophily/raw/race-B03002-2020-tract.csv")
race_cnty = pd.read_csv("/content/drive/MyDrive/H08-ResilienceIndex/data/homophily/raw/race-B03002-2020-county.csv")

county_df = pd.merge(race_cnty, lang_cnty, on=["GEO_ID", "year"])
county_df["Pr_AAPI"] = county_df["Pr_Asian"] + county_df["Pr_Hawaiian"]
county_df.drop(columns=["GEO_ID", "state", "county", "Pr_Asian", "Pr_Hawaiian", "Pr_Otherrace", "Pr_Multirace"], inplace=True)
column_order = ["fips", "NAME", "year"] + [col for col in county_df.columns if col not in ["fips", "NAME", "year"]]
county_df = county_df.reindex(columns=column_order)
county_df["fips"] = county_df["fips"].astype(str).str.zfill(5)
county_df["NonHispanic_County"] = county_df["Population"] - county_df["Hispanic"]
county_df.rename(columns={"fips": "CountyFIPS",
                          'NAME': "CountyName",
                          'Population': "Pop_County",
                          'Pr_White': "Pr_White_County",
                          'Pr_Black': 'Pr_Black_County',
                          'Pr_AAPI': 'Pr_AAPI_County',
                          'Pr_Native': 'Pr_Native_County',
                          'Pr_Hispanic': 'Pr_Hispanic_County',
                          'Pr_EnglishAtHome': 'Pr_EnglishAtHome_County',
                          'Pr_SpanishAtHome': 'Pr_SpanishAtHome_County',
                          'Pr_IndoEuropeanAtHome': 'Pr_IndoEuropeanAtHome_County',
                          'Pr_AsianLanguageAtHome': 'Pr_AsianLanguageAtHome_County',
                          'Pr_EngLessThanWell': 'Pr_EngLessThanWell_County',
                          'Hispanic': 'Hispanic_County'
                          }, inplace=True)

county_df.dtypes

tract_df = pd.merge(race_tract, lang_tract, on=["GEO_ID", "year"])
tract_df.drop(columns=["GEO_ID"], inplace=True)

for column in tract_df.columns:
  if column.startswith("Pr_"):
      tract_df[column] = tract_df[column].fillna(0)

tract_df['state'] = tract_df['state'].astype(str).str.zfill(2)
tract_df['county'] = tract_df['county'].astype(str).str.zfill(3)
tract_df["CountyFIPS"] = tract_df['state'] + tract_df['county']
tract_df["NonHispanic"] = tract_df["Population"] - tract_df["Hispanic"]
tract_df.drop(columns=["state", "county"], inplace=True)

tract_df.dtypes

merged_df = pd.merge(tract_df, county_df, on=["CountyFIPS", "year"], how="left")
merged_df

merged_df.columns

df = merged_df.copy()

df["Dissimilarity_Hispanic"] = ((df["Hispanic"]/df["Hispanic_County"]) - (df["NonHispanic"]/df["NonHispanic_County"])).abs()

df["HHI_Race"] = df["Pr_White"]**2 + df["Pr_Black"]**2 + df["Pr_Native"]**2 + df["Pr_Asian"]**2 + df["Pr_Hispanic"]**2
df["HHI_Lang"] = df["Pr_EnglishAtHome"]**2 + df["Pr_SpanishAtHome"]**2 + df["Pr_IndoEuropeanAtHome"]**2 + df["Pr_AsianLanguageAtHome"]**2

df

# Calculate weighted homogeneity index at county level
df['Weighted_HHI_Race'] = df["HHI_Race"] * df['Population']

# Group by county and calculate the sum of weighted homogeneity and total population
race_homophily = df.groupby('CountyFIPS').agg({'Weighted_HHI_Race': 'sum'})

# Reset index to make 'county' a regular column
race_homophily.reset_index(inplace=True)

race_homophily

# Calculate weighted homogeneity index at county level
df['Weighted_HHI_Lang'] = df["HHI_Lang"] * df['Population']

# Group by county and calculate the sum of weighted homogeneity and total population
language_homophily = df.groupby('CountyFIPS').agg({'Weighted_HHI_Lang': 'sum'})

# Reset index to make 'county' a regular column
language_homophily.reset_index(inplace=True)

language_homophily

# Group by county and calculate the sum of weighted homogeneity and total population
hispanic_dissimilarity = df.groupby('CountyFIPS').agg({'Dissimilarity_Hispanic': 'sum'})

# Reset index to make 'county' a regular column
hispanic_dissimilarity.reset_index(inplace=True)

# Divided by 2 to normalize the index between 0 and 1, with higher values indicating greater dissimilarity between the groups across the areas.

hispanic_dissimilarity["Dissimilarity_Hispanic"] = hispanic_dissimilarity["Dissimilarity_Hispanic"] * 0.5

hispanic_dissimilarity

hispanic_dissimilarity.Dissimilarity_Hispanic.describe()

from functools import reduce

frames = [race_homophily, language_homophily, hispanic_dissimilarity]
homophily = reduce(lambda left, right: pd.merge(left, right, on=['CountyFIPS'], how='inner'), frames)
homophily

homophily.to_csv("homophily.csv", index=False)