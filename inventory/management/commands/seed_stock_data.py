# inventory/management/commands/seed_stock_data.py

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

# استيراد النماذج فقط، لا حاجة لاستيراد signals
from inventory.models import Product, StockMovement

# --------------------------------------------------------------------
# --- قمنا بنسخ الخوارزمية هنا كدالة مساعدة محلية ---
# --------------------------------------------------------------------
def calculate_and_update_prediction(product_instance):
    """
    دالة مساعدة محلية تقوم بنفس منطق الإشارة تمامًا.
    تحسب متوسط الاستهلاك اليومي لمنتج معين وتقوم بتحديثه.
    """
    # 1. تحديد النطاق الزمني: آخر 90 يومًا.
    ninety_days_ago = timezone.now() - timedelta(days=90)
    
    # 2. فلترة حركات المخزون ذات الصلة.
    relevant_movements = StockMovement.objects.filter(
        product=product_instance,
        movement_type='OUT',
        movement_date__gte=ninety_days_ago
    )
    
    # 3. حساب المدة الزمنية بالأيام.
    if relevant_movements.count() > 1:
        first_movement = relevant_movements.earliest('movement_date')
        last_movement = relevant_movements.latest('movement_date')
        time_delta_days = (last_movement.movement_date - first_movement.movement_date).days + 1
        
        # 4. حساب إجمالي الكمية المباعة.
        total_quantity_sold = sum(movement.quantity for movement in relevant_movements)

        # 5. حساب المتوسط اليومي الجديد.
        if time_delta_days > 0:
            new_daily_rate = total_quantity_sold / time_delta_days
        else:
            new_daily_rate = total_quantity_sold
    
    elif relevant_movements.count() == 1:
        new_daily_rate = relevant_movements.first().quantity
    
    else:
        new_daily_rate = 0.0

    # 6. تحديث حقل المنتج في قاعدة البيانات.
    product_instance.daily_consumption_rate = new_daily_rate
    product_instance.prediction_last_updated = timezone.now()
    product_instance.save(update_fields=['daily_consumption_rate', 'prediction_last_updated'])

# --------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Generates historical stock data AND recalculates all predictions.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # الجزء الأول: بذر البيانات (يبقى كما هو)
        self.stdout.write(self.style.SUCCESS('--- Step 1: Seeding Historical Data ---'))
        self.stdout.write('Deleting old OUT stock movements...')
        StockMovement.objects.filter(movement_type='OUT').delete()
        self.stdout.write('Resetting old prediction data...')
        Product.objects.all().update(daily_consumption_rate=0.00, prediction_last_updated=None)
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Please add products first.'))
            return
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)
        self.stdout.write(f'Generating data for {len(products)} products...')
        generated_movements = []
        for product in products:
            num_movements = random.randint(15, 50)
            for _ in range(num_movements):
                quantity = random.randint(1, 5)
                movement_date = start_date + timedelta(seconds=random.randint(0, 90*24*3600))
                movement = StockMovement(
                    product=product, movement_type='OUT', quantity=quantity,
                    movement_date=movement_date, notes='Generated historical data'
                )
                generated_movements.append(movement)
        self.stdout.write(f'Saving {len(generated_movements)} new movements...')
        StockMovement.objects.bulk_create(generated_movements)
        self.stdout.write('Updating current stock quantities...')
        for product in products:
            total_sold = sum(m.quantity for m in generated_movements if m.product == product)
            product.quantity_in_stock = max(0, 200 - total_sold)
            product.save(update_fields=['quantity_in_stock'])
        self.stdout.write(self.style.SUCCESS('Step 1 finished successfully.'))

        # --- الجزء الثاني: إعادة حساب التنبؤات (يستخدم الدالة المحلية الآن) ---
        self.stdout.write(self.style.SUCCESS('\n--- Step 2: Recalculating All Predictions ---'))
        count = 0
        for product in products:
            # استدعاء الدالة المساعدة المحلية مباشرة
            calculate_and_update_prediction(product)
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Step 2 finished: Successfully recalculated predictions for {count} products.'))
        self.stdout.write(self.style.SUCCESS('\nData seeding and prediction calculation complete!'))