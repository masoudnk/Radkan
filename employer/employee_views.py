from rest_framework.decorators import api_view

from employer.views import manage_and_create_employee_request, POST_METHOD_STR


@api_view([POST_METHOD_STR])
def create_employee_request_for_employees(request):
    cpy_data = request.data.copy()
    cpy_data["employee_id"] = request.user.id
    return manage_and_create_employee_request(cpy_data)
