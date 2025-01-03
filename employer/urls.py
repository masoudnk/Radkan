"""
URL configuration for Radkan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from employer import views, policy_views, report_views,employee_views

urlpatterns = [
    path('test/', views.test, name='test'),
    path('get_user_permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('create_employer/', views.create_employer, name='create_employer'),
    path('change_password/', views.change_password, name='password_reset'),
    path('create_password_reset_request/', views.create_password_reset_request, name='create_password_reset_request'),
    path('create_work_place/', views.create_work_place, name='create_work_place'),
    path('get_workplaces_list/', views.get_workplaces_list, name='get_workplaces_list'),
    path('create_employee/', views.create_employee, name='create_employee'),
    path('create_holiday/', views.create_holiday, name='create_holiday'),
    path('get_holidays_list/', views.get_holidays_list, name='get_holidays_list'),
    path('create_work_category/', views.create_work_category, name='create_work_category'),
    path('get_provinces/', views.get_provinces, name='get_provinces'),
    path('get_cities/', views.get_cities, name='get_cities'),
    path('create_ticket/', views.create_ticket, name='create_ticket'),
    path('get_ticket_sections_list/', views.get_ticket_sections_list, name='get_ticket_sections_list'),
    path('create_employee_request/', views.create_employee_request, name='create_employee_request'),
    path('get_employee_requests_list/', views.get_employee_requests_list, name='get_employee_requests_list'),
    path('employer_login/', views.employer_login, name='employer_login'),
    path('get_employer_profile/', views.get_employer_profile, name='get_employer_profile'),
    path('update_employer_info/', views.update_employer_info, name='update_employer_info'),
    path('create_work_shift/', views.create_work_shift, name='create_work_shift'),
    path('get_work_shifts_list/', views.get_work_shifts_list, name='get_work_shifts_list'),
    path('create_work_shift_plan/', views.create_work_shift_plan, name='create_work_shift_plan'),
    path('get_work_shift_plans_list/', views.get_work_shift_plans_list, name='get_work_shift_plans_list'),
    path('update_work_shift_plan/', views.update_work_shift_plan, name='update_work_shift_plan'),
    path('create_manager/', views.create_manager, name='create_manager'),
    path('get_permissions/', views.get_permissions, name='get_permissions'),
    path('get_workplaces_excel/', views.get_workplaces_excel, name='get_workplaces_excel'),
    path('search_workplaces/', views.search_workplaces, name='search_workplaces'),
    path('search_work_shift/', views.search_work_shift, name='search_work_shift'),
    path('get_employees_excel/', views.get_employees_excel, name='get_employees_excel'),
    path('search_employees/', views.search_employees, name='search_employees'),
    path('get_employees_list/', views.get_employees_list, name='get_employees_list'),
    path('get_employee_requests_excel/', views.get_employee_requests_excel, name='get_employee_requests_excel'),
    path('get_employee_request_choices/', views.get_employee_request_choices, name='get_employee_request_choices'),
    path('get_employer_choices/', views.get_employer_choices, name='get_employer_choices'),
    path('get_attendance_device_choices/', views.get_attendance_device_choices, name='get_attendance_device_choices'),
    path('get_leave_policy_choices/', views.get_leave_policy_choices, name='get_leave_policy_choices'),
    path('get_work_shift_plan_choices/', views.get_work_shift_plan_choices, name='get_work_shift_plan_choices'),
    path('delete_workplace/<int:oid>/', views.delete_workplace, name='delete_workplace'),
    path('delete_work_shift/<int:oid>/', views.delete_work_shift, name='delete_work_shift'),

    # ----------------------------employee_views------------------------------------
    path('create_employee_request_for_employees/', employee_views.create_employee_request_for_employees, name='create_employee_request_for_employees'),

    # -----------------------------------report_views-----------------------------
    path('report_employees_function/', report_views.report_employees_function, name='report_employees_function'),
    path('get_employer_dashboard/', report_views.get_employer_dashboard, name='get_employer_dashboard'),

    # -------------------------------policy_views---------------------------------
    path('create_work_policy/', policy_views.create_work_policy, name='create_work_policy'),
    path('create_earned_leave_policy/', policy_views.create_earned_leave_policy, name='create_earned_leave_policy'),
    path('create_sick_leave_policy/', policy_views.create_sick_leave_policy, name='create_sick_leave_policy'),
    path('create_overtime_policy/', policy_views.create_overtime_policy, name='create_overtime_policy'),
    path('create_manual_traffic_policy/', policy_views.create_manual_traffic_policy, name='create_manual_traffic_policy'),
    path('create_work_mission_policy/', policy_views.create_work_mission_policy, name='create_work_mission_policy'),

]
