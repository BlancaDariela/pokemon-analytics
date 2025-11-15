import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Pokémon Analytics",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF0000;
        text-align: center;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B4CCA;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    connection_string = "mongodb+srv://admin:TU_PASSWORD@cluster0.zqozcwk.mongodb.net/"
    client = pymongo.MongoClient(connection_string)
    return client["pokemon_nube"]["pokemon"]

@st.cache_data
def load_data():
    collection = get_database()
    data = list(collection.find())
    df = pd.DataFrame(data)
    
    if 'Sp' in df.columns and isinstance(df['Sp'].iloc[0], dict):
        df['Sp_Atk'] = df['Sp'].apply(lambda x: x.get('Atk', 0) if isinstance(x, dict) else 0)
        df['Sp_Def'] = df['Sp'].apply(lambda x: x.get('Def', 0) if isinstance(x, dict) else 0)
    
    return df

try:
    df = load_data()
    st.success(f"✅ Conectado exitosamente! {len(df)} pokémon cargados.")
except Exception as e:
    st.error(f"❌ Error al conectar: {e}")
    st.stop()

st.markdown('<h1 class="main-header">⚡ POKÉMON ANALYTICS ⚡</h1>', unsafe_allow_html=True)
st.markdown("---")

st.sidebar.header("🎮 Filtros")

generaciones = sorted(df['Generation'].unique())
gen_seleccionada = st.sidebar.multiselect(
    "Generación:",
    options=generaciones,
    default=generaciones
)

tipos = sorted(df['Type 1'].unique())
tipo_seleccionado = st.sidebar.multiselect(
    "Tipo Principal:",
    options=tipos,
    default=tipos
)

mostrar_legendarios = st.sidebar.checkbox("Solo Legendarios", value=False)

df_filtrado = df.copy()
if gen_seleccionada:
    df_filtrado = df_filtrado[df_filtrado['Generation'].isin(gen_seleccionada)]
if tipo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['Type 1'].isin(tipo_seleccionado)]
if mostrar_legendarios:
    df_filtrado = df_filtrado[df_filtrado['Legendary'] == True]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Pokémon mostrados: **{len(df_filtrado)}**")

st.markdown('<h2 class="sub-header">📊 Estadísticas Generales</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Pokémon",
        value=len(df_filtrado),
        delta=f"{len(df_filtrado) - len(df)} desde total"
    )

with col2:
    legendarios = len(df_filtrado[df_filtrado['Legendary'] == True])
    st.metric(
        label="⭐ Legendarios",
        value=legendarios,
        delta=f"{(legendarios/len(df_filtrado)*100):.1f}%"
    )

with col3:
    avg_total = df_filtrado['Total'].mean()
    st.metric(
        label="💪 Total Promedio",
        value=f"{avg_total:.0f}",
        delta=f"{avg_total - df['Total'].mean():.0f}"
    )

with col4:
    tipos_unicos = df_filtrado['Type 1'].nunique()
    st.metric(
        label="🎨 Tipos Únicos",
        value=tipos_unicos
    )

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Análisis General", "💪 Top Pokémon", "🎨 Por Tipo", "🔍 Búsqueda"])

with tab1:
    st.markdown('<h2 class="sub-header">📈 Análisis de Estadísticas</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.histogram(
            df_filtrado,
            x='Total',
            nbins=30,
            title='Distribución del Total de Estadísticas',
            color_discrete_sequence=['#FF6B6B']
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        gen_counts = df_filtrado['Generation'].value_counts().sort_index()
        fig2 = px.bar(
            x=gen_counts.index,
            y=gen_counts.values,
            title='Pokémon por Generación',
            labels={'x': 'Generación', 'y': 'Cantidad'},
            color_discrete_sequence=['#4ECDC4']
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("### ⚔️ Estadísticas Promedio")
    
    stat_cols = ['HP', 'Attack', 'Defense', 'Speed']
    if 'Sp_Atk' in df_filtrado.columns:
        stat_cols.extend(['Sp_Atk', 'Sp_Def'])
    
    stats_promedio = df_filtrado[stat_cols].mean()
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatterpolar(
        r=stats_promedio.values,
        theta=stats_promedio.index,
        fill='toself',
        name='Promedio'
    ))
    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.markdown('<h2 class="sub-header">💪 Top Pokémon Más Fuertes</h2>', unsafe_allow_html=True)
    
    top_n = st.slider("Selecciona cantidad:", min_value=5, max_value=50, value=10, step=5)
    
    top_pokemon = df_filtrado.nlargest(top_n, 'Total')[['Name', 'Type 1', 'Type 2', 'Total', 'HP', 'Attack', 'Defense', 'Legendary']]
    
    fig4 = px.bar(
        top_pokemon,
        x='Name',
        y='Total',
        color='Type 1',
        title=f'Top {top_n} Pokémon Más Fuertes',
        hover_data=['Type 2', 'HP', 'Attack', 'Defense']
    )
    fig4.update_layout(xaxis_tickangle=-45, height=500)
    st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("### 📋 Tabla Detallada")
    st.dataframe(
        top_pokemon.reset_index(drop=True),
        use_container_width=True,
        height=400
    )

with tab3:
    st.markdown('<h2 class="sub-header">🎨 Análisis por Tipo de Pokémon</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_counts = df_filtrado['Type 1'].value_counts()
        fig5 = px.pie(
            values=tipo_counts.values,
            names=tipo_counts.index,
            title='Distribución por Tipo Principal',
            hole=0.4
        )
        fig5.update_layout(height=500)
        st.plotly_chart(fig5, use_container_width=True)
    
    with col2:
        tipo_avg = df_filtrado.groupby('Type 1')['Total'].mean().sort_values(ascending=False)
        fig6 = px.bar(
            x=tipo_avg.index,
            y=tipo_avg.values,
            title='Total Promedio por Tipo',
            labels={'x': 'Tipo', 'y': 'Total Promedio'},
            color=tipo_avg.values,
            color_continuous_scale='Viridis'
        )
        fig6.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig6, use_container_width=True)
    
    st.markdown("### 📊 Estadísticas Detalladas por Tipo")
    tipo_stats = df_filtrado.groupby('Type 1')[['HP', 'Attack', 'Defense', 'Speed', 'Total']].mean().round(2)
    tipo_stats['Cantidad'] = df_filtrado.groupby('Type 1').size()
    tipo_stats = tipo_stats.sort_values('Total', ascending=False)
    st.dataframe(tipo_stats, use_container_width=True)

with tab4:
    st.markdown('<h2 class="sub-header">🔍 Buscar Pokémon Específico</h2>', unsafe_allow_html=True)
    
    nombre_busqueda = st.text_input("Escribe el nombre del Pokémon:", "")
    
    if nombre_busqueda:
        pokemon_encontrado = df[df['Name'].str.contains(nombre_busqueda, case=False, na=False)]
        
        if len(pokemon_encontrado) > 0:
            st.success(f"✅ Se encontraron {len(pokemon_encontrado)} resultado(s)")
            
            for idx, pokemon in pokemon_encontrado.iterrows():
                with st.expander(f"⚡ {pokemon['Name']}", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**Número:** #{pokemon['#']}")
                        st.markdown(f"**Tipo 1:** {pokemon['Type 1']}")
                        st.markdown(f"**Tipo 2:** {pokemon.get('Type 2', 'N/A')}")
                        st.markdown(f"**Generación:** {pokemon['Generation']}")
                        st.markdown(f"**Legendario:** {'⭐ Sí' if pokemon['Legendary'] else '❌ No'}")
                        st.markdown(f"**Total:** {pokemon['Total']}")
                    
                    with col2:
                        stats = [pokemon['HP'], pokemon['Attack'], pokemon['Defense'], pokemon['Speed']]
                        categories = ['HP', 'Attack', 'Defense', 'Speed']
                        
                        if 'Sp_Atk' in pokemon:
                            stats.extend([pokemon['Sp_Atk'], pokemon['Sp_Def']])
                            categories.extend(['Sp. Atk', 'Sp. Def'])
                        
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=stats,
                            theta=categories,
                            fill='toself',
                            name=pokemon['Name']
                        ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 200])),
                            showlegend=False,
                            height=300
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("⚠️ No se encontró ningún Pokémon con ese nombre")
    else:
        st.info("💡 Escribe el nombre de un Pokémon para ver sus detalles")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚡ Pokémon Analytics Dashboard | Datos almacenados en MongoDB Atlas ☁️</p>
    <p>Proyecto de Cómputo en la Nube | 2024</p>
</div>
""", unsafe_allow_html=True)
