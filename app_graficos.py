import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

st.title('Visor de ventas -Tienda de conveniencia')

# Definir columnas necesarias globalmente para evitar errores
columnas_necesarias = {'producto', 'turno', 'tienda', 'venta_total'}

archivo = st.file_uploader('Sube el archivo CSV', type=['csv'])

if archivo is not None:
    # Cargar el dataframe una sola vez
    df = pd.read_csv(archivo)
    st.subheader('Vista previa del archivo')
    st.dataframe(df)
    
    # Validacion
    if not columnas_necesarias.issubset(df.columns):
        st.error('El archivo debe contener las columnas: ' + str(columnas_necesarias))
    else:
        # KPIs generales
        total_ventas = df['venta_total'].sum()
        promedio_ventas = df['venta_total'].mean()

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

        
    
        
        # Ventas de productos
        st.subheader('Ventas total por producto (Interactividad)')
        ventas_producto = df.groupby('producto')['venta_total'].sum().reset_index()
        fig1 = px.bar(ventas_producto, x='producto', y='venta_total', title='Ventas por Producto')
        st.plotly_chart(fig1)
    
         # Gráfico interactivo de ventas por turno
        st.subheader('Ventas total por turno (Interactividad)')
        ventas_turno = df.groupby('turno')['venta_total'].sum().reset_index()
        fig2 = px.bar(ventas_turno, x='turno', y='venta_total', title='Ventas por Turno')
        st.plotly_chart(fig2)
        
        # Gráfico interactivo de ventas por tienda
        st.subheader('Ventas total por tienda (Interactividad)')
        ventas_tienda = df.groupby('tienda')['venta_total'].sum().reset_index()
        fig3 = px.bar(ventas_tienda, x='tienda', y='venta_total', title='Ventas por Tienda')
        st.plotly_chart(fig3)
       

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
else:
    # Mensaje informativo inicial si no hay archivo
    st.info("Por favor sube un archivo CSV para visualizar los datos. Se requieren las columnas: " + str(columnas_necesarias))
