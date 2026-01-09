import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Visor de ventas -Tienda de conveniencia')

archivo = st.file_uploader('Sube el archivo CSV', type=['csv'])

if archivo is not None:
    df = pd.read_csv(archivo)
    st.subheader('Vista previa del archivo')
    st.dataframe(df)
    
    #Validacion
    columnas_necesarias = {'producto', 'turno', 'tienda','venta_total'}
    if not columnas_necesarias.issubset(df.columns):
        st.error('El archivo debe contener las columnas: '+ str(columnas_necesarias))
    else:
        # Ventas de productos
        st.subheader('Ventas total por tipo de producto')
        ventas_producto = df.groupby('producto')['venta_total'].sum()

        fig1 = plt.figure()
        ventas_producto.plot(kind='bar', x='producto', y='venta_total')
        plt.xticks(rotation=45)
        st.pyplot(fig1)
