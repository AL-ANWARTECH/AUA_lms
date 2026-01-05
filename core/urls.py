from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Authentication & Home ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Password Reset ---
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),

    # --- Dashboards ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # --- Course Management ---
    path('courses/', views.course_list, name='course_list'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:pk>/unenroll/', views.unenroll_course, name='unenroll_course'),
    
    # --- Modules & Lessons ---
    path('course/<int:course_pk>/module/create/', views.create_module, name='create_module'),
    path('module/<int:module_pk>/lesson/create/', views.create_lesson, name='create_lesson'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:pk>/complete/', views.complete_lesson, name='complete_lesson'),
    path('lesson/<int:pk>/uncomplete/', views.uncomplete_lesson, name='uncomplete_lesson'),

    # --- Quizzes ---
    path('quiz/<int:lesson_pk>/create/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:pk>/manage/', views.manage_quiz, name='manage_quiz'),
    path('quiz/<int:quiz_pk>/question/create/', views.create_question, name='create_question'),
    path('question/<int:pk>/edit/', views.edit_question, name='edit_question'),
    path('quiz/<int:quiz_pk>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_pk>/submit/', views.submit_quiz, name='submit_quiz'),

    # --- Assignments ---
    path('assignment/<int:lesson_pk>/create/', views.create_assignment, name='create_assignment'),

    # --- Grading ---
    path('gradebook/student/', views.student_gradebook, name='student_gradebook'),
    path('gradebook/instructor/<int:course_pk>/', views.instructor_gradebook, name='instructor_gradebook'),
    path('grade/<int:enrollment_pk>/<str:grade_type>/<int:item_pk>/', views.record_grade, name='record_grade'),

    # --- Forums ---
    path('forum/<int:course_pk>/', views.course_forum, name='course_forum'),
    path('forum/<int:forum_pk>/topic/create/', views.create_topic, name='create_topic'),
    path('topic/<int:topic_pk>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:topic_pk>/post/create/', views.create_post, name='create_post'),

    # --- Certificates ---
    path('certificate/<int:enrollment_pk>/', views.generate_certificate, name='generate_certificate'),
    path('certificates/student/', views.student_certificates, name='student_certificates'),
    path('certificates/instructor/', views.instructor_certificates, name='instructor_certificates'),
    path('certificates/instructor/<int:course_pk>/', views.instructor_certificates, name='instructor_certificates_detail'),
    path('certificate/template/<int:course_pk>/', views.manage_certificate_template, name='manage_certificate_template'),
    path('certificate/eligibility/<int:course_pk>/', views.check_certificate_eligibility, name='certificate_eligibility'),

    # --- Notifications ---
    path('notifications/', views.notifications_list, name='notifications_list'),
    
    # FIXED: Changed name from 'notification_preference' to 'notification_preferences'
    path('notifications/preferences/', views.notification_preference, name='notification_preferences'),
    
    path('notifications/<int:notification_pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # --- Analytics & Reporting ---
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/generate/', views.generate_report, name='generate_report'),
    path('analytics/report/<int:report_pk>/', views.view_report, name='view_report'),
    path('analytics/course/<int:course_pk>/', views.course_analytics, name='course_analytics'),
    path('analytics/student/<int:student_pk>/', views.student_analytics, name='student_analytics'),

    # --- Accessibility ---
    path('accessibility/', views.accessibility_settings, name='accessibility_settings'),
    path('accessibility/toggle/<str:mode>/', views.toggle_accessibility_mode, name='toggle_accessibility_mode'),
    path('accessibility/statement/', views.accessibility_statement, name='accessibility_statement'),
    path('accessibility/shortcuts/', views.keyboard_shortcuts, name='keyboard_shortcuts'),
    path('accessibility/audit/', views.accessibility_audit_log, name='accessibility_audit_log'),
    path('accessibility/scan/', views.run_accessibility_scan, name='run_accessibility_scan'),
    path('accessibility/resources/', views.accessibility_resources, name='accessibility_resources'),
]