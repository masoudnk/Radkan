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

from employer import views, policy_views

urlpatterns = [
    path('get_user_permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('create_employer/', views.create_employer, name='create_employer'),
    path('change_password/', views.change_password, name='password_reset'),
    path('create_password_reset_request/', views.create_password_reset_request, name='create_password_reset_request'),
    path('create_work_place/', views.create_work_place, name='create_work_place'),
    path('get_workplaces_list/', views.get_workplaces_list, name='get_workplaces_list'),
    path('create_employee/', views.create_employee, name='create_employee'),
    path('create_holiday/', views.create_holiday, name='create_holiday'),
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
    path('get_work_shift_plan_type_choices/', views.get_work_shift_plan_type_choices, name='get_work_shift_plan_type_choices'),

    # ----------------------------------------------------------------
    path('create_work_policy/', policy_views.create_work_policy, name='create_work_policy'),
    path('create_earned_leave_policy/', policy_views.create_earned_leave_policy, name='create_earned_leave_policy'),
    path('create_sick_leave_policy/', policy_views.create_sick_leave_policy, name='create_sick_leave_policy'),
    path('create_overtime_policy/', policy_views.create_overtime_policy, name='create_overtime_policy'),
    path('create_manual_traffic_policy/', policy_views.create_manual_traffic_policy, name='create_manual_traffic_policy'),
    path('create_work_mission_policy/', policy_views.create_work_mission_policy, name='create_work_mission_policy'),

]
