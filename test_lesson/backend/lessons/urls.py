from django.urls import path
from . import views


urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('api/start-lesson/', views.start_lesson, name='start_lesson'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
]
