#from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Employee
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
@admin.register(Employee)
class EmployeeHistoryAdmin(SimpleHistoryAdmin):
    list_display = ["employee_id", "first_name", "last_name", "email"]
    history_list_display = ["status"]