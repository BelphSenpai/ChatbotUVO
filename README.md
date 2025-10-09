# ChatbotUVO

Nota de mantenimiento: commit de prueba para verificar persistencia de fichas/notas tras despliegue.

**ChatbotUVO** es un asistente conversacional basado en RAG (Retrieval-Augmented Generation), que utiliza embeddings y un índice FAISS para recuperar información relevante de una base de datos textual antes de generar respuestas con un modelo de lenguaje.

> 🚀 **Colaboración activa**: Proyecto en desarrollo colaborativo

El sistema se apoya en dos modelos de inteligencia artificial:

- 🤖 Un modelo para generación de respuestas (chat).  
- 🧠 Un modelo especializado en el filtrado y selección de información relevante desde la base de conocimiento.

---

## 🧠 ¿Cómo funciona?

1. El usuario introduce una pregunta o mensaje.  
2. Se generan los embeddings del input y se buscan los documentos más relevantes mediante FAISS.  
3. El modelo de filtrado evalúa los resultados y selecciona los más pertinentes.  
4. El modelo de chat genera una respuesta en función del input y el contexto recuperado.

---

## 🧰 Tecnologías utilizadas

- Python  
- [OpenAI API](https://platform.openai.com/)  
- FAISS  
- Embeddings (`text-embedding-ada-002`)  
- Variables de entorno (`.env`)

---

## ⚙️ Instalación

1. **Clona el repositorio:**

```bash
git clone https://github.com/BelphSenpai/ChatbotUVO.git
cd ChatbotUVO
```

2. **Instala las dependencias (se recomienda entorno virtual):**

```bash
pip install -r requirements.txt
```

3. **Crea el archivo `.env` en el directorio raíz:**

```env
OPENAI_API_KEY=tu_clave_de_openai
```

> ⚠️ Este archivo contiene información sensible. Asegúrate de que no se suba a ningún repositorio público.

---

## ▶️ Uso

Ejecuta el chatbot desde la terminal con:

```bash
python main.py
```

Esto abrirá una consola interactiva para escribir preguntas y recibir respuestas generadas por IA, con acceso a la base de conocimiento.

---

## 📁 Estructura del proyecto (ejemplo)

```
ChatbotUVO/
├── data/                  → Documentos base para embeddings  
├── index/                 → Índices FAISS  
├── models/                → Lógica para chat y filtrado  
├── utils/                 → Funciones auxiliares  
├── main.py                → Punto de entrada del programa  
├── requirements.txt       → Dependencias del proyecto  
└── .env                   → Clave API de OpenAI (no incluida)  
```

---

## 📌 Notas

- El sistema es modular y puede adaptarse fácilmente a nuevas fuentes de datos.  
- Actualmente funciona únicamente desde consola.  
- Se planea una futura integración con API REST o interfaz gráfica.

---

## ✅ Requisitos

- Python 3.8 o superior  
- Clave de API de OpenAI  
- Conexión a internet para acceder a la API

---

## 🛡️ Licencia

Este proyecto está bajo la licencia MIT.

---

## 📬 Contacto

Creado por [BelphSenpai](https://github.com/BelphSenpai)  
¿Preguntas o sugerencias? No dudes en abrir un issue en el repositorio.