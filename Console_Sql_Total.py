import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from contextlib import closing
from PIL import Image

# Configuration de la page Streamlit
st.set_page_config(
    layout="wide",
    page_title="Global Sales Dashboard",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Connexion à SQL Server
def get_db_connection():
    server = 'DESKTOP-2D5TJUA'
    database = 'Total_Stat'
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

# Authentification
def authenticate(username, password):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "SELECT u.Hyp, e.Type, e.Date_In FROM Users u "
                "JOIN Effectifs e ON u.Hyp = e.Hyp "
                "WHERE u.UserName = ? AND u.PassWord = ?", 
                (username, password))
            result = cursor.fetchone()
            return result if result else None
    except Exception as e:
        st.error(f"Erreur d'authentification : {e}")
        return None
    finally:
        conn.close()

# Page de connexion
def login_page():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image('TotalEnergies.png', width=400)
    with col2:
        st.markdown("<h2 style='color:#00a083;'>Connexion</h2>", unsafe_allow_html=True)
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter"):
            user_data = authenticate(username, password)
            if user_data:
                st.session_state.update({
                    "authenticated": True,
                    "hyp": user_data[0],
                    "user_type": user_data[1],
                    "date_in": user_data[2],
                    "username": username
                })
                st.success("Authentification réussie")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

@st.cache_data
def load_data():
    """Chargement des données depuis SQL Server."""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame(), pd.DataFrame()

        with closing(conn.cursor()) as cursor:
            # Chargement des données Sales
            cursor.execute("""
                SELECT Hyp, ORDER_REFERENCE, ORDER_DATE, SHORT_MESSAGE, Country, City, Total_sale, Rating, Id_Sale 
                FROM Sales""")
            sales_df = pd.DataFrame.from_records(cursor.fetchall(), 
                                               columns=[column[0] for column in cursor.description])

            # Chargement des données Staff
            cursor.execute("""
                SELECT Hyp, Team, Activité, Date_In 
                FROM Effectifs""")
            staff_df = pd.DataFrame.from_records(cursor.fetchall(),
                                               columns=[column[0] for column in cursor.description])

        return sales_df, staff_df
    except Exception as e:
        st.error(f"Erreur de chargement des données: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        if conn:
            conn.close()

@st.cache_data
def preprocess_data(df):
    """Prétraitement des données."""
    if 'ORDER_DATE' in df.columns:
        df['ORDER_DATE'] = pd.to_datetime(df['ORDER_DATE'], errors='coerce')
    if 'Total_sale' in df.columns:
        df['Total_sale'] = pd.to_numeric(df['Total_sale'], errors='coerce').fillna(0)
    
    if 'Date_In' in df.columns:
        df['Date_In'] = pd.to_datetime(df['Date_In'], errors='coerce')
    return df

def filter_data(df, country_filter, team_filter, activity_filter, start_date, end_date, staff_df, current_hyp=None):
    """Appliquer les filtres aux données en utilisant Hyp comme clé."""
    filtered_df = df.copy()
    
    if current_hyp:
        return filtered_df[filtered_df['Hyp'] == current_hyp]
    
    if 'ORDER_DATE' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['ORDER_DATE'] >= pd.to_datetime(start_date)) & 
            (filtered_df['ORDER_DATE'] <= pd.to_datetime(end_date))
        ]
    
    if country_filter != 'Tous' and 'Country' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Country'] == country_filter]
    
    if 'Hyp' in filtered_df.columns and not staff_df.empty:
        staff_filtered = staff_df.copy()
        
        if team_filter != 'Toutes':
            staff_filtered = staff_filtered[staff_filtered['Team'] == team_filter]
        if activity_filter != 'Toutes':
            staff_filtered = staff_filtered[staff_filtered['Activité'] == activity_filter]
        
        filtered_df = filtered_df[filtered_df['Hyp'].isin(staff_filtered['Hyp'])]

    return filtered_df

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
                locations.append({
                    'City': row['City'], 
                    'Country': row['Country'],
                    'Latitude': location.latitude,
                    'Longitude': location.longitude
                })
        except:
            continue
    
    if locations:
        locations_df = pd.DataFrame(locations)
        df = pd.merge(df, locations_df, on=['City', 'Country'], how='left')
    return df

def manager_dashboard():
    sales_df, staff_df = load_data()
    sales_df = preprocess_data(sales_df)
    staff_df = preprocess_data(staff_df)

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
        
        with st.expander("Période", expanded=True):
            min_date = sales_df['ORDER_DATE'].min() if not sales_df.empty else datetime.now()
            max_date = sales_df['ORDER_DATE'].max() if not sales_df.empty else datetime.now()
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Date début", min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("Date fin", max_date, min_value=min_date, max_value=max_date)

    if selected == "Sales":
        st.header("Vue Détailée des Données Sales")
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            country_sales_filter = st.selectbox("Filtrer par Pays (Sales)", ['Tous'] + sorted(sales_df['Country'].dropna().unique()))
        
        with col2:
            selected_team = st.selectbox("Sélectionner équipe", ['Toutes'] + sorted(staff_df['Team'].dropna().unique()))
        
        with col3:
            selected_activity = st.selectbox("Sélectionner activité", ['Toutes'] + sorted(staff_df['Activité'].dropna().unique()))
        
        filtered_sales = filter_data(sales_df, country_sales_filter, selected_team, selected_activity, start_date, end_date, staff_df)
        st.dataframe(filtered_sales)

    elif selected == "Tableau de bord":
        st.header("Analyse Commerciale - Sales")
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            country_sales_filter = st.selectbox("Filtrer par Pays (Sales)", ['Tous'] + sorted(sales_df['Country'].dropna().unique()))
        
        with col2:
            selected_team = st.selectbox("Sélectionner équipe", ['Toutes'] + sorted(staff_df['Team'].dropna().unique()))
        
        with col3:
            selected_activity = st.selectbox("Sélectionner activité", ['Toutes'] + sorted(staff_df['Activité'].dropna().unique()))
            
        filtered_sales = filter_data(sales_df, country_sales_filter, selected_team, selected_activity, start_date, end_date, staff_df)
        
        if not filtered_sales.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Ventes Totales", f"${filtered_sales['Total_sale'].sum():,.2f}")
            col2.metric("Vente Moyenne", f"${filtered_sales['Total_sale'].mean():,.2f}")
            col3.metric("Nombre de Transactions", len(filtered_sales))
            
            sales_by_city = filtered_sales.groupby('City')['Total_sale'].sum().reset_index()
            fig = px.bar(sales_by_city, x='City', y='Total_sale', color='City', title="Ventes par Ville")
            st.plotly_chart(fig, use_container_width=True)
            
            if not staff_df.empty and 'Hyp' in filtered_sales.columns:
                sales_with_team = filtered_sales.merge(staff_df[['Hyp', 'Team']], on='Hyp', how='left')
                sales_by_team = sales_with_team.groupby('Team')['Total_sale'].sum().reset_index()
                fig = px.pie(sales_by_team, names='Team', values='Total_sale', title="Répartition des ventes par équipe")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Aucune donnée à afficher pour les ventes.")
        
    elif selected == "Planning":
        st.header("Planification")
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image('TotalEnergies.png', width=280)
        with col2:
            st.markdown("<h1 style='color: #00a083; margin-bottom: 0;'>Global Sales Dashboard</h1>", unsafe_allow_html=True)
            st.markdown("<h2 style='color: #fecd1b; margin-top: 0;'>December 2024: All Teams</h2>", unsafe_allow_html=True)

        st.header("Sales Analytics")
            
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sales", f"${sales_df['Total_sale'].sum():,.0f}")
        with col2:
            st.metric("Average Sale", f"${sales_df['Total_sale'].mean():,.2f}")
        with col3:
            st.metric("Transactions", len(sales_df))
            
        fig = px.bar(
            sales_df.groupby('City')['Total_sale'].sum().reset_index(),
            x='City',
            y='Total_sale',
            color='City',
            title="Sales by City"
        )
        st.plotly_chart(fig, use_container_width=True)
            
        if 'Latitude' not in sales_df.columns or 'Longitude' not in sales_df.columns:
            with st.spinner("Geocoding cities... This may take a while for large datasets"):
                sales_df = geocode_data(sales_df)
            
        countries = sorted(sales_df['Country'].unique())
        selected_country = st.selectbox("Select Country", countries)
        filtered_df = sales_df[sales_df['Country'] == selected_country]
            
        city_data = filtered_df.groupby(['City', 'Latitude', 'Longitude']).agg(
            TOTAL_SALES=('Total_sale', 'sum'),
            TRANSACTION_COUNT=('Total_sale', 'count')
        ).reset_index().dropna()
            
        if not city_data.empty:
            st.subheader(f"Sales Map - {selected_country}")
            
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
                mapbox_style="open-street-map"
            )
            
            fig.update_layout(
                height=600,
                margin={"r":0,"t":40,"l":0,"b":0},
                coloraxis_colorbar={
                    "title": "Sales Amount",
                    "tickprefix": "$"
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
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
            
        st.subheader("Detailed Sales Data")
        st.dataframe(
            filtered_df.sort_values('Total_sale', ascending=False),
            use_container_width=True,
            height=400
        )

        if not staff_df.empty:
            fig = px.bar(staff_df.groupby('Team').size().reset_index(name='Count'),
                         x='Team', y='Count', color='Team',
                         title="Répartition des effectifs par équipe")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

def agent_dashboard():
    st.title(f"Bienvenue {st.session_state['username']}")
    st.info(f"Votre date d'entrée : {st.session_state['date_in'].strftime('%d/%m/%Y')}")
    st.write("Vous avez un accès limité à l'application.")

    sales_df, staff_df = load_data()
    sales_df = preprocess_data(sales_df)
    agent_sales = filter_data(sales_df, None, None, None, None, None, staff_df, st.session_state['hyp'])
    
    st.header("Vos Performances")
    
    if not agent_sales.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Ventes Totales", f"${agent_sales['Total_sale'].sum():,.2f}")
        col2.metric("Vente Moyenne", f"${agent_sales['Total_sale'].mean():,.2f}")
        col3.metric("Nombre de Transactions", len(agent_sales))
        
        sales_by_date = agent_sales.groupby(agent_sales['ORDER_DATE'].dt.date)['Total_sale'].sum().reset_index()
        fig = px.line(sales_by_date, x='ORDER_DATE', y='Total_sale', title="Vos ventes par date")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée de vente disponible")

# Gestion de l'état de connexion
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    if st.session_state["user_type"] in ["Manager", "Hyperviseur"]:
        manager_dashboard()
    else:
        agent_dashboard()
else:
    login_page()