import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuration de la page Streamlit
st.set_page_config(
    layout="wide",
    page_title="Global Sales Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    """Chargement des données Excel."""
    try:
        # Charger les données avec les colonnes correctes
        sales_df = pd.read_excel(
            'Sources.xlsm',
            sheet_name='Sales',
            usecols=['Hyp', 'ORDER_REFERENCE', 'ORDER_DATE', 'SHORT_MESSAGE', 'Country', 'City', 'Montant', 'Rating'],
            header=0
        )
        recolt_df = pd.read_excel(
            'Sources.xlsm',
            sheet_name='Recolt',
            usecols=['Hyp', 'Banques', 'TRANSACTION', 'ORDER_REFERENCE', 'ORDER_DATE', 'SHORT_MESSAGE', 'City', 'Country'],
            header=0
        )
        staff_df = pd.read_excel(
            'Sources.xlsm',
            sheet_name='Effectif',
            usecols=['ID', 'Hyp', 'ID_AGTSDA', 'UserName', 'NOM', 'PRENOM', 'Team', 'Type', 'Activité', 'Departement', 'Date_In'],
            header=0
        ).drop_duplicates()
        
        return sales_df, recolt_df, staff_df
    except Exception as e:
        st.error(f"Erreur de chargement des fichiers Excel : {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data
def preprocess_data(df):
    """Prétraitement des données."""
    if 'ORDER_DATE' in df.columns:
        df['ORDER_DATE'] = pd.to_datetime(df['ORDER_DATE'], errors='coerce')
    if 'Montant' in df.columns:
        df['Montant'] = pd.to_numeric(df['Montant'], errors='coerce').fillna(0)
    if 'TRANSACTION' in df.columns:
        df['TRANSACTION'] = pd.to_numeric(df['TRANSACTION'], errors='coerce').fillna(0)
    if 'Date_In' in df.columns:
        df['Date_In'] = pd.to_datetime(df['Date_In'], errors='coerce')
    return df

# Chargement et prétraitement des données
sales_df, recolt_df, staff_df = load_data()
sales_df = preprocess_data(sales_df)
recolt_df = preprocess_data(recolt_df)
staff_df = preprocess_data(staff_df)

# Barre latérale : Menu de navigation
with st.sidebar:
    st.image('TotalEnergies.png', width=200)
    st.markdown("<h1 style='text-align: center; color: #00a083;'>Menu</h1>", unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["Tableau de bord", "Sales", "Recolt", "Planning"],
        icons=["bar-chart", "currency-dollar", "list-ul", "calendar"],
        default_index=0
    )
    
    st.markdown("---")
    st.markdown("<h2 style='font-size: 16px; color: #00a083;'>Filtres de Dates</h2>", unsafe_allow_html=True)
    
    # Filtres de dates globaux
    with st.expander("Période", expanded=True):
        min_date = min(
            sales_df['ORDER_DATE'].min() if not sales_df.empty else datetime.now(),
            recolt_df['ORDER_DATE'].min() if not recolt_df.empty else datetime.now()
        )
        max_date = max(
            sales_df['ORDER_DATE'].max() if not sales_df.empty else datetime.now(),
            recolt_df['ORDER_DATE'].max() if not recolt_df.empty else datetime.now()
        )
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Date début", min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("Date fin", max_date, min_value=min_date, max_value=max_date)

# Defining the filter function
def filter_data(df, country_filter, team_filter, department_filter, activity_filter, start_date, end_date):
    """Appliquer les filtres aux données en utilisant Hyp comme clé."""
    filtered_df = df.copy()
    
    # Filtrer par date si la colonne existe
    if 'ORDER_DATE' in filtered_df.columns:
        filtered_df = filtered_df[ 
            (filtered_df['ORDER_DATE'] >= pd.to_datetime(start_date)) & 
            (filtered_df['ORDER_DATE'] <= pd.to_datetime(end_date))
        ]
    
    # Filtrer par pays si la colonne existe
    if country_filter != 'Tous' and 'Country' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Country'] == country_filter]
    
    # Pour les filtres d'équipe, département et activité, nous devons joindre avec staff_df via Hyp
    if 'Hyp' in filtered_df.columns and not staff_df.empty:
        # Créer un sous-ensemble de staff_df basé sur les filtres
        staff_filtered = staff_df.copy()
        
        if team_filter != 'Toutes':
            staff_filtered = staff_filtered[staff_filtered['Team'] == team_filter]
        if department_filter != 'Tous':
            staff_filtered = staff_filtered[staff_filtered['Departement'] == department_filter]
        if activity_filter != 'Toutes':
            staff_filtered = staff_filtered[staff_filtered['Activité'] == activity_filter]
        
        # Filtrer le dataframe principal en gardant seulement les Hyp qui correspondent
        filtered_df = filtered_df[filtered_df['Hyp'].isin(staff_filtered['Hyp'])]

    return filtered_df

# Contenu dynamique par page
if selected == "Sales":
    st.header("Vue Détailée des Données Sales")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        country_sales_filter = st.selectbox("Filtrer par Pays (Sales)", ['Tous'] + sorted(sales_df['Country'].dropna().unique()))
    
    with col2:
        selected_team = st.selectbox("Sélectionner équipe", ['Toutes'] + sorted(staff_df['Team'].dropna().unique()))
    
    with col3:
        selected_department = st.selectbox("Sélectionner département", ['Tous'] + sorted(staff_df['Departement'].dropna().unique()))
    
    with col4:
        selected_activity = st.selectbox("Sélectionner activité", ['Toutes'] + sorted(staff_df['Activité'].dropna().unique()))
    
    filtered_sales = filter_data(sales_df, country_sales_filter, selected_team, selected_department, selected_activity, start_date, end_date)
    st.dataframe(filtered_sales)

elif selected == "Recolt":
    st.header("Vue Détailée des Données Recolt")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        country_recolt_filter = st.selectbox("Filtrer par Pays (Recolt)", ['Tous'] + sorted(recolt_df['Country'].dropna().unique()))
    
    with col2:
        selected_team = st.selectbox("Sélectionner équipe", ['Toutes'] + sorted(staff_df['Team'].dropna().unique()))
    
    with col3:
        selected_department = st.selectbox("Sélectionner département", ['Tous'] + sorted(staff_df['Departement'].dropna().unique()))
    
    with col4:
        selected_activity = st.selectbox("Sélectionner activité", ['Toutes'] + sorted(staff_df['Activité'].dropna().unique()))
    
    filtered_recolt = filter_data(recolt_df, country_recolt_filter, selected_team, selected_department, selected_activity, start_date, end_date)

    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(filtered_recolt)
    with col2:
        # Ajouter des visualisations ou autres éléments pour la deuxième colonne
        pass

elif selected == "Tableau de bord":
    st.header("Analyse Commerciale - Sales")
    country_recolt_filter = st.selectbox("Filtrer par Pays (Recolt)", ['Tous'] + sorted(recolt_df['Country'].dropna().unique()))
    
    
    selected_team = st.selectbox("Sélectionner équipe", ['Toutes'] + sorted(staff_df['Team'].dropna().unique()))
    
 
    selected_department = st.selectbox("Sélectionner département", ['Tous'] + sorted(staff_df['Departement'].dropna().unique()))
    
 
    selected_activity = st.selectbox("Sélectionner activité", ['Toutes'] + sorted(staff_df['Activité'].dropna().unique()))
    
    country_sales_filter = st.selectbox("Filtrer par Pays (Sales)", ['Tous'] + sorted(sales_df['Country'].dropna().unique()))
    filtered_sales = filter_data(sales_df, country_sales_filter, selected_team, selected_department, selected_activity, start_date, end_date)
    
    if not filtered_sales.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Ventes Totales", f"${filtered_sales['Montant'].sum():,.2f}")
        col2.metric("Vente Moyenne", f"${filtered_sales['Montant'].mean():,.2f}")
        col3.metric("Nombre de Transactions", len(filtered_sales))
        
        # Ventes par ville
        sales_by_city = filtered_sales.groupby('City')['Montant'].sum().reset_index()
        fig = px.bar(sales_by_city, x='City', y='Montant', color='City', title="Ventes par Ville")
        st.plotly_chart(fig, use_container_width=True)
        
        # Ventes par équipe (via Hyp -> staff_df)
        if not staff_df.empty and 'Hyp' in filtered_sales.columns:
            sales_with_team = filtered_sales.merge(staff_df[['Hyp', 'Team']], on='Hyp', how='left')
            sales_by_team = sales_with_team.groupby('Team')['Montant'].sum().reset_index()
            fig = px.pie(sales_by_team, names='Team', values='Montant', title="Répartition des ventes par équipe")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher pour les ventes.")
    
    st.header("Analyse Commerciale - Recolt")
    country_recolt_filter = st.selectbox("Filtrer par Pays (Recolt)", ['Tous'] + sorted(recolt_df['Country'].dropna().unique()))
    filtered_recolt = filter_data(recolt_df, country_recolt_filter, selected_team, selected_department, selected_activity, start_date, end_date)
    
    if not filtered_recolt.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Montant Total", f"${filtered_recolt['TRANSACTION'].sum():,.2f}")
        col2.metric("Montant Moyen", f"${filtered_recolt['TRANSACTION'].mean():,.2f}")
        col3.metric("Nombre de Transactions", len(filtered_recolt))
        
        # Transactions par ville
        recolt_by_city = filtered_recolt.groupby('City')['TRANSACTION'].sum().reset_index()
        fig = px.bar(recolt_by_city, x='City', y='TRANSACTION', color='City', title="Montants par Ville")
        st.plotly_chart(fig, use_container_width=True)
        
        # Transactions par banque
        recolt_by_bank = filtered_recolt.groupby('Banques')['TRANSACTION'].sum().reset_index()
        fig = px.pie(recolt_by_bank, names='Banques', values='TRANSACTION', title="Répartition par banque")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher pour les montants.")

elif selected == "Planning":
    st.header("Planification")
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image('TotalEnergies.png', width=280)
    with col2:
        st.markdown("<h1 style='color: #00a083; margin-bottom: 0;'>Global Sales Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #fecd1b; margin-top: 0;'>December 2024: All Departments</h2>", unsafe_allow_html=True)

    # Navigation horizontale
    
# Chargement des données
@st.cache_data
def load_data():
    excel_file = 'Sources.xlsm'
    sheet_name = 'Recolt'
    
    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        usecols='A:H',
        header=0,
        index_col=None
    )
    
    # Nettoyage des données
    df_clean = df.dropna().copy()
    df_clean['TRANSACTION'] = pd.to_numeric(
        df_clean['TRANSACTION'], 
        errors='coerce'
    ).fillna(0)
    
    return df_clean.reset_index(drop=True)

# Fonction pour géocoder les villes
@st.cache_data
def geocode_data(df):
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        return df
    
    geolocator = Nominatim(user_agent="sales_dashboard")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    cities = df[['City', 'Country']].drop_duplicates()
    locations = []
    
    for _, row in cities.iterrows():
        try:
            location = geocode(f"{row['City']}, {row['Country']}")
            if location:
                locations.append({'City': row['City'], 
                                'Country': row['Country'],
                                'Latitude': location.latitude,
                                'Longitude': location.longitude})
            else:
                locations.append({'City': row['City'], 
                                'Country': row['Country'],
                                'Latitude': None,
                                'Longitude': None})
        except:
            locations.append({'City': row['City'], 
                            'Country': row['Country'],
                            'Latitude': None,
                            'Longitude': None})
    
    locations_df = pd.DataFrame(locations)
    df = pd.merge(df, locations_df, on=['City', 'Country'], how='left')
    return df

try:
    df = load_data()
    
    # Section Dashboard
    
    st.header("Sales Analytics")
        
        # KPI Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
            st.metric("Total Sales", f"${df['TRANSACTION'].sum():,.0f}")
           
    with col2:
            st.metric("Average Sale", f"${df['TRANSACTION'].mean():,.2f}")
    with col3:
            st.metric("Transactions", len(df))
        
        # Visualisation
    fig = px.bar(
            df.groupby('City')['TRANSACTION'].sum().reset_index(),
            x='City',
            y='TRANSACTION',
            color='City',
            title="Sales by City"
        )
    st.plotly_chart(fig, use_container_width=True)
        
  
        
        # Géocodage des villes si nécessaire
    if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
            with st.spinner("Geocoding cities... This may take a while for large datasets"):
                df = geocode_data(df)
        
        # Filtre par pays
    countries = sorted(df['Country'].unique())
    selected_country = st.selectbox("Select Country", countries)
    filtered_df = df[df['Country'] == selected_country]
        
        # Préparation des données pour la carte
    city_data = filtered_df.groupby(['City', 'Latitude', 'Longitude']).agg(
            TOTAL_SALES=('TRANSACTION', 'sum'),
            TRANSACTION_COUNT=('TRANSACTION', 'count')
        ).reset_index().dropna()
        
    if not city_data.empty:
            # Section Carte
            st.subheader(f"Sales Map - {selected_country}")
            
            # Création de la carte avec Plotly
            fig = px.scatter_mapbox(
                city_data,
                lat="Latitude",
                lon="Longitude",
                size="TOTAL_SALES",
                color="TOTAL_SALES",
                hover_name="City",
                hover_data={
                    "TOTAL_SALES": ":$.2f",
                    "TRANSACTION_COUNT": True,
                    "Latitude": False,
                    "Longitude": False
                },
                zoom=5,
                center={
                    "lat": city_data['Latitude'].mean(),
                    "lon": city_data['Longitude'].mean()
                },
                title=f"Sales Distribution in {selected_country}",
                size_max=30,
                color_continuous_scale=px.colors.sequential.Viridis,
                mapbox_style="open-street-map"  # Utilisez "carto-positron" pour un style plus simple
            )
            
            # Personnalisation de la mise en page
            fig.update_layout(
                height=600,
                margin={"r":0,"t":40,"l":0,"b":0},
                coloraxis_colorbar={
                    "title": "Sales Amount",
                    "tickprefix": "$"
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Graphique supplémentaire
            st.subheader("Top Cities by Sales")
            top_cities = city_data.sort_values('TOTAL_SALES', ascending=False).head(10)
            fig_bar = px.bar(
                top_cities,
                x='City',
                y='TOTAL_SALES',
                color='TOTAL_SALES',
                labels={'TOTAL_SALES': 'Total Sales ($)'},
                text_auto='.2s'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
            st.warning("No geographic data available for the selected country")
        
        # Tableau de données détaillées
    st.subheader("Detailed Transaction Data")
    st.dataframe(
            filtered_df.sort_values('TRANSACTION', ascending=False),
            use_container_width=True,
            height=400
        )

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    
    # Visualisation des effectifs par département
    if not staff_filtered.empty:
        fig = px.bar(staff_filtered.groupby('Departement').size().reset_index(name='Count'),
                     x='Departement', y='Count', color='Departement',
                     title="Répartition des effectifs par département")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
