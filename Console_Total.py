import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuration de la page
st.set_page_config(layout="wide", page_title="Global Sales Dashboard", page_icon="📊")

# Header avec logo et titre
col1, col2 = st.columns([1, 5])
with col1:
    st.image('TotalEnergies.png', width=280)
with col2:
    st.markdown("<h1 style='color: #00a083; margin-bottom: 0;'>Global Sales Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #fecd1b; margin-top: 0;'>December 2024: All Departments</h2>", unsafe_allow_html=True)

# Navigation horizontale
selected = option_menu(
    menu_title=None,
    options=["Home", "Dashboard", "Details", "Planning"],
    icons=["house", "bar-chart", "list-ul", "calendar"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f8f9fa"},
        "nav-link": {
            "font-size": "14px",
            "text-align": "center",
            "margin": "0 5px",
            "color": "#00a083",
            "border-radius": "5px",
            "padding": "8px 12px"
        },
        "nav-link-selected": {
            "background-color": "#2f5d87",
            "color": "white",
            "font-weight": "normal"
        },
        "icon": {"color": "#fecd1b", "font-size": "16px"}
    }
)

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
    df_clean['TRANSACTION_AMOUNT'] = pd.to_numeric(
        df_clean['TRANSACTION_AMOUNT'], 
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
    if selected == "Dashboard":
        st.header("Sales Analytics")
        
        # KPI Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sales", f"${df['TRANSACTION_AMOUNT'].sum():,.0f}")
        with col2:
            st.metric("Average Sale", f"${df['TRANSACTION_AMOUNT'].mean():,.2f}")
        with col3:
            st.metric("Transactions", len(df))
        
        # Visualisation
        fig = px.bar(
            df.groupby('City')['TRANSACTION_AMOUNT'].sum().reset_index(),
            x='City',
            y='TRANSACTION_AMOUNT',
            color='City',
            title="Sales by City"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif selected == "Details":
        st.header("Detailed Data View")
        
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
            TOTAL_SALES=('TRANSACTION_AMOUNT', 'sum'),
            TRANSACTION_COUNT=('TRANSACTION_AMOUNT', 'count')
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
            filtered_df.sort_values('TRANSACTION_AMOUNT', ascending=False),
            use_container_width=True,
            height=400
        )

except Exception as e:
    st.error(f"Error loading data: {str(e)}")