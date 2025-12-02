"""Configuración centralizada para la aplicación Streamlit."""

N8N_WEBHOOK_URL = "https://n8n.yamboly.lat/webhook/b4b0f8c6-7ec2-4672-bb84-31ec2b3e2c5c"
SUPABASE_URL = "https://kxieicvtrimhozgrykex.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4aWVpY3Z0cmltaG96Z3J5a2V4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODc5NzAsImV4cCI6MjA4MDI2Mzk3MH0.2bVO6YjcsaOCT70YeVuG7pZgmPSyM_j7VfR-zK6px1Q"
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

