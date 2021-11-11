#!/usr/bin/env python
# coding: utf-8

# In[3]:


# install calmap
get_ipython().system(' pip install calmap')
get_ipython().system(' pip install lxml')


# # Importation Des library

# In[4]:


# essential libraries
import json
import random
from urllib.request import urlopen
import requests
import lxml.html as lh

# storing and analysis
import numpy as np
import pandas as pd


# visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objs as go
import plotly.figure_factory as ff
import calmap
import folium
import seaborn as sns

# offline plotly visualization
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly as py
import plotly.graph_objs as go
init_notebook_mode(connected=True) 

# color pallette
tpc = '#393e46' # confirmed - grey
dth = '#ff2e63' # death - red
rec = '#21bf73' # recovered - cyan
act = '#fe9801' # active cases - yellow
hos = '#d2691e' # hospitalized cases - brown

# converter
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()   

# hide warnings
import warnings
warnings.filterwarnings('ignore')

# gathering the geojson for Italian Regions
with urlopen('https://gist.githubusercontent.com/datajournalism-it/48e29e7c87dca7eb1d29/raw/2636aeef92ba0770a073424853f37690064eb0ea/regioni.geojson') as response:
    regions = json.load(response)

# gathering the geojson for Italian Provinces
with urlopen('https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson') as response:
    provinces = json.load(response)


# # Dataset

# # Regional Data

# # Description des variables
# 
# * SNo: Numéro de série
# 
# * Date: Date de notification au format AAAA-MM-JJTHH: MM: SS (ISO 8601)
# 
# * Country: Pays au format XYZ (ISO 3166-1 alpha-3)
# 
# * RegionCode: Code de la région (ISTAT 2019)
# 
# * RegionName: Nom de la région
# 
# * Latitude: Latitude par région
# 
# * Longitude: Longitude par région
# 
# * HospitalizedPatients: Patients hospitalisés présentant des symptômes, non en soins intensifs
# 
# * IntensiveCarePatients: Patients en soins intensifs
# 
# * TotalHospitalizedPatients: Total des patients hospitalisés (patients hospitalisés + patients en soins intensifs)
# 
# * HomeConfinement: Les personnes en quarantaine par confinement à domicile
# 
# * CurrentPositiveCases: Nombre total de cas positifs actuels (patients hospitalisés en quarantaine domestique)
# 
# * NewPositiveCases: Nouveau nombre de cas positifs actuels (HospitalizedPatients + HomeConfinement)
# 
# * Recovered: Nombre de cas récupérés
# 
# * Deaths: Nombre de décès
# 
# * TotalPositiveCases: Nombre total de cas positifs
# 
# * TestsPerformed: Nombre de tests effectués

# In[5]:


# importing datasets
Data_Byregion = pd.read_csv(r"/Users/yassinelatif/Desktop/Project.lsd/covid19_italy_region.csv", 
                         names = ['SNo','Date', 'Country', 'RegionCode', 'RegionName', 'Latitude', 'Longitude', 'HospitalizedPatients', 'IntensiveCarePatients', 'TotalHospitalizedPatients', 'HomeConfinement', 'CurrentPositiveCases', 'NewPositiveCases', 'Recovered', 'Deaths', 'TotalPositiveCases', 'TestsPerformed'], 
                         header = 0,
                         index_col = False)
Data_Byregion['Date'] = pd.to_datetime(Data_Byregion['Date'])
Data_Byregion.replace("Emilia Romagna", "Emilia-Romagna", inplace = True)
Data_Byregion.head()


# In[6]:


# dataframe info
Data_Byregion.info()


# In[7]:


# checking for missing value
Data_Byregion.isna().sum()


# In[8]:


#Scraper to create the dataframe with the population by region
url='https://www.tuttitalia.it/regioni/popolazione/'
page = requests.get(url)
doc = lh.fromstring(page.content)
tr_elements = doc.xpath('//tr')
[len(T) for T in tr_elements]

col=[]
i=0
for t in tr_elements[0]:
    i+=1
    name=t.text_content()
    col.append((name,[]))
    

for j in range(1,len(tr_elements)):
    T=tr_elements[j]
    
    if len(T)!=7:
        break
    
    i=0
    
    for t in T.iterchildren():
        data=t.text_content() 
        if i>0:
            try:
                data=int(data)
            except:
                pass
        col[i][1].append(data)
        i+=1
        
Dict = {title:column for (title,column) in col}
pop_reg = pd.DataFrame(Dict)
pop_reg = pop_reg.iloc[:,1:3]
pop_reg.columns = ['RegionName','Population']

for i in range(0, len(pop_reg['Population'])):
    pop_reg['Population'][i] = float(pop_reg['Population'][i].translate({ord('.'): None}))
pop_reg['Population'] = pop_reg['Population'].astype(float)


# # Preprocessing

# # Cleaning Data Per Region 

# In[9]:


Data_Byregion.tail()


# In[10]:


Data_Byregion.isnull()


# True càd on a une valeur manquante dans cette columns
# 
# D'aprés la commande data.insull().sum() on a la sommes des valeurs manquantes est 1155 valeurs manquantes
# 
# Remplacer les valeurs manquantes par la median

# In[11]:


median = int(Data_Byregion["TestsPerformed"].median())
Data_Byregion["TestsPerformed"].fillna(median, inplace=True)


# # Verifier column TestPerformed

# In[12]:


Data_Byregion["TestsPerformed"]


# voilà maintenant  on a remplacer les valeur manquante par la partie entiére de la médian parce que on peut pas faire un test demi c'est illogique 

# In[13]:


Data_Byregion.isnull().sum()


# In[14]:


Data_Byregion.head()


# In[15]:


# cases 
cases = ['TotalPositiveCases', 'Deaths', 'Recovered', 'Active']

# Active Case = confirmed - deaths - recovered
Data_Byregion['Active'] = Data_Byregion['TotalPositiveCases'] - Data_Byregion['Deaths'] - Data_Byregion['Recovered']


# # Regroupement des data par region

# In[16]:


# latest
data = Data_Byregion[Data_Byregion['Date'] == max(Data_Byregion['Date'])].reset_index()

# latest condensed
data_grouped = data.groupby('RegionName')['TotalPositiveCases', 'Deaths', 'Recovered', 'Active'].sum().reset_index()

#latest condensed with data about swabs (tests), quarantine and hospitalization
data_grouped_moreinfo = data.groupby('RegionName')['TotalPositiveCases', 'Deaths', 'Recovered', 'Active','TestsPerformed','HomeConfinement','HospitalizedPatients', 'IntensiveCarePatients', 'TotalHospitalizedPatients'].sum().reset_index()

#Regional visualization adjustment (Merging Trento and Bolzano into Trentino-Alto Adige)
dgm_2 = data.copy()
dgm_2.replace("P.A. Bolzano", "Trentino-Alto Adige", inplace = True)
dgm_2.replace("P.A. Trento", "Trentino-Alto Adige", inplace = True)
dgm_2 = dgm_2.groupby('RegionName')['TotalPositiveCases', 'Deaths', 'Recovered', 'Active','TestsPerformed','HomeConfinement','HospitalizedPatients', 'IntensiveCarePatients', 'TotalHospitalizedPatients'].sum().reset_index()


# # Province Data

# In[17]:


Data_Byprovince = pd.read_csv(r"/Users/yassinelatif/Desktop/Project.lsd/covid19_italy_province.csv", parse_dates=["Date"])


# # Variables Description
# 
# * SNo: Serial Number
# 
# * Date: Date of Notification in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
# 
# * Country: Country in format XYZ (ISO 3166-1 alpha-3)
# 
# * RegionCode: Code of the Region (ISTAT 2019)
# 
# * Longitude : Longitude par province
# 
# * RegionName: Name of the Region
# 
# * ProvinceCode: Code de la province (ISTAT 2019)
# 
# * ProvinceName: Nom de la province
# 
# * ProvinceAbbreviation: Province abrégée (2 lettres)
# 
# * Latitude : Latitude par province
# 
# * Longitude : Longitude par province
# 
# * TotalPositiveCases: Nombre total de cas positifs par province

# In[18]:


# importing datasets
Data_Byprovince = pd.read_csv(r"/Users/yassinelatif/Desktop/Project.lsd/covid19_italy_province.csv", parse_dates=["Date"], 
                         names = ['SNo','Date', 'Country', 'RegionCode', 'RegionName','ProvinceCode','ProvinceName','ProvinceAbbreviation', 'Latitude', 'Longitude', 'TotalPositiveCases'], 
                         header = 0,
                         index_col = False)
Data_Byprovince.head()


# In[19]:


# dataframe info
Data_Byprovince.info()


# # Cleaning Data Per Province

# In[20]:


Data_Byprovince.tail()


# In[21]:


Data_Byprovince.isnull()


# In[22]:


Data_Byprovince.isnull().sum()


# True càd on a une valeur manquante dans cette column
# 
# D'aprés la commande data.insull().sum() on a la sommes des valeurs manquantes est 16317 valeurs manquantes
# 
# Remplacer les valeurs manquantes par la median et NAN par 'ID' dans la column ProvinceAbbreviation
# 

# In[23]:


median = Data_Byprovince["Latitude"].median()
Data_Byprovince["Latitude"].fillna(median, inplace=True)


# In[24]:


median = Data_Byprovince["Longitude"].median()
Data_Byprovince["Longitude"].fillna(median, inplace=True)


# In[25]:


Data_Byprovince["ProvinceAbbreviation"].fillna("ID", inplace=True)


# In[26]:


Data_Byprovince.isnull().sum()


# In[27]:


Data_Byprovince.head()


# # Regroupement des data par Province

# In[28]:


# latest
Data_Byprovince = Data_Byprovince[Data_Byprovince['Date'] == max(Data_Byprovince['Date'])].reset_index()

# latest condensed
data_grouped_province = Data_Byprovince.groupby('ProvinceName')['TotalPositiveCases'].sum().reset_index()



# # Visualisation Des Données Par Region

# In[30]:


#Visualisation de les pays les plus touchées par COVID-19
temp = data.groupby(['RegionName'])['TotalPositiveCases', 'Deaths', 'Recovered','Active'].max()
temp.style.background_gradient(cmap='Reds')


# In[31]:


temp = data.groupby('Date')['TotalPositiveCases', 'Deaths', 'Recovered','Active'].sum().reset_index()
temp = temp[temp['Date']==max(temp['Date'])].reset_index(drop=True)
temp.style.background_gradient(cmap='Pastel1')


# In[32]:


tm = temp.melt(id_vars="Date", value_vars=['TotalPositiveCases', 'Deaths', 'Recovered','Active'])
fig = px.treemap(tm, path=["variable"], values="value", height=400, width=600,
                color_discrete_sequence=[tpc, dth, rec, act])
fig.show()


# # Region-wise Data

# # Confirmed, Deaths, Recovered  cases by Region

# In[33]:


temp_f = data_grouped.sort_values(by='TotalPositiveCases', ascending=False)
temp_f = temp_f.reset_index(drop=True)
temp_f.style.background_gradient(cmap='Reds')


# # Regions with deaths reported

# In[34]:


temp_dg = temp_f[temp_f['Deaths']>0][['RegionName', 'Deaths']]
temp_dg.sort_values('Deaths', ascending=False).reset_index(drop=True).style.background_gradient(cmap='Reds')


# # Regions with no cases reported as recovered

# In[35]:


temp = temp_f[temp_f['Recovered']==0][['RegionName', 'TotalPositiveCases', 'Deaths', 'Recovered']]
temp.reset_index(drop=True).style.background_gradient(cmap='Reds')


# On déduit qu'aucune region  n'en est affecté par Covid-19

# #  Regions with Recovered reported
# 

# In[36]:


temp_dg = temp_f[temp_f['Deaths']>0][['RegionName', 'Recovered']]
temp_dg.sort_values('Recovered', ascending=False).reset_index(drop=True).style.background_gradient(cmap='Greens')


# In[37]:


temp = data_grouped[data_grouped['TotalPositiveCases']==
                          data_grouped['Deaths']+
                          data_grouped['Recovered']]
temp = temp[['RegionName', 'TotalPositiveCases', 'Deaths', 'Recovered']]
temp = temp.sort_values('TotalPositiveCases', ascending=False)
temp = temp.reset_index(drop=True)
temp.style.background_gradient(cmap='Greens')


# * On conclue qu'ancune région  où les cas ne sont plus concernés

# ### Further data about swabs, domestic quarantine and hospitalization

# ### By Region

# In[38]:


temp_f = data_grouped_moreinfo.sort_values(by='TotalPositiveCases', ascending=False)
temp_f = temp_f.reset_index(drop=True)

temp_f.style.background_gradient(cmap='Reds')


# ### Throughout Italy

# In[39]:


temp_f = Data_Byregion.groupby('Date')['TotalPositiveCases', 'Deaths', 'Recovered', 'Active','HomeConfinement','TotalHospitalizedPatients','HospitalizedPatients', 'IntensiveCarePatients','TestsPerformed'].sum().reset_index()
temp_f = temp_f[temp_f['Date']==max(temp_f['Date'])].reset_index(drop=True)
temp_f.style.background_gradient(cmap='Pastel1')


# # Maps

# ### Across Italy - Regions

# In[40]:


# Italy_Regions

m_Regions = folium.Map(location=[41.8719, 12.5674],
               min_zoom=5, max_zoom=10, zoom_start=5)

for i in range(0, len(data)):
    folium.Circle(
        location=[data.iloc[i]['Latitude'], data.iloc[i]['Longitude']],
        color='crimson', 
        fill = True,
        fill_color='crimson',
        tooltip =   "<div style='margin: 0; background-color: black; color: white;'>"+
                    '<li><bold>Country : '+str(data.iloc[i]['Country'])+
                    '<li><bold>RegionName : '+str(data.iloc[i]['RegionName'])+
                    '<li><bold>TotalPositiveCases : '+str(data.iloc[i]['TotalPositiveCases'])+
                    '<li><bold>Deaths : '+str(data.iloc[i]['Deaths'])+
                    '<li><bold>Recovered : '+str(data.iloc[i]['Recovered'])+
                    '<li><bold>Active : '+str(data.iloc[i]['Active'])+
                    "<li>Taux de mortalite: "+ str(round((data.iloc[i]['Deaths']/data.iloc[i]['TotalPositiveCases'])*100, 2))+ "</li>"+
                    "</ul></div>",
        radius=int(data.iloc[i]['TotalPositiveCases'])**1).add_to(m_Regions)
m_Regions.save('m_Regions.html')

m_Regions


# In[41]:


#Making sure the properties from the geojson include the region name

print(data_grouped["RegionName"][0])

print(regions["features"][3]["properties"])


# In[42]:


#Total Positive Cases
fig = go.Figure(go.Choroplethmapbox(geojson=regions, locations=dgm_2['RegionName'],
                                    featureidkey="properties.NOME_REG",
                                    z=dgm_2['TotalPositiveCases'], colorscale='matter', zmin=0, zmax=max(dgm_2['TotalPositiveCases']),
                                    marker_opacity=0.8, marker_line_width=0.1))
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.update_traces(showscale=True)
fig.update_layout(title='Total Positive Cases by Region')
fig.show()


# In[43]:


# Deaths
fig = go.Figure(go.Choroplethmapbox(geojson=regions, locations=dgm_2['RegionName'],
                                    featureidkey="properties.NOME_REG",
                                    z=dgm_2['Deaths'], colorscale='amp', zmin=0, zmax=max(dgm_2['Deaths']),
                                    marker_opacity=0.8, marker_line_width=0.1))
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.update_traces(showscale=True)
fig.update_layout(title='Deaths by Region')
fig.show()


# In[201]:


formated_gdf = Data_Byregion.groupby(['Date', 'RegionName'])['Latitude','Longitude','TotalPositiveCases', 'Deaths'].max()
formated_gdf = formated_gdf.reset_index()
formated_gdf['Date'] = pd.to_datetime(formated_gdf['Date'])
formated_gdf['Date'] = formated_gdf['Date'].dt.strftime('%m/%d/%Y')
formated_gdf['size'] = formated_gdf['TotalPositiveCases'].pow(0.5)

fig = px.scatter_mapbox(formated_gdf, lat="Latitude", lon="Longitude",
                     color="TotalPositiveCases", size='size', hover_name="RegionName", hover_data=['TotalPositiveCases','Deaths'],
                     color_continuous_scale='matter',
                     range_color= [0, max(formated_gdf['TotalPositiveCases'])+2],
                     animation_frame="Date", 
                     title='Spread over time')
fig.update(layout_coloraxis_showscale=True)
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.show()


# ### Across Italy - Provinces

# Remarque: La carte ci-dessous montre uniquement les cas confirmés qui ont été attribués à une province dans l'ensemble de données et ne tient pas compte de ceux qui n'ont pas été attribués. Malheureusement, l'ensemble de données de la province ne rapporte que les cas confirmés sans autre classification.

# In[45]:


#otal Positive Cases
temp = Data_Byprovince.groupby(['ProvinceName', 'ProvinceCode'])['TotalPositiveCases'].sum().reset_index()

fig = go.Figure(go.Choroplethmapbox(geojson=provinces, locations=temp['ProvinceCode'],
                                    featureidkey="properties.prov_istat_code_num",
                                    z=temp['TotalPositiveCases'], colorscale='matter', zmin=0, zmax=max(temp['TotalPositiveCases']),
                                    text = temp['ProvinceName'],
                                    hoverinfo = 'text+z',
                                    marker_opacity=0.8, marker_line_width=0.1))
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=4, mapbox_center = {"lat": 41.8719, "lon": 12.5674})
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.update_traces(showscale=True)
fig.update_layout(title='Total Positive Cases Cases by Province')
fig.show()


# # Evolution of total cases over time

# In[92]:


temp = Data_Byregion.groupby('Date')['Deaths', 'Recovered', 'Active','TotalPositiveCases'].sum().reset_index()
temp = temp.melt(id_vars="Date", value_vars=['Deaths', 'Recovered', 'Active', 'TotalPositiveCases'],
                 var_name='Case', value_name='Count')
temp.head()

fig = px.area(temp, x="Date", y="Count", color='Case',
             title='Cases over time', color_discrete_sequence = [dth, rec, act, tpc])
fig.show()


# # Recovery, mortality and hospitalization rate over time

# Notez s'il vous plaît:
# 
# Il est très probable que les taux indiqués ci-dessous surestiment la létalité réelle du COVID-19, car le nombre réel de personnes infectées pourrait facilement être supérieur aux cas confirmés.

# In[47]:


temp = Data_Byregion.groupby('Date').sum().reset_index()

# adding two more columns
temp['No. of Deaths to 100 Confirmed Cases'] = round(temp['Deaths']/temp['TotalPositiveCases'], 3)*100
temp['No. of Recovered to 100 Confirmed Cases'] = round(temp['Recovered']/temp['TotalPositiveCases'], 3)*100
temp['No. of Hospitalized to 100 Confirmed Cases'] = round(temp['TotalHospitalizedPatients']/temp['TotalPositiveCases'], 3)*100

# temp['No. of Recovered to 1 Death Case'] = round(temp['Recovered']/temp['Deaths'], 3)

temp = temp.melt(id_vars='Date', value_vars=['No. of Deaths to 100 Confirmed Cases', 'No. of Recovered to 100 Confirmed Cases', 'No. of Hospitalized to 100 Confirmed Cases'], 
                 var_name='Ratio', value_name='Value')

fig = px.line(temp, x="Date", y="Value", color='Ratio', log_y=True, 
              title='Recovery, Mortality and Hospitalization Rate Over The Time', color_discrete_sequence=[dth, rec, hos],
              height=800)
fig.update_layout(legend_orientation='h', legend_title='')
fig.show()


# # Nombre de régions dans lesquelles le COVID-19 s'est propagé

# Remarque:
# 
# Comme mentionné précédemment, les provinces autonomes de Trente et Bolzano sont étiquetées comme des régions, de sorte que le nombre total de régions s'élève à 21.

# In[226]:


reg_spread = Data_Byregion[Data_Byregion['TotalPositiveCases']!=0].groupby('Date')['RegionName'].unique().apply(len)
reg_spread = pd.DataFrame(reg_spread).reset_index()

fig = px.line(reg_spread, x='Date', y='RegionName',
              title='Number of Italian Regions to which COVID-19 spread over the time',
             color_discrete_sequence=[tpc,dth, rec])
fig.update_traces(textposition='top center')
fig.update_layout(uniformtext_minsize=5, uniformtext_mode='hide')
fig.show()


# # La vue d'ensemble des cas par région

# In[140]:


cl = data.groupby('RegionName')['TotalPositiveCases', 'Deaths', 'Recovered'].sum()
cl = cl.reset_index().sort_values(by='TotalPositiveCases', ascending=False).reset_index(drop=True)
cl.head().style.background_gradient(cmap='rainbow')


# In[141]:


ncl = cl.copy()
ncl['Active'] = ncl['TotalPositiveCases'] - ncl['Deaths'] - ncl['Recovered']
ncl = ncl.melt(id_vars="RegionName", value_vars=['Active', 'Recovered', 'Deaths', 'TotalPositiveCases'])

fig = px.bar(ncl.sort_values(['variable', 'value']), 
             y="RegionName", x="value", color='variable', orientation='h', height=800,
             title='Number and state of Cases by Region', color_discrete_sequence=[act, dth, rec, tpc])
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.update_traces(opacity=0.6)
fig.show()


# # Top 5 des régions par catégorie

# In[50]:


dgm = data_grouped_moreinfo

dgm.head()


# In[51]:


fig = px.bar(dgm.sort_values('TotalPositiveCases', ascending=False).head(5).sort_values('TotalPositiveCases', ascending=True), 
             x="TotalPositiveCases", y="RegionName", title='Total Positive Cases', text='TotalPositiveCases', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['TotalPositiveCases'])+10000])
fig.update_traces(marker_color=tpc, opacity=0.6, textposition='outside')
fig.show()


# In[52]:


fig = px.bar(dgm.sort_values('Deaths', ascending=False).head(5).sort_values('Deaths', ascending=True), 
             x="Deaths", y="RegionName", title='Deaths', text='Deaths', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['Deaths'])+5000])
fig.update_traces(marker_color=dth, opacity=0.6, textposition='outside')
fig.show()


# In[53]:


fig = px.bar(dgm.sort_values('Recovered', ascending=False).head(5).sort_values('Recovered', ascending=True), 
             x="Recovered", y="RegionName", title='Recovered', text='Recovered', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['Recovered'])+10000])
fig.update_traces(marker_color=rec, opacity=0.6, textposition='outside')
fig.show()


# In[54]:


fig = px.bar(dgm.sort_values('Active', ascending=False).head(5).sort_values('Active', ascending=True), 
             x="Active", y="RegionName", title='Currently Active', text='Active', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['Active'])+10000])
fig.update_traces(marker_color=act, opacity=0.6, textposition='outside')
fig.show()


# In[55]:


# (Only regions with more than 500 case are considered)

dgm['Mortality Rate'] = round((dgm['Deaths']/dgm['TotalPositiveCases'])*100, 2)
temp = dgm[dgm['TotalPositiveCases']>500]
temp = temp.sort_values('Mortality Rate', ascending=False)

fig = px.bar(temp.sort_values('Mortality Rate', ascending=False).head(5).sort_values('Mortality Rate', ascending=True), 
             x="Mortality Rate", y="RegionName", text='Mortality Rate', orientation='h', 
             width=700, height=600, range_x = [0, 20], title='Mortality Rate (No. of Deaths Per 100 Confirmed Case)')
fig.update_traces(marker_color=dth, opacity=0.6, textposition='outside')
fig.show()


# In[56]:


fig = px.bar(dgm.sort_values('TotalHospitalizedPatients', ascending=False).head(5).sort_values('TotalHospitalizedPatients', ascending=True), 
             x="TotalHospitalizedPatients", y="RegionName", title='TotalHospitalizedPatients', text='TotalHospitalizedPatients', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['TotalHospitalizedPatients'])+2500])
fig.update_traces(marker_color=hos, opacity=0.6, textposition='outside')
fig.show()


# In[57]:


dgm['Hospitalization Rate'] = round((dgm['TotalHospitalizedPatients']/dgm['TotalPositiveCases'])*100, 2)
temp = dgm[dgm['TotalPositiveCases']>100]
temp = temp.sort_values('Mortality Rate', ascending=False)

fig = px.bar(temp.sort_values('Hospitalization Rate', ascending=False).head(5).sort_values('Hospitalization Rate', ascending=True), 
             x="Hospitalization Rate", y="RegionName", text='Hospitalization Rate', orientation='h', 
             width=700, height=600, range_x = [0, 100], title='Hospitalization Rate (No. of TotalHospitalizedPatients Per 100 Confirmed Case)')
fig.update_traces(marker_color=hos, opacity=0.6, textposition='outside')
fig.show()


# In[58]:


fig = px.bar(dgm.sort_values('HomeConfinement', ascending=False).head(5).sort_values('HomeConfinement', ascending=True), 
             x="HomeConfinement", y="RegionName", title='Home Confinement', text='HomeConfinement', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['HomeConfinement'])+5000])
fig.update_traces(marker_color=act, opacity=0.6, textposition='outside')
fig.show()


# In[227]:


fig = px.bar(dgm.sort_values('TestsPerformed', ascending=False).head(5).sort_values('TestsPerformed', ascending=True), 
             x="TestsPerformed", y="RegionName", title='Tests Performed (tests)', text='TestsPerformed', orientation='h', 
             width=700, height=700, range_x = [0, max(dgm['TestsPerformed'])+80000])
fig.update_traces(marker_color='purple', opacity=0.6, textposition='outside')
fig.show()


# # Les Cas par million d'habitants

# In[60]:


# merge dataframes
temp = pd.merge(dgm_2, pop_reg, how='left', right_on='RegionName', left_on='RegionName')
# print(temp[temp['Country Name'].isna()])
temp = temp[['RegionName', 'TotalPositiveCases', 'Deaths', 'Recovered', 'Active', 'Population']]
#temp.columns = ['Region', 'TotalPositiveCases', 'Deaths', 'Recovered', 'Active', 'Population']
    
# calculate TotalPositiveCases/Population
temp['TotalPositiveCases Per Million Inhabitants'] = round(temp['TotalPositiveCases']/temp['Population']*1000000, 2)

fig = px.bar(temp.head(20).sort_values('TotalPositiveCases Per Million Inhabitants', ascending=True), 
             x='TotalPositiveCases Per Million Inhabitants', y='RegionName', orientation='h', 
             width=1000, height=700, text='TotalPositiveCases Per Million Inhabitants', title='Total Positive Cases cases Per Million Inhabitants',
             range_x = [0, max(temp['TotalPositiveCases Per Million Inhabitants'])+2500])
fig.update_traces(textposition='outside', marker_color=dth, opacity=0.7)
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[61]:


temp = pd.merge(dgm_2, pop_reg, how='left', right_on='RegionName', left_on='RegionName')
# print(temp[temp['Country Name'].isna()])
temp = temp[['RegionName', 'TotalPositiveCases', 'Deaths', 'Recovered', 'Active', 'Population','IntensiveCarePatients','HospitalizedPatients','TotalHospitalizedPatients']]
#temp.columns = ['Region', 'TotalPositiveCases', 'Deaths', 'Recovered', 'Active', 'Population']
    
# calculate Hospitalized/Population
temp['Hospitalized not in ICU Per Million Inhabitants'] = round(temp['HospitalizedPatients']/temp['Population']*1000000, 2)
temp['Hospitalized in ICU Per Million Inhabitants'] = round(temp['IntensiveCarePatients']/temp['Population']*1000000, 2)
# countries with population greater that 1 million only
#temp = temp[temp['Population']>1000000].sort_values('Confirmed Per Million People', ascending=False).reset_index(drop=True)
# temp.head()


# temp['No. of Recovered to 1 Death Case'] = round(temp['Recovered']/temp['Deaths'], 3)
temp = temp.melt(id_vars='RegionName', value_vars=['Hospitalized not in ICU Per Million Inhabitants', 'Hospitalized in ICU Per Million Inhabitants'], 
                 var_name='Hospitalized cases per Million Inhabitants', value_name='Value')

fig = px.bar(temp.sort_values('Value', ascending=True),
             x="Value", y="RegionName", color='Hospitalized cases per Million Inhabitants', orientation='h', 
             title='Hospitalized Cases Per Million Inhabitants',
             color_discrete_sequence=['saddlebrown', 'sandybrown'],
             height=1000,
             text='Value',
             range_x = [0, max(temp['Value'])+500]
             )
fig.update_traces(textposition='outside', opacity=0.7)
fig.update_layout(barmode='stack')
fig.update_layout(uniformtext_minsize=11, uniformtext_mode='hide')
fig.update_layout(legend_orientation="h", legend_title='')
fig.show()


# # Day by day

# ### Throughout Italy

# In[62]:


temp = Data_Byregion.groupby('Date')['NewPositiveCases'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')

fig = px.bar(temp, x="NewPositiveCases", y="Date", orientation='h', height=800, 
             text = 'NewPositiveCases',
             title='N. of New Positive Cases in Italy for each day',
             range_x = [0, max(temp['NewPositiveCases'])+1000])
fig.update_layout(xaxis_title='Newly Positive Cases')
fig.update_traces(marker_color=act, opacity=0.6, textposition='outside')
fig.show()


# In[63]:


temp = Data_Byregion.groupby('Date')['TotalPositiveCases', 'Deaths', 'Recovered'].sum().reset_index()
#temp['Date'] = pd.to_datetime(temp['Date'])
#temp['Date'] = temp['Date'].dt.strftime('%d %b')
temp = temp.reset_index().sort_values(by='TotalPositiveCases', ascending=True).reset_index(drop=True)

ntemp = temp.copy()
ntemp['Active'] = ntemp['TotalPositiveCases'] - ntemp['Deaths'] - ntemp['Recovered']
ntemp = ntemp.melt(id_vars="Date", value_vars=['Active', 'Recovered', 'Deaths'])
ntemp['Date'] = pd.to_datetime(ntemp['Date'])
ntemp['Date'] = ntemp['Date'].dt.strftime('%d %b')

fig = px.bar(ntemp.sort_values(['variable', 'value']), 
             y="Date", x="value", color='variable', orientation='h', height=1200,
             title='Total N. of Active, Deceased and Recovered cases in Italy', color_discrete_sequence=[act, dth, rec])
fig.update_yaxes(categoryorder = "total ascending")
fig.update_layout(xaxis_title='Value')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.update_traces(opacity=0.6)
fig.show()


# # By Region

# In[64]:


temp = Data_Byregion.groupby(['RegionName', 'Date'])['TotalPositiveCases', 'Deaths', 'Recovered'].sum()
temp = temp.reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')

fig = px.bar(temp, x="TotalPositiveCases", y="Date", color='RegionName', orientation='h', height=1200,
             title='Total N. of Confirmed cases')
fig.show()


# In[66]:


temp = Data_Byregion.groupby(['RegionName', 'Date', ])['TotalPositiveCases', 'Deaths', 'Recovered']
temp = temp.sum().diff().reset_index()

mask = temp['RegionName'] != temp['RegionName'].shift(1)

temp.loc[mask, 'TotalPositiveCases'] = np.nan
temp.loc[mask, 'Deaths'] = np.nan
temp.loc[mask, 'Recovered'] = np.nan

temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')

fig = px.bar(temp, x="TotalPositiveCases", y="Date", color='RegionName', orientation='h', height = 1200,
             title='New  Positive Cases cases every day')
fig.show()


# In[67]:


temp = Data_Byregion.groupby(['RegionName', 'Date'])['TotalPositiveCases', 'Deaths', 'Recovered'].sum()
temp = temp.reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')

fig = px.bar(temp, x="Deaths", y="Date", color='RegionName', orientation='h', height=1200,
             title='Total N. of Deaths')
fig.show()


# In[211]:


temp = Data_Byregion.groupby(['RegionName', 'Date', ])['TotalPositiveCases', 'Deaths', 'Recovered']
temp = temp.sum().diff().reset_index()

mask = temp['RegionName'] != temp['RegionName'].shift(1)

temp.loc[mask, 'TotalPositiveCases'] = (np.nan)
temp.loc[mask, 'Deaths'] = (np.nan)
temp.loc[mask, 'Recovered'] = (np.nan)

temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')

fig = px.bar(temp, x="Deaths", y="Date", color='RegionName', orientation='h', height=1200,
             title='New Deaths every day')
fig.show()


# In[70]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['TotalPositiveCases'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%m/%d/%Y')
temp = temp.sort_values(by='Date')

fig = px.bar(temp, y='RegionName', x='TotalPositiveCases', color='RegionName', orientation='h',  
             title='Total Positive Cases cases over time', animation_frame='Date', height=1000, 
             range_x=[0, max(temp['TotalPositiveCases']+5000)],
             text='TotalPositiveCases')
fig.update_traces(textposition='outside')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[202]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['Deaths'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%m/%d/%Y')
temp = temp.sort_values(by='Date')

fig = px.bar(temp, y='RegionName', x='Deaths', color='RegionName', orientation='h',  
             title='Deaths Cases cases over time', animation_frame='Date', height=1000, 
             range_x=[0, max(temp['Deaths']+5000)],
             text='Deaths')
fig.update_traces(textposition='outside')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[204]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['Recovered'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%m/%d/%Y')
temp = temp.sort_values(by='Date')

fig = px.bar(temp, y='RegionName', x='Recovered', color='RegionName', orientation='h',  
             title='Recovered Cases cases over time', animation_frame='Date', height=1000, 
             range_x=[0, max(temp['Recovered']+5000)],
             text='Recovered')
fig.update_traces(textposition='outside')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[207]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['Active'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%m/%d/%Y')
temp = temp.sort_values(by='Date')

fig = px.bar(temp, y='RegionName', x='Active', color='RegionName', orientation='h',  
             title='Active cases over time', animation_frame='Date', height=1000, 
             range_x=[0, max(temp['Active']+2000)],
             text='Active')
fig.update_traces(textposition='outside')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[206]:


temp = Data_Byprovince.groupby(['Date', 'ProvinceName'])['TotalPositiveCases'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%m/%d/%Y')
temp = temp.sort_values(by='Date')

fig = px.bar(temp, y='ProvinceName', x='TotalPositiveCases', color='ProvinceName', orientation='h',  
             title='Total Positive Cases cases over time Per Province', animation_frame='Date', height=1000, 
             range_x=[0, max(temp['TotalPositiveCases']+5000)],
             text='TotalPositiveCases')
fig.update_traces(textposition='outside')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
fig.show()


# In[71]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['TotalPositiveCases'].sum().reset_index()
temp['Date'] = pd.to_datetime(temp['Date'])
temp['Date'] = temp['Date'].dt.strftime('%d %b')
px.line(temp, x="Date", y="TotalPositiveCases", color='RegionName', title='Cases Spread', height=600)


# In[72]:


temp = data_grouped
fig = px.scatter(temp, 
                 x='TotalPositiveCases', y='Deaths', color='RegionName',
                 text='RegionName', log_x=True, log_y=True, title='Deaths vs TotalPositiveCases')
fig.update_traces(textposition='top center')
fig.show()


# # Composition des Cas Per Region

# In[142]:


fig = px.treemap(data.sort_values(by='TotalPositiveCases', ascending=False).reset_index(drop=True), 
                 path=["RegionName"], values="TotalPositiveCases", height=700,
                 title='Number of Total Positive  Cases',
                 color_discrete_sequence = px.colors.qualitative.Prism)
fig.data[0].textinfo = 'label+text+value'
fig.show()

fig = px.treemap(data.sort_values(by='Deaths', ascending=False).reset_index(drop=True), 
                 path=["RegionName"], values="Deaths", height=700,
                 title='Number of Deaths reported',
                 color_discrete_sequence = px.colors.qualitative.Prism)
fig.data[0].textinfo = 'label+text+value'
fig.show()

fig = px.treemap(data.sort_values(by='Recovered', ascending=False).reset_index(drop=True), 
                 path=["RegionName"], values="Recovered", height=700,
                 title='Number of Recovered reported',
                 color_discrete_sequence = px.colors.qualitative.Prism)
fig.data[0].textinfo = 'label+text+value'
fig.show()

fig = px.treemap(data.sort_values(by='Active', ascending=False).reset_index(drop=True), 
                 path=["RegionName"], values="Active", height=700,
                 title='Number of Active reported',
                 color_discrete_sequence = px.colors.qualitative.Prism)
fig.data[0].textinfo = 'label+text+value'
fig.show()


# # Composition des Cas Per Province

# In[143]:


fig = px.treemap(data_grouped_province.sort_values(by='TotalPositiveCases', ascending=False).reset_index(drop=True), 
                 path=["ProvinceName"], values="TotalPositiveCases", height=700,
                 title='Number of Total Positive Cases reported Per Province',
                 color_discrete_sequence = px.colors.qualitative.Prism)
fig.data[0].textinfo = 'label+text+value'
fig.show()


# # Durée de l'épidémie

# Remarque: 
# 
# Dans le graphique, le dernier jour est indiqué comme un jour après la dernière notification d'un nouveau cas confirmé.

# In[75]:


# first date
# ----------
first_date = Data_Byregion[Data_Byregion['TotalPositiveCases']>0]
# converting Date to datetime
first_date['Date'] = pd.to_datetime(first_date['Date'])
first_date = first_date.groupby('RegionName')['Date'].agg(['min']).reset_index()
# first_date.head()

from datetime import timedelta  

# last date
# ---------
last_date = Data_Byregion
# converting Date to datetime
last_date['Date'] = pd.to_datetime(last_date['Date'])
last_date = Data_Byregion.groupby(['RegionName', 'Date', ])['TotalPositiveCases', 'Deaths', 'Recovered']
last_date = last_date.sum().diff().reset_index()

mask = last_date['RegionName'] != last_date['RegionName'].shift(1)
last_date.loc[mask, 'TotalPositiveCases'] = np.nan
last_date.loc[mask, 'Deaths'] = np.nan
last_date.loc[mask, 'Recovered'] = np.nan

last_date = last_date[last_date['TotalPositiveCases']>0]
last_date = last_date.groupby('RegionName')['Date'].agg(['max']).reset_index()
# last_date.head()

# first_last
# ----------
first_last = pd.concat([first_date, last_date[['max']]], axis=1)

# added 1 more day, which will show the next day as the day on which last case appeared
first_last['max'] = first_last['max'] + timedelta(days=1)

# no. of days
first_last['Days'] = first_last['max'] - first_last['min']

# task column as country
first_last['Task'] = first_last['RegionName']

# rename columns
first_last.columns = ['RegionName', 'Start', 'Finish', 'Days', 'Task']

# sort by no. of days
first_last = first_last.sort_values('Days')
# first_last.head()

# visualization
# --------------

# produce random colors
clr = ["#"+''.join([random.choice('0123456789ABC') for j in range(6)]) for i in range(len(first_last))]

#plot
fig = ff.create_gantt(first_last, index_col='RegionName', colors=clr, show_colorbar=False, 
                      bar_width=0.2, showgrid_x=True, showgrid_y=True, height=500, 
                      title=('Gantt Chart'))
fig.show()


# # Region Wise

# ### Confirmed cases

# In[76]:


temp = Data_Byregion.groupby(['Date', 'RegionName'])['TotalPositiveCases'].sum()
temp = temp.reset_index().sort_values(by=['Date', 'RegionName'])

plt.style.use('seaborn')
g = sns.FacetGrid(temp, col="RegionName", hue="RegionName", 
                  sharey=False, col_wrap=4)
g = g.map(plt.plot, "Date", "TotalPositiveCases")
g.set_xticklabels(rotation=90)
plt.show()


# ### Ln(TotalPositiveCases)

# In[77]:


temp = Data_Byregion.copy()

temp['LnTotalPositiveCases'] = np.log(temp['TotalPositiveCases'])
temp = temp.groupby(['Date', 'RegionName'])['LnTotalPositiveCases'].sum()
temp = temp.reset_index().sort_values(by=['Date', 'RegionName'])


plt.style.use('seaborn')
g = sns.FacetGrid(temp, col="RegionName", hue="RegionName", 
                  sharey=False, col_wrap=4)
g = g.map(plt.plot, "Date", "LnTotalPositiveCases")
g.set_xticklabels(rotation=90)
plt.show()


# ### New Positive Cases

# In[91]:


temp = Data_Byregion.groupby(['RegionName', 'Date', ])['TotalPositiveCases', 'Deaths', 'Recovered']
temp = temp.sum().diff().reset_index()

mask = temp['RegionName'] != temp['RegionName'].shift(1)

temp.loc[mask, 'TotalPositiveCases'] = np.nan
temp.loc[mask, 'Deaths'] = np.nan
temp.loc[mask, 'Recovered'] = np.nan

plt.style.use('seaborn')
g = sns.FacetGrid(temp, col="RegionName", hue="RegionName", 
                  sharey=False, col_wrap=4)
g = g.map(sns.lineplot, "Date", "TotalPositiveCases")
g.set_xticklabels(rotation=90)
plt.show()


# # Calendar map

# In[79]:


Data_Byregion['Date'] = pd.to_datetime(Data_Byregion['Date'])


# ### Nombre de nouveaux cas confirmés chaque jour

# In[80]:


temp = Data_Byregion.groupby('Date')['TotalPositiveCases'].sum()
temp = temp.diff()

plt.figure(figsize=(20, 5))
ax = calmap.yearplot(temp, fillcolor='white', cmap='Oranges', linewidth=0.5)


# ### Nombre de nouveaux décès chaque jour

# In[81]:


temp = Data_Byregion.groupby('Date')['Deaths'].sum()
temp = temp.diff()

plt.figure(figsize=(20, 5))
ax = calmap.yearplot(temp, fillcolor='white', cmap='Reds', linewidth=0.5)


# ### Nombre de régions nouvellement touchées chaque jour

# In[82]:


spread = Data_Byregion[Data_Byregion['TotalPositiveCases']!=0].groupby('Date')
spread = spread['RegionName'].unique().apply(len).diff()

plt.figure(figsize=(20, 5))
ax = calmap.yearplot(spread, fillcolor='white', cmap='Greens', linewidth=0.5)


# In[83]:


# Italy_Province

m_province = folium.Map(location=[41.8719, 12.5674],
               min_zoom=5, max_zoom=10, zoom_start=5)

for i in range(0, len(Data_Byprovince)):
    folium.Circle(
        location=[Data_Byprovince.iloc[i]['Latitude'], Data_Byprovince.iloc[i]['Longitude']],
        color='crimson', 
        fill = True,
        fill_color='crimson',
        tooltip =   "<div style='margin: 0; background-color: black; color: white;'>"+
                    '<li><bold>Country : '+str(Data_Byprovince.iloc[i]['Country'])+
                    '<li><bold>RegionName : '+str(Data_Byprovince.iloc[i]['RegionName'])+
                    '<li><bold>ProvinceName : '+str(Data_Byprovince.iloc[i]['ProvinceName'])+
                    '<li><bold>TotalPositiveCases : '+str(Data_Byprovince.iloc[i]['TotalPositiveCases']),
                radius=int(Data_Byprovince.iloc[i]['TotalPositiveCases'])**1).add_to(m_province)
m_province.save('m_province.html')

m_province


# In[84]:


plt.figure(figsize=(10,5), dpi=100)

plt.style.use('default')

Lazio = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lazio"]['TotalPositiveCases']

Veneto = Data_Byregion.loc[Data_Byregion['RegionName'] == "Veneto"]['TotalPositiveCases']

Lombardia = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lombardia"]['TotalPositiveCases']

bp = plt.boxplot([Lazio, Veneto, Lombardia], labels=['Lazio', 'Veneto', "Lombardia"], patch_artist=True)

plt.title('Total Positive Cases Region Comparison')
plt.ylabel('Total Positive Cases Per Region')
plt.xlabel('Region Name')

for box in bp['boxes']:
    #Set edge color:
    box.set(color='#4286f4', linewidth=2)
    # Change Fill Color:
    box.set(facecolor = '#e0e0e0')
    
    

plt.show()


# In[85]:


plt.figure(figsize=(10,5), dpi=100)

plt.style.use('default')

Lazio = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lazio"]['Recovered']

Veneto = Data_Byregion.loc[Data_Byregion['RegionName'] == "Veneto"]['Recovered']

Lombardia = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lombardia"]['Recovered']

bp = plt.boxplot([Lazio, Veneto, Lombardia], labels=['Lazio', 'Veneto', "Lombardia"], patch_artist=True)

plt.title('Recovered Cases Region Comparison')
plt.ylabel('Recovered Per Region')
plt.xlabel('Region Name')

for box in bp['boxes']:
    #Set edge color:
    box.set(color='#4286f4', linewidth=2)
    # Change Fill Color:
    box.set(facecolor = '#e0e0e0')
    
    

plt.show()


# In[86]:


plt.figure(figsize=(10,5), dpi=100)

plt.style.use('default')

Lazio = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lazio"]['Deaths']

Veneto = Data_Byregion.loc[Data_Byregion['RegionName'] == "Veneto"]['Deaths']

Lombardia = Data_Byregion.loc[Data_Byregion['RegionName'] == "Lombardia"]['Deaths']

bp = plt.boxplot([Lazio, Veneto, Lombardia], labels=['Lazio', 'Veneto', "Lombardia"], patch_artist=True)

plt.title('Deaths Cases Region Comparison')
plt.ylabel('Deaths Cases Per Region')
plt.xlabel('Region Name')

for box in bp['boxes']:
    #Set edge color:
    box.set(color='#4286f4', linewidth=2)
    # Change Fill Color:
    box.set(facecolor = '#e0e0e0')
    
    

plt.show()


# In[175]:


np.random.seed(19680801)

plt.rcdefaults()
fig, ax = plt.subplots()

# Importation Des Données
Region = data['RegionName']
error = np.random.rand(len(Region))
TotalPositiveCases = data['TotalPositiveCases']


ax.barh(Region, TotalPositiveCases, xerr=error, align='center', color='b')
ax.set_yticks(Region)
ax.set_yticklabels(Region)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('TotalPositiveCases')
ax.set_ylabel('Name of Region ')
ax.set_title('Distrubition Total Positive Cases By Region')

plt.show()


# In[176]:


np.random.seed(19680801)

plt.rcdefaults()
fig, ax = plt.subplots()

# Importation Des Données
Region = data['RegionName']
error = np.random.rand(len(Region))
Deaths = data['Deaths']


ax.barh(Region, Deaths, xerr=error, align='center', color='Red')
ax.set_yticks(Region)
ax.set_yticklabels(Region)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Deaths')
ax.set_ylabel('Name of Region ')
ax.set_title('Distrubition Deaths By Region')

plt.show()


# In[178]:


np.random.seed(19680801)

plt.rcdefaults()
fig, ax = plt.subplots()

# Importation Des Données
Region = data['RegionName']
error = np.random.rand(len(Region))
Recovered = data['Recovered']


ax.barh(Region, Recovered, xerr=error, align='center', color='Green')
ax.set_yticks(Region)
ax.set_yticklabels(Region)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Recovered')
ax.set_ylabel('Name of Region ')
ax.set_title('Distribution Recovered By Region')

plt.show()


# In[180]:


np.random.seed(19680801)

plt.rcdefaults()
fig, ax = plt.subplots()

# Importation Des Données
Region = data['RegionName']
error = np.random.rand(len(Region))
Active = data['Active']


ax.barh(Region, Active, xerr=error, align='center', color='Orange')
ax.set_yticks(Region)
ax.set_yticklabels(Region)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Active')
ax.set_ylabel('Name of Region ')
ax.set_title('Distribution Active By Region')

plt.show()


# In[160]:


sns.barplot(x=Data_Byregion['RegionName'], y=Data_Byregion['TotalPositiveCases'])
plt.xticks(rotation=90, ha='right')
plt.title('Total Positive Cases By Region')
plt.rc('figure', figsize=(10, 5))


# In[161]:


sns.barplot(x=Data_Byregion['RegionName'], y=Data_Byregion['Deaths'])
plt.xticks(rotation=90, ha='right')
plt.title('Number The Deaths By Region')
plt.rc('figure', figsize=(10, 5))


# In[162]:


sns.barplot(x=Data_Byregion['RegionName'], y=Data_Byregion['Recovered'])
plt.xticks(rotation=90, ha='right')
plt.title('Number The Recovred By Region')
plt.rc('figure', figsize=(10, 5))


# In[164]:


#Province Bar Plot
sns.barplot(x=Data_Byprovince['ProvinceName'], y=Data_Byprovince['TotalPositiveCases'])
plt.xticks(rotation=90, size=80, ha='right')
plt.yticks(size=80, ha='right')



plt.title('Total Positive Cases By Province',size=80)
plt.ylabel('Total Positive Cases', size=80)
xlabel=plt.xlabel('Name Of Province', size=80)


plt.rc('figure', figsize=(160,80))


# # Créeation De La Base des Données

# In[165]:


import sqlite3

conn = sqlite3.connect('Projet_Lsd_Covid_19.db')

c = conn.cursor()


# # Connexion de la table by region avec la base des données

# In[166]:


Data_Byregion.to_sql('Covid_19_in_italy_Byregion', conn, schema=None, if_exists='fail', index=True, index_label=None, chunksize=None, dtype=None, method=None)


# # Connexion de la table by province avec la base des données

# In[167]:


Data_Byprovince.to_sql('Covid_19_in_italy_Byprovince', conn,schema=None, if_exists='fail', index=True, index_label=None, chunksize=None, dtype=None, method=None)


# # Pies Visualisation

# ### Per Region

# In[168]:


#Distribution of Total Positive Cases Per Region
fig = px.pie(data, values=data['TotalPositiveCases'], names=data['RegionName'],
            title='Distribution of Total Positive Cases Per Region',
            )
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    template='plotly_white')
plt.rc('figure', figsize=(160,80))
fig.show()


# In[169]:


#Distribution of Deaths Per Region
fig = px.pie(data, values=data['Deaths'], names=data['RegionName'],
            title='Distribution of Deaths Per Region',
            )
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    template='plotly_white')
fig.show()


# In[170]:


#Distribution of Recovered Per Region
fig = px.pie(data, values=data['Recovered'], names=data['RegionName'],
            title='Distribution of Recovered Per Region',
            )
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    template='plotly_white')
fig.show()


# In[33]:


#Distribution of Active Per Region
fig = px.pie(data, values=data['Active'], names=data['RegionName'],
            title='Distribution of Active Per Region',
            )
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    template='plotly_white')
fig.show()


# ### Per Province

# In[172]:


#Distribution of Total Positive Cases Per Province
fig = px.pie(data_grouped_province, values=data_grouped_province['TotalPositiveCases'], names=data_grouped_province['ProvinceName'],
            title='Distribution of Total Positive Cases Per Province',
            )
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(
    template='plotly_white')
fig.show()


# # Scatter Plots

# ### Per Region

# In[189]:


fig = px.scatter(data, x=data['RegionName'], y=data['TotalPositiveCases'], size=data['TotalPositiveCases'],
                color=data['RegionName'], hover_name=data['RegionName'], size_max=60)

fig.update_layout()
fig.show()


# In[190]:


fig = px.scatter(data, x=data['RegionName'], y=data['Deaths'], size=data['Deaths'],
                color=data['RegionName'], hover_name=data['RegionName'], size_max=60)

fig.update_layout()
fig.show()


# In[197]:


fig = px.scatter(data, x=data['RegionName'], y=data['Recovered'], size=data['Recovered'],
                color=data['RegionName'], hover_name=data['RegionName'], size_max=60 
                     )

fig.update_layout()
fig.show()


# In[192]:


fig = px.scatter(data, x=data['RegionName'], y=data['Active'], size=data['Active'],
                color=data['RegionName'], hover_name=data['RegionName'], size_max=60)

fig.update_layout()
fig.show()


# ### Per Province

# In[195]:


fig = px.scatter(data_grouped_province, x=data_grouped_province['ProvinceName'], y=data_grouped_province['TotalPositiveCases'], size=data_grouped_province['TotalPositiveCases'],
                color=data_grouped_province['ProvinceName'], hover_name=data_grouped_province['ProvinceName'], size_max=60)

fig.update_layout()
fig.show()


# # Conclusion

# * Les premiers cas de coronavirus à propagation terrestre en Italie sont apparus dans les régions du nord de la Lombardie, de la Vénétie et de l'Émilie-Romagne le 20 février
# 
# * La collecte des données a commencé le 24 février
# 
# * Le 8 mars 2020, le Premier ministre Giuseppe Conte a étendu la quarantaine à toute la Lombardie et à 14 autres provinces du nord, et le lendemain à toute l'Italie, plaçant plus de 60 millions de personnes en quarantaine.
# 
# * Le 11 mars 2020, PM Conte a interdit la quasi-totalité des activités commerciales à l'exception des supermarchés et des pharmacies.
# 
# * Le 16 mars 2020, l'Italie est devenue le centre mondial des cas actifs de coronavirus avec deux fois plus de cas actifs de tout autre pays, y compris la Chine et l'Iran, combinés à 20603 cas actifs. Les USA ont pris le relais quelques semaines plus tard, le 11 avril.
# 
# * Au 8 mai 2020, l'Italie comptait 87 961 cas actifs, l'un des nombres les plus élevés au monde. Dans l'ensemble, il y a eu 217 185 cas confirmés et 30 201 décès (un taux de mortalité d'environ 500 par million d'habitants), tandis qu'il y a eu 99 023 récupérations ou licenciements.
# 
# * Le 8 mai, l'Italie avait testé environ 1 610 000 personnes.

# # Étude Statistique

# * Pour connaitre le nombre de cas à la date maximale l'erreur serait de faire la somme de la colonne Confirmed, car il s'agit d'une donnée cumulée chaque jour !
# * Il faut donc extraire les données à la date souhaitée et de réaliser ensuite les différents calculs
# 
# * On extrait les données à la derniere date la plus récente

# In[212]:


dataDerniereDate = Data_Byregion[Data_Byregion['Date'] == max(Data_Byregion['Date'])].reset_index()


# In[213]:


TotalPositiveCases = dataDerniereDate["TotalPositiveCases"].sum()
TotalPositiveCases


# In[214]:


Recovered = dataDerniereDate["Recovered"].sum()
Recovered


# In[215]:


Deaths = dataDerniereDate["Deaths"].sum()
Deaths


# # les statistiques de toute l'Italie :
# 
# 
# 

# In[216]:


print("  Confirmes : "+str(TotalPositiveCases))
print("  Gueris : "+str(Recovered))
print("  Decedes : "+str(Deaths))
print("  Taux mortalité (%): "+str(round((Deaths/TotalPositiveCases)*100,2)))

#Pour utilisation dans la synthèse
confirmes = TotalPositiveCases
gueris = Recovered
decedes = Deaths
mortalite = round((Deaths/TotalPositiveCases)*100,2)


# In[217]:


#Déterminer les caractéristiques de la variable des guérisons "Recovered":
#la moyenne :
print("la moyenne est : ",data["Recovered"].mean())
#la variance :
print("la variance est :",data["Recovered"].var())
#l'écart type :
print("lécart type est :",data["Recovered"].std())
#le Min,Max et la somme :
print("le minimum de la série est : ",min(data["Recovered"]))
print("le maximum de la série est : ",max(data["Recovered"]))
print("la somme des éléments de la série est :",sum(data["Recovered"]))
#la médiane :
print("la médiane est :",data["Recovered"].median())


# In[218]:


#Déterminer les caractéristiques de la variable des décès "Deaths":
#la moyenne :
print("la moyenne est : ",data["Deaths"].mean())
#la variance :
print("la variance est :",data["Deaths"].var())
#l'écart type :
print("lécart type est :",data["Deaths"].std())
#le Min,Max et la somme :
print("le minimum de la série est : ",min(data["Deaths"]))
print("le maximum de la série est : ",max(data["Deaths"]))
print("la somme des éléments de la série est :",sum(data["Deaths"]))
#la médiane :
print("la médiane est :",data["Deaths"].median())


# In[219]:


#Déterminer les caractéristiques de la variable du Total des cas positifs "TotalPositiveCases":
#la moyenne :
print("la moyenne est : ",data["TotalPositiveCases"].mean())
#la variance :
print("la variance est :",data["TotalPositiveCases"].var())
#l'écart type :
print("lécart type est :",data["TotalPositiveCases"].std())
#le Min,Max et la somme :
print("le minimum de la série est : ",min(data["TotalPositiveCases"]))
print("le maximum de la série est : ",max(data["TotalPositiveCases"]))
print("la somme des éléments de la série est :",sum(data["TotalPositiveCases"]))
#la médiane :
print("la médiane est :",np.median(data["TotalPositiveCases"]))


# # Description De La Table By Region

# In[39]:


data_grouped.describe()


# * Dans cette description, nous allons faire une étude bivariée concernant les deux variables : "Total Positive Cases" et "Tests Performed"; Mettons la variable 'TestsPerformed' variable dépendante et la variable 'TotalPositiveCases' comme variable explicative.

# In[29]:


#calcul du matrice de covariance
x = list(data["TotalPositiveCases"])
y = list(data["Recovered"])
np.cov(x,y)


# In[30]:


#Pour le coefficient de corrélation
np.corrcoef(x,y)


# * la donnée qui nous intéresse est donc en haut à droite et/ou en bas à gauche
# * Plus le coefficient est proche de 1, la relation linéaire positive entre les variables est forte.

# * Pour les coefficients de la droite des moindres carrés, on va utiliser la fonction linregress de scipy.stats.
# * Elleprend en arguments les deux listes de données X et Y et renvoie 5 nombres réels. Seuls les 3 premiers nous
# * intéressent : le premier est le coefficient directeur de la droite, le deuxième est l’ordonnée à l’origine et le troisième
# 
# 

# In[35]:


#le coefficient de corrélation :
from scipy.stats import linregress
linregress(x,y)


# In[36]:


plt.plot(x,y,'b*') #nuage de points


# In[225]:


data.to_csv('Data_Grouped.csv')




