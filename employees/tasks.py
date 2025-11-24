# employees/tasks.py

from celery import shared_task
import time
from .models import Employee

@shared_task
def send_welcome_email(employee_id):
    """
    مهمة تجريبية لإرسال بريد إلكتروني ترحيبي.
    في الوقت الحالي، ستقوم فقط بطباعة رسالة.
    """
    try:
        employee = Employee.objects.get(id=employee_id)
        print(f"Preparing to send a welcome email to {employee.first_name} {employee.last_name}...")
        # محاكاة لعملية تستغرق وقتاً (مثل الاتصال بخادم البريد)
        time.sleep(5) # انتظر 5 ثوانٍ
        print("==============================================")
        print(f"Email SENT successfully to {employee.email}!")
        print("==============================================")
        return f"Email sent to {employee.email}"
    except Employee.DoesNotExist:
        return f"Employee with id {employee_id} does not exist."