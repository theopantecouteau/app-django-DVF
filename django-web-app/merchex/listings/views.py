# ~/projects/django-web-app/merchex/listings/views.py

import pandas as pd
import plotly.express as px
from django.http import JsonResponse
from django.shortcuts import render
from .forms import NameForm
from fuzzywuzzy import process, fuzz
import plotly.graph_objects as go
import json
import folium

dtypes = {'No disposition': 'Int64', 'Code postal': str, 'Code commune': str, 'Prefixe de section': str,
                      'Section': str, 'No plan': str}
low_memory = False
df = pd.read_csv('data_cleaned_2022.csv', header=0, dtype=dtypes, low_memory=low_memory)
df2 = pd.read_csv('data_cleaned_2021.csv', header=0, dtype=dtypes, low_memory=low_memory)
df3 = pd.read_csv('data_cleaned_2020.csv', header=0, dtype=dtypes, low_memory=low_memory)
df4 = pd.read_csv('data_cleaned_2019.csv', header=0, dtype=dtypes, low_memory=low_memory)
df5 = pd.read_csv('data_cleaned_2018.csv', header=0, dtype=dtypes, low_memory=low_memory)
df['Date mutation'] = pd.to_datetime(df['Date mutation'], format='%Y-%m-%d')
df2['Date mutation'] = pd.to_datetime(df2['Date mutation'], format='%Y-%m-%d')
df3['Date mutation'] = pd.to_datetime(df3['Date mutation'], format='%Y-%m-%d')
df4['Date mutation'] = pd.to_datetime(df4['Date mutation'], format='%Y-%m-%d')
df5['Date mutation'] = pd.to_datetime(df5['Date mutation'], format='%Y-%m-%d')

def get_name(request, df=df, df2=df2, df3=df3, df4=df4, df5=df5):
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            error = ""
            # Récupérer la valeur du formulaire
            fname = form.cleaned_data['fname']
            data_type = 'Code postal' if fname.isdigit() else 'Commune'
            print(fname)
            print(len(fname))
            if data_type == 'Code postal':
                if len(fname) == 2:
                    data_type = 'Code departement'
                elif len(fname) != 5:
                    error = "Veuillez entrer un code postal (5 chiffres) ou une code département (2 chiffres) ou une ville valide"
                    return render(request, 'index.html',
                                  {'error': error, 'form': form})
            else:
                if data_type != 'Commune':
                    error = "Veuillez entrer un code postal (5 chiffres) ou une code département (2 chiffres) ou une ville valide"
                    return render(request, 'index.html',
                                  {'error': error, 'form': form})


            result = process.extractOne(fname, df[data_type], scorer=fuzz.token_sort_ratio)
            matched_value = result[0] if result is not None else None
            if matched_value is None:
                error = "Veuillez entrer un code postal (5 chiffres) ou une code département (2 chiffres) ou une ville valide"
                return render(request, 'index.html',
                              {'error': error, 'form': form})

            # Filtrer les données en utilisant la valeur correspondante
            filtered_df = df[df[data_type] == matched_value]
            filtered_df2 = df2[df2[data_type] == matched_value]
            filtered_df3 = df3[df3[data_type] == matched_value]
            filtered_df4 = df4[df4[data_type] == matched_value]
            filtered_df5 = df5[df5[data_type] == matched_value]



            df = filtered_df['Type local'].value_counts()
            # Créer un graphique avec Plotly
            fig = px.pie(df, values=df.values, names=df.index, title=f'Type de logement à {matched_value}')

            df = filtered_df['Date mutation'].dt.to_period('M').value_counts()
            df = df.to_frame(name='Nombre de ventes')
            df.index = df.index.astype('str').sort_values()
            fig2 = px.line(df, x=df.index, y='Nombre de ventes',
                          title=f'Nombre de ventes par mois en 2022 à {matched_value}')

            prix_moyen_appartement = round(filtered_df[filtered_df['Type local'] == 'Appartement']['Valeur fonciere'].mean())
            prix_moyen_maison = round(filtered_df[filtered_df['Type local'] == 'Maison']['Valeur fonciere'].mean())
            prix_moyen_dependance = round(filtered_df[filtered_df['Type local'] == 'Dépendance']['Valeur fonciere'].mean())
            prix_moyen_local_industriel = round(filtered_df[filtered_df['Type local'] == 'Local industriel. commercial ou assimilé']['Valeur fonciere'].mean())
            prix_moyen_m = round(filtered_df['Prix au m²'].mean())

            nombre_vente_2022, _ = filtered_df.shape
            nombre_vente_2021, _ = filtered_df2.shape
            nombre_vente_2020, _ = filtered_df3.shape
            nombre_vente_2019, _ = filtered_df4.shape
            nombre_vente_2018, _ = filtered_df5.shape

            data_year = {'Annee': ['2018', '2019', '2020', '2021', '2022'], 'Nombre de ventes': [nombre_vente_2018, nombre_vente_2019, nombre_vente_2020, nombre_vente_2021, nombre_vente_2022]}
            df_year = pd.DataFrame(data_year)
            fig3 = px.line(df_year, x='Annee', y='Nombre de ventes', title=f'Evolution du nombre de ventes par année à {matched_value}')

            prix_moyen_2022 = round(filtered_df['Valeur fonciere'].mean())
            prix_moyen_2021 = round(filtered_df2['Valeur fonciere'].mean())
            prix_moyen_2020 = round(filtered_df3['Valeur fonciere'].mean())
            prix_moyen_2019 = round(filtered_df4['Valeur fonciere'].mean())
            prix_moyen_2018 = round(filtered_df5['Valeur fonciere'].mean())
            data_price_year = {'Annee': ['2018', '2019', '2020', '2021', '2022'], 'Prix moyen': [prix_moyen_2018, prix_moyen_2019, prix_moyen_2020, prix_moyen_2021, prix_moyen_2022]}
            df_price_year = pd.DataFrame(data_price_year)
            fig4 = px.line(df_price_year, x='Annee', y='Prix moyen', title=f'Evolution du prix moyen par année à {matched_value}')

            geo_data = json.load(open('departements.geojson'))
            data_map = filtered_df.groupby('Code departement')['Valeur fonciere'].mean().reset_index()
            # Define bins
            bins = list(data_map['Valeur fonciere'].quantile([0, 0.2, 0.4, 0.6, 0.8, 1]))
            m = folium.Map(location=[45.8566, 2.3522], zoom_start=6)
            # Add the color for the chloropleth:
            folium.Choropleth(
                geo_data=geo_data,
                name='choropleth',
                data=data_map,
                columns=['Code departement', 'Valeur fonciere'],
                key_on='feature.properties.code',
                fill_color='BuPu',
                fill_opacity=0.7,
                line_opacity=0.8,
                legend_name='Localisation en France',
                bins=bins,
                nan_fill_color='#ffffff'
            ).add_to(m)

            graph_html_map = m.get_root().render()

            graph_html = '<div id="graph-container">{}</div>'.format(fig.to_html(include_plotlyjs='cdn'))
            graph_html += '<div id="graph-container2">{}</div>'.format(fig2.to_html(include_plotlyjs='cdn'))
            graph_html += '<div id="graph-container3">{}</div>'.format(fig3.to_html(include_plotlyjs='cdn'))
            graph_html += '<div id="graph-container4">{}</div>'.format(fig4.to_html(include_plotlyjs='cdn'))

            return render(request, 'index.html',
                          {'form': form, 'graph_html': graph_html, 'prix_moyen_appartement': prix_moyen_appartement,
                           'prix_moyen_maison': prix_moyen_maison, 'prix_moyen_dependance': prix_moyen_dependance,
                           'prix_moyen_local_industriel': prix_moyen_local_industriel, 'prix_moyen_m': prix_moyen_m, 'graph_html_map': graph_html_map})

    else:
        form = NameForm()

    return render(request, 'index.html', {'form': form})

