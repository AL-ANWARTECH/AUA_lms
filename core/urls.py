from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('courses/', views.course_list, name='course_list'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:pk>/unenroll/', views.unenroll_course, name='unenroll_course'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:course_pk>/module/create/', views.create_module, name='create_module'),
    path('module/<int:module_pk>/lesson/create/', views.create_lesson, name='create_lesson'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:pk>/complete/', views.complete_lesson, name='complete_lesson'),
    path('lesson/<int:pk>/uncomplete/', views.uncomplete_lesson, name='uncomplete_lesson'),
]