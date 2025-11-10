"""Configuración centralizada para la aplicación Streamlit."""

N8N_WEBHOOK_URL = "https://n8n.yamboly.lat/webhook/b4b0f8c6-7ec2-4672-bb84-31ec2b3e2c5c"
SUPABASE_URL = "https://vvkmtgaarazlugtvabsz.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2a210Z2FhcmF6bHVndHZhYnN6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3MzI3NDIsImV4cCI6MjA3ODMwODc0Mn0.wH6pbV2UAFxJaVcKU0xdI8FBwYaDq-heVAUEft2B0OE"
)

# Tablas y columnas relacionadas con la asignación de cursos.
STUDENTS_TABLE = "users"
COURSES_TABLE = "subjects"
STUDENT_COURSES_TABLE = "user_subscriptions"
STUDENT_COURSES_STUDENT_FIELD = "user_id"
STUDENT_COURSES_COURSE_FIELD = "subject_id"

# Campos sugeridos para mostrar nombres en la interfaz.
STUDENT_NAME_FIELDS = ("full_name", "name", "first_name", "email")
COURSE_NAME_FIELDS = ("title", "name")

