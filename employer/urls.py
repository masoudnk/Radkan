from django.urls import path

from employer import views, policy_views, report_views, employee_views

urlpatterns = [
    path('test/<key>/', views.test, name='test'),

    # --------------------------password--------------------------------------#}
    path('change_password/', views.change_password, name='password_reset'),
    path('create_password_reset_request/', views.create_password_reset_request, name='create_password_reset_request'),

    # -----------------------------permissions-----------------------------------#}
    path('get_permissions/', views.get_permissions, name='get_permissions'),
    path('get_user_permissions/', views.get_user_permissions, name='get_user_permissions'),

    # ------------------------employer----------------------------------------#}
    path('create_employer/', views.create_employer, name='create_employer'),
    path('get_employer_profile/', views.get_employer_profile, name='get_employer_profile'),
    path('update_employer_info/', views.update_employer_info, name='update_employer_info'),
    path('get_employer_choices/', views.get_employer_choices, name='get_employer_choices'),
    path('get_legal_entity_types_list/', views.get_legal_entity_types_list, name='get_legal_entity_types_list'),
    path('get_employer_messages_list/', views.get_employer_messages_list, name='get_employer_messages_list'),

    # -----------------------------workplace-----------------------------------#}
    path('create_work_place/', views.create_work_place, name='create_work_place'),
    path('get_workplaces_list/', views.get_workplaces_list, name='get_workplaces_list'),
    path('update_work_place/<int:oid>/', views.update_work_place, name='update_work_place'),
    path('get_workplaces_excel/', views.get_workplaces_excel, name='get_workplaces_excel'),
    path('search_workplaces/', views.search_workplaces, name='search_workplaces'),
    path('import_work_places_excel/', views.import_work_places_excel, name='import_work_places_excel'),
    path('delete_workplace/<int:oid>/', views.delete_workplace, name='delete_workplace'),
    path('get_workplace/<int:oid>/', views.get_workplace, name='get_workplace'),

    # -------------------------------employee---------------------------------#}
    path('delete_employee/<int:oid>/', views.delete_employee, name='delete_employee'),
    path('get_employee/<int:oid>/', views.get_employee, name='get_employee'),
    path('update_employee/<int:oid>/', views.update_employee, name='update_employee'),
    path('create_employee/', views.create_employee, name='create_employee'),
    path('get_employees_excel/', views.get_employees_excel, name='get_employees_excel'),
    path('search_employees/', views.search_employees, name='search_employees'),
    path('get_employees_list/', views.get_employees_list, name='get_employees_list'),

    # -------------------------------holiday---------------------------------#}
    path('delete_holiday/<int:oid>/', views.delete_holiday, name='delete_holiday'),
    path('search_holidays/', views.search_holidays, name='search_holidays'),
    path('create_holiday/', views.create_holiday, name='create_holiday'),
    path('get_holidays_list/', views.get_holidays_list, name='get_holidays_list'),

    # -----------------------------category-----------------------------------#}
    path('update_work_category/<int:oid>/', views.update_work_category, name='update_work_category'),
    path('get_work_category/<int:oid>/', views.get_work_category, name='get_work_category'),
    path('delete_work_category/<int:oid>/', views.delete_work_category, name='delete_work_category'),
    path('get_work_categories_list/', views.get_work_categories_list, name='get_work_categories_list'),
    path('create_work_category/', views.create_work_category, name='create_work_category'),

    # -----------------------------ticket-----------------------------------#}
    path('get_tickets_list/', views.get_tickets_list, name='get_tickets_list'),
    path('create_ticket_conversation/<int:oid>/', views.create_ticket_conversation, name='create_ticket_conversation'),
    path('get_ticket/<int:oid>/', views.get_ticket, name='get_ticket'),
    path('update_ticket_status/<int:oid>/', views.update_ticket_status, name='update_ticket_status'),
    path('create_ticket/', views.create_ticket, name='create_ticket'),
    path('get_ticket_sections_list/', views.get_ticket_sections_list, name='get_ticket_sections_list'),

    # ---------------------------employee_request-------------------------------------#}
    path('update_employee_request_status/<int:oid>/', views.update_employee_request_status, name='update_employee_request_status'),
    path('get_employee_requests_excel/', views.get_employee_requests_excel, name='get_employee_requests_excel'),
    path('get_employee_request_choices/', views.get_employee_request_choices, name='get_employee_request_choices'),
    path('create_employee_request/', views.create_employee_request, name='create_employee_request'),
    path('get_employees_requests_list/', views.get_employees_requests_list, name='get_employees_requests_list'),

    # -------------------------shift---------------------------------------#}
    path('delete_work_shift/<int:oid>/', views.delete_work_shift, name='delete_work_shift'),
    path('create_work_shift/', views.create_work_shift, name='create_work_shift'),
    path('get_work_shifts_list/', views.get_work_shifts_list, name='get_work_shifts_list'),
    path('create_work_shift_plan/', views.create_work_shift_plan, name='create_work_shift_plan'),
    path('get_work_shift_plans_list/<int:oid>/', views.get_work_shift_plans_list, name='get_work_shift_plans_list'),
    path('update_work_shift_plan/', views.update_work_shift_plan, name='update_work_shift_plan'),
    path('search_work_shift/', views.search_work_shift, name='search_work_shift'),
    path('get_work_shift_plan_choices/', views.get_work_shift_plan_choices, name='get_work_shift_plan_choices'),

    # ------------------------------manager----------------------------------#}
    path('update_manager/<int:oid>/', views.update_manager, name='update_manager'),
    path('get_manager/<int:oid>/', views.get_manager, name='get_manager'),
    path('delete_manager/<int:oid>/', views.delete_manager, name='delete_manager'),
    path('create_manager/', views.create_manager, name='create_manager'),
    path('get_managers_list/', views.get_managers_list, name='get_managers_list'),

    # ----------------------------------------------------------------#}
    # path('get_attendance_device_choices/', views.get_attendance_device_choices, name='get_attendance_device_choices'),

    # ---------------------------project-------------------------------------#}
    path('get_projects_list/', views.get_projects_list, name='get_projects_list'),
    path('create_project/', views.create_project, name='create_project'),
    path('update_project/<int:oid>/', views.update_project, name='update_project'),
    path('get_project/<int:oid>/', views.get_project, name='get_project'),
    path('delete_project/<int:oid>/', views.delete_project, name='delete_project'),

    # ----------------------------radkan_message------------------------------------#}
    path('get_radkan_messages_view_info_list/<int:oid>/', views.get_radkan_messages_view_info_list, name='get_radkan_messages_view_info_list'),
    path('get_radkan_messages_list/', views.get_radkan_messages_list, name='get_radkan_messages_list'),
    path('create_radkan_message/', views.create_radkan_message, name='create_radkan_message'),
    path('delete_radkan_message/<int:oid>/', views.delete_radkan_message, name='delete_radkan_message'),

    # -----------------------------rtsp-----------------------------------#}
    path('create_rtsp/', views.create_rtsp, name='create_rtsp'),
    path('update_rtsp/<int:oid>/', views.update_rtsp, name='update_rtsp'),
    path('get_rtsps_list/', views.get_rtsps_list, name='get_rtsps_list'),
    path('get_rtsp/<int:oid>/', views.get_rtsp, name='get_rtsp'),
    path('delete_rtsp/<int:oid>/', views.delete_rtsp, name='delete_rtsp'),

    # ----------------------------employee_views------------------------------------
    path('create_employee_request_for_employees/', employee_views.create_employee_request_for_employees, name='create_employee_request_for_employees'),
    path('create_roll_call/', employee_views.create_roll_call, name='create_roll_call'),
    path('get_employee_profile/', employee_views.get_employee_profile, name='get_employee_profile'),
    path('get_employee_work_shift_plans_list/', employee_views.get_employee_work_shift_plans_list, name='get_employee_work_shift_plans_list'),
    path('get_message/<int:oid>/', employee_views.get_message, name='get_message'),
    path('get_roll_calls_list/<int:year>/<int:month>/', employee_views.get_roll_calls_list, name='get_roll_calls_list'),
    path('get_employee_requests_list/<int:year>/<int:month>/', employee_views.get_employee_requests_list, name='get_employee_requests_list'),
    path('get_employee_report_for_employees/', employee_views.get_employee_report_for_employees, name='get_employee_report_for_employees'),

    # -----------------------------------report_views-----------------------------
    path('report_employees_function/', report_views.report_employees_function, name='report_employees_function'),
    path('get_employer_dashboard/', report_views.get_employer_dashboard, name='get_employer_dashboard'),
    path('get_employee_report/<int:oid>/', report_views.get_employee_report, name='get_employee_report'),
    path('get_employees_function_report_excel/', report_views.get_employees_function_report_excel, name='get_employees_function_report_excel'),
    path('report_employee_traffic/<int:oid>/', report_views.report_employee_traffic, name='report_employee_traffic'),
    path('get_employee_traffic_report_excel/', report_views.get_employee_traffic_report_excel, name='get_employee_traffic_report_excel'),
    path('report_employee_leave/<int:oid>/', report_views.report_employee_leave, name='report_employee_leave'),
    path('report_employees_leave/', report_views.report_employees_leave, name='report_employees_leave'),
    path('report_project_traffic/', report_views.report_project_traffic, name='report_project_traffic'),
    path('get_employees_leave_excel/', report_views.get_employees_leave_excel, name='get_employees_leave_excel'),

    # -------------------------------policy_views---------------------------------
    path('get_work_policies_list/', policy_views.get_work_policies_list, name='get_work_policies_list'),
    path('get_leave_policy_choices/', policy_views.get_leave_policy_choices, name='get_leave_policy_choices'),
    path('create_work_policy/', policy_views.create_work_policy, name='create_work_policy'),
    path('create_earned_leave_policy/', policy_views.create_earned_leave_policy, name='create_earned_leave_policy'),
    path('create_sick_leave_policy/', policy_views.create_sick_leave_policy, name='create_sick_leave_policy'),
    path('create_overtime_policy/', policy_views.create_overtime_policy, name='create_overtime_policy'),
    path('create_manual_traffic_policy/', policy_views.create_manual_traffic_policy, name='create_manual_traffic_policy'),
    path('create_work_mission_policy/', policy_views.create_work_mission_policy, name='create_work_mission_policy'),
    path('delete_work_policy/<int:oid>/', policy_views.delete_work_policy, name='delete_work_policy'),

    path('get_work_policy/<int:oid>/', policy_views.get_work_policy, name='get_work_policy'),
    path('update_work_policy/<int:oid>/', policy_views.update_work_policy, name='update_work_policy'),
    path('update_earned_leave_policy/<int:wp_id>/', policy_views.update_earned_leave_policy, name='update_earned_leave_policy'),
    path('update_sick_leave_policy/<int:wp_id>/', policy_views.update_sick_leave_policy, name='update_sick_leave_policy'),
    path('update_overtime_policy/<int:wp_id>/', policy_views.update_overtime_policy, name='update_overtime_policy'),
    path('update_manual_traffic_policy/<int:wp_id>/', policy_views.update_manual_traffic_policy, name='update_manual_traffic_policy'),
    path('update_work_mission_policy/<int:wp_id>/', policy_views.update_work_mission_policy, name='update_work_mission_policy'),

]
