#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar duplicados en los archivos de poderes.
Elimina bloques de texto duplicados manteniendo solo una copia de cada uno.
"""

import os
import sys

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PODERES_DIR = os.path.join(BASE_DIR, 'www', 'poderes', 'usuarios')


def limpiar_duplicados(contenido):
    """
    Limpia bloques duplicados del contenido.
    Divide por bloques (separados por líneas vacías) y elimina duplicados.
    """
    if not contenido.strip():
        return ""
    
    # Dividir en bloques (separados por una o más líneas vacías)
    bloques = []
    bloque_actual = []
    
    for linea in contenido.split('\n'):
        linea_stripped = linea.strip()
        if not linea_stripped:
            # Si encontramos una línea vacía y tenemos contenido, guardamos el bloque
            if bloque_actual:
                bloque_texto = '\n'.join(bloque_actual).strip()
                if bloque_texto:
                    bloques.append(bloque_texto)
                bloque_actual = []
        else:
            bloque_actual.append(linea)
    
    # Añadir el último bloque si existe
    if bloque_actual:
        bloque_texto = '\n'.join(bloque_actual).strip()
        if bloque_texto:
            bloques.append(bloque_texto)
    
    # Eliminar duplicados manteniendo el orden
    bloques_unicos = []
    vistos = set()
    
    for bloque in bloques:
        # Normalizar el bloque para comparación (eliminar espacios extra)
        bloque_normalizado = '\n'.join(linea.strip() for linea in bloque.split('\n') if linea.strip())
        if bloque_normalizado and bloque_normalizado not in vistos:
            vistos.add(bloque_normalizado)
            bloques_unicos.append(bloque)
    
    # Reconstruir el contenido con doble línea vacía entre bloques
    return '\n\n'.join(bloques_unicos)


def limpiar_archivo(usuario):
    """Limpia los duplicados de un archivo de poderes."""
    ruta = os.path.join(PODERES_DIR, f"{usuario}.txt")
    
    if not os.path.exists(ruta):
        return False
    
    try:
        # Leer contenido
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido_original = f.read()
        
        # Limpiar duplicados
        contenido_limpiado = limpiar_duplicados(contenido_original)
        
        # Solo escribir si hay cambios
        if contenido_limpiado.strip() != contenido_original.strip():
            # Guardar backup
            ruta_backup = ruta + '.backup'
            with open(ruta_backup, 'w', encoding='utf-8') as f:
                f.write(contenido_original)
            
            # Escribir contenido limpiado
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(contenido_limpiado)
            
            return True
        return False
    except Exception as e:
        print(f"✗ Error procesando {usuario}: {e}")
        return False


def main():
    print("=== Limpiar Duplicados en Archivos de Poderes ===\n")
    
    if not os.path.exists(PODERES_DIR):
        print(f"Error: No existe el directorio {PODERES_DIR}")
        return
    
    archivos_procesados = 0
    archivos_limpiados = 0
    
    for filename in os.listdir(PODERES_DIR):
        if not filename.endswith('.txt') or filename.endswith('.backup'):
            continue
        
        usuario = os.path.splitext(filename)[0]
        archivos_procesados += 1
        
        if limpiar_archivo(usuario):
            archivos_limpiados += 1
            print(f"✓ Limpiado: {usuario}")
    
    print(f"\n=== Proceso completado ===")
    print(f"Archivos procesados: {archivos_procesados}")
    print(f"Archivos limpiados: {archivos_limpiados}")
    print(f"\nNota: Se han creado archivos .backup por si necesitas recuperar el contenido original.")


if __name__ == '__main__':
    main()

