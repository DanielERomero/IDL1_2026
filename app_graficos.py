import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from supabase import create_client, Client
import os


# Configuración de página
st.set_page_config(page_title="Visor de Ventas", layout="wide")
st.title('Visor de ventas - Tienda de conveniencia')

# Definir columnas necesarias globalmente para evitar errores
columnas_necesarias = {'producto', 'turno', 'tienda', 'venta_total'}

# Conexión a Supabase 
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error de configuración de secretos: {e}")
        return None

supabase = init_connection()


# obtener los datos desde Supabase
@st.cache_data(ttl=600) # Cache por 10 minutos
def obtener_datos():
    if not supabase:
        return []
    try:
        # Ajusta el nombre de la tabla si es necesario
        response = supabase.table('IDL1_2026').select('*').execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener los datos: {e}")
        return []

# Obtener los datos desde Supabase
data = obtener_datos()
if data:
    df = pd.DataFrame(data)
    st.subheader('Vista de Datos desde Supabase')
    st.dataframe(df)

    
    # Validación
    if not columnas_necesarias.issubset(df.columns):
        st.error('El archivo debe contener las columnas: ' + str(columnas_necesarias))
        st.write(f"Columnas encontradas: {df.columns.tolist()}")
    else:
        df['venta_total'] = pd.to_numeric(df['venta_total'], errors='coerce')
        # KPIs generales
        total_ventas = df['venta_total'].sum()
        ventas_promedio = df['venta_total'].mean()

        # KPIs visuales con colores
        st.markdown("""
        <style>
        .metric {
            background-color: #f0f0f5;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            font-size: 20px;
            color: black;
        }
        .kpi-container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric" style="background-color: #007bff;">Total Ventas: ${total_ventas:,.2f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric" style="background-color: #28a745;">Ventas Promedio: ${ventas_promedio:,.2f}</div>', unsafe_allow_html=True)

        # Producto con mayores ventas
        producto_top = df.groupby('producto')['venta_total'].sum().idxmax()
        ventas_producto_top = df.groupby('producto')['venta_total'].sum().max()
        st.markdown(f'<div class="metric" style="background-color: #ffc107;">Producto más vendido: {producto_top} (${ventas_producto_top:,.2f})</div>', unsafe_allow_html=True)

        # Turno con mayores ventas
        turno_top = df.groupby('turno')['venta_total'].sum().idxmax()
        ventas_turno_top = df.groupby('turno')['venta_total'].sum().max()
        st.markdown(f'<div class="metric" style="background-color: #17a2b8;">Turno más rentable: {turno_top} (${ventas_turno_top:,.2f})</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico interactivo de ventas por producto
        st.subheader('Ventas total por producto (Interactividad)')
        ventas_producto = df.groupby('producto')['venta_total'].sum().reset_index()
        fig1 = px.bar(ventas_producto, x='producto', y='venta_total', title='Ventas por Producto', color='producto', color_continuous_scale='Viridis')
        st.plotly_chart(fig1)

        # Gráfico de lineas
        st.subheader('Tendencia de Ventas Semanal')

        # 1. Asegurar formato fecha
        df['fecha'] = pd.to_datetime(df['fecha'])

        # 2. Agrupar por SEMANA ('W' = Weekly)
        # Esto suaviza el gráfico: en lugar de 200 puntos ruidosos, tendrás ~30 barras claras.
        df_semanal = df.resample('W', on='fecha')['venta_total'].sum().reset_index()

        if len(df_semanal) > 1:
            # 3. Calcular la Regresión Lineal (Tendencia)
            df_semanal['fecha_num'] = df_semanal['fecha'].map(pd.Timestamp.timestamp)
            
            model = LinearRegression()
            X = df_semanal['fecha_num'].values.reshape(-1, 1)
            y = df_semanal['venta_total'].values
            
            model.fit(X, y)
            df_semanal['tendencia'] = model.predict(X)

            # 4. GRAFICAR (Barras + Línea)
            # Usamos BARRAS para los datos reales (se ve más "sólido" que los puntos)
            fig_trend = px.bar(
                df_semanal, 
                x='fecha', 
                y='venta_total',
                title='Evolución de Ventas Semanales + Tendencia',
                labels={'venta_total': 'Ventas ($)', 'fecha': 'Semana'},
                opacity=0.6  # Un poco transparente para que la línea destaque
            )
            
            # Agregamos la línea de tendencia encima
            fig_trend.add_scatter(
                x=df_semanal['fecha'], 
                y=df_semanal['tendencia'], 
                mode='lines', 
                name='Tendencia', 
                line=dict(color='red', width=4) # Línea roja y gruesa
            )
            
            # Ajustes visuales para que se vea profesional
            fig_trend.update_layout(
                xaxis_title="Semana",
                yaxis_title="Total Vendido ($)",
                showlegend=True
            )

            st.plotly_chart(fig_trend, use_container_width=True)
            
            # DATO CLAVE: Mostrar la tasa de crecimiento
            coef = model.coef_[0] * 604800 # Pendiente por segundos en una semana
            estado = "creciendo 📈" if coef > 0 else "decreciendo 📉"
            st.info(f"Análisis rápido: Tus ventas están {estado} a un ritmo promedio de ${abs(coef):.2f} por semana.")

        else:
            st.warning("No hay suficientes semanas de datos para calcular una tendencia.")

        # Gráfico interactivo de ventas por turno
        st.subheader('Ventas total por turno (Interactividad)')
        # Agrupar las ventas por turno
        ventas_turno = df.groupby('turno')['venta_total'].sum().reset_index()

        # Ahora, crea el gráfico de torta con las columnas correctas
        fig2 = px.pie(ventas_turno, names='turno', values='venta_total', title='Ventas por Turno', color='turno', color_discrete_sequence=px.colors.qualitative.Set3)

        # Mostrar el gráfico
        st.plotly_chart(fig2)

        # Gráfico interactivo de ventas por tienda
        st.subheader('Ventas total por tienda (Interactividad)')
        ventas_tienda = df.groupby('tienda')['venta_total'].sum().reset_index()
        fig3 = px.bar(ventas_tienda, x='tienda', y='venta_total', title='Ventas por Tienda', color='tienda', color_continuous_scale='RdBu')
        st.plotly_chart(fig3)

        # Gráfico de dispersión de ventas por producto vs turno
        st.subheader('Comparativa: Ventas por Producto y Turno')

        # 1. Agrupamos los datos (Data Science Tip: Siempre agrega antes de graficar)
        df_agrupado = df.groupby(['producto', 'turno'])['venta_total'].sum().reset_index()

        # 2. Creamos el gráfico de barras agrupadas
        fig4 = px.bar(
            df_agrupado, 
            x='producto', 
            y='venta_total', 
            color='turno', 
            barmode='group',  # 'group' pone las barras al lado, 'stack' las apila
            title='Ventas Totales por Producto desglosado por Turno',
            text_auto='.2s',  # Muestra el valor resumido encima de la barra (ej: 1.2k)
            color_discrete_sequence=px.colors.qualitative.Pastel # Colores más suaves
        )

        fig4.update_layout(xaxis_title="Producto", yaxis_title="Venta Total ($)")
        st.plotly_chart(fig4, use_container_width=True)

        # --- SECCIÓN CORRELACIÓN ---
        st.title("Correlación de Pearson - ventas")

        st.subheader("Variables numéricas disponibles")
        vars_numericas = df.select_dtypes(include='number').columns.tolist()
        st.write(vars_numericas)

        var_x = st.selectbox("Selecciona la primera variable", vars_numericas)
        var_y = st.selectbox("Selecciona la segunda variable", vars_numericas)

        if var_x and var_y:
            if var_x != var_y:
                correlacion = df[var_x].corr(df[var_y], method='pearson')

                st.metric(
                    label=f"Correlación entre {var_x} y {var_y}",
                    value=round(correlacion, 3)
                )

                # Interpretación automática
                interpretacion = ""
                abs_corr = abs(correlacion)
                if abs_corr >= 0.7:
                    st.warning("Correlación fuerte")
                    interpretacion = "Existe una relación fuerte entre las variables seleccionadas."
                elif abs_corr >= 0.4:
                    st.info("Correlación moderada")
                    interpretacion = "Existe una relación moderada."
                elif abs_corr >= 0.2:
                    st.success("Correlación débil")
                    interpretacion = "La relación es débil."
                else:
                    st.write("Correlación nula o inexistente")
                    interpretacion = "No hay una relación significativa entre las variables."

                st.info(f"Interpretación: {interpretacion}")

            else:
                st.error("Seleccione dos variables diferentes")
        # Gráfico de correlación
        st.subheader("Matriz de Correlación")
        corr_matrix = df[vars_numericas].corr()

        # Usar Seaborn para el heatmap de correlación
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax, fmt=".2f", cbar_kws={'label': 'Correlación'})
        st.pyplot(fig)
else:
    # Mensaje informativo inicial si no hay archivo
    st.info("Por favor sube un archivo CSV para visualizar los datos. Se requieren las columnas: " + str(columnas_necesarias))
