from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from products.models import Product
from .models import ReturnItem, ReturnTransaction, Sale, SaleItem


@login_required
def billing_home(request):
    products = Product.objects.filter(is_active=True)
    active_staff = CustomUser.objects.filter(role='staff', is_active=True)

    sales = Sale.objects.filter(status='completed').select_related('staff')
    today = timezone.localdate()
    today_sales = sales.filter(created_at__date=today)

    context = {
        'products': products.order_by('name'),
        'total_products': products.count(),
        'low_stock_products': products.filter(stock_quantity__lte=10).count(),
        'total_stock': sum(product.stock_quantity for product in products),
        'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'today_revenue': today_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'total_transactions': sales.count(),
        'today_transactions': today_sales.count(),
        'active_staff': active_staff.count(),
        'recent_sales': sales.order_by('-created_at')[:10],
        'user': request.user,
    }
    return render(request, 'billing_home.html', context)


@login_required
def pos_billing(request):
    products = Product.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        selected_items = []
        subtotal = Decimal('0.00')
        discount = Decimal(request.POST.get('discount', '0') or '0')

        for product in products:
            quantity = request.POST.get(f'qty_{product.id}')
            if quantity is None:
                continue
            try:
                qty = int(quantity)
            except (TypeError, ValueError):
                continue
            if qty <= 0:
                continue
            if qty > product.stock_quantity:
                return render(request, 'ceatenewbill.html', {
                    'products': products,
                    'error': f'Not enough stock for {product.name}. Available: {product.stock_quantity}.',
                    'user': request.user,
                })
            line_total = product.selling_price * qty
            subtotal += line_total
            selected_items.append({
                'product': product,
                'quantity': qty,
                'unit_price': product.selling_price,
                'total_price': line_total,
            })

        if not selected_items:
            return render(request, 'ceatenewbill.html', {
                'products': products,
                'error': 'Please select at least one product to create a bill.',
                'user': request.user,
            })

        total_amount = subtotal - discount
        bill_number = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        sale = Sale.objects.create(
            bill_number=bill_number,
            staff=request.user,
            subtotal=subtotal,
            discount=discount,
            total_amount=total_amount,
            payment_method=request.POST.get('payment_method', 'cash'),
            status='completed',
        )

        for item in selected_items:
            product = item['product']
            product.stock_quantity -= item['quantity']
            product.save(update_fields=['stock_quantity'])

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price'],
            )

        return redirect('billing_home')

    return render(request, 'ceatenewbill.html', {
        'products': products,
        'user': request.user,
    })

def _build_sale_item_rows(sale):
    rows = []
    if not sale:
        return rows

    for sale_item in sale.items.select_related('product').all():
        previous_returned = sale_item.return_items.aggregate(total=Sum('quantity'))['total'] or 0
        available = int(sale_item.quantity) - int(previous_returned)
        rows.append({
            'sale_item': sale_item,
            'previous_returned': int(previous_returned),
            'available': max(0, available),
            'default_return_qty': min(1, max(0, available)),
        })
    return rows


@login_required
def returns_page(request):
    sales = Sale.objects.filter(status='completed').select_related('staff').prefetch_related('items__product', 'items__return_items').order_by('-created_at')
    selected_sale = None
    selected_sale_items = []
    error_message = None
    success_message = None

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        selected_sale = get_object_or_404(Sale, pk=sale_id, status='completed')

        selected_ids = set()
        for value in request.POST.getlist('return_selected'):
            if value:
                selected_ids.add(value)

        return_rows = []
        for sale_item in selected_sale.items.select_related('product').all():
            selected = (
                request.POST.get(f'return_selected_{sale_item.id}') == 'on'
                or request.POST.get(f'return_selected_{sale_item.product.id}') == 'on'
                or str(sale_item.id) in selected_ids
                or str(sale_item.product.id) in selected_ids
            )
            if not selected:
                continue

            quantity_raw = request.POST.get(f'return_qty_{sale_item.id}') or request.POST.get(f'return_qty_{sale_item.product.id}') or '0'
            try:
                quantity = int(quantity_raw)
            except (TypeError, ValueError):
                quantity = 0

            previous_returned = sale_item.return_items.aggregate(total=Sum('quantity'))['total'] or 0
            available = int(sale_item.quantity) - int(previous_returned)
            if quantity <= 0:
                continue
            if quantity > available:
                error_message = f'Cannot return {quantity} units of {sale_item.product.name}. Only {available} are available.'
                break
            return_rows.append((sale_item, quantity, sale_item.unit_price * quantity))

        if error_message:
            selected_sale_items = _build_sale_item_rows(selected_sale)
        elif not return_rows:
            error_message = 'Please select at least one item to return.'
            selected_sale_items = _build_sale_item_rows(selected_sale)
        else:
            refund_total = sum(item[2] for item in return_rows)
            return_transaction = ReturnTransaction.objects.create(
                return_number=f"RET-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                sale=selected_sale,
                processed_by=request.user,
                refund_amount=refund_total,
                refund_method=request.POST.get('refund_method', 'cash'),
                reason=request.POST.get('reason', '') or 'Customer return',
                status='completed',
            )

            for sale_item, quantity, refund_amount in return_rows:
                ReturnItem.objects.create(
                    return_transaction=return_transaction,
                    sale_item=sale_item,
                    quantity=quantity,
                    refund_amount=refund_amount,
                )
                product = sale_item.product
                product.stock_quantity += quantity
                product.save(update_fields=['stock_quantity'])

            success_message = f'Return {return_transaction.return_number} processed successfully. Stock has been restored.'
            selected_sale_items = _build_sale_item_rows(selected_sale)

    else:
        sale_id = request.GET.get('sale_id')
        if sale_id:
            selected_sale = sales.filter(pk=sale_id).first()
        else:
            selected_sale = sales.first()

    if selected_sale and not selected_sale_items:
        selected_sale_items = _build_sale_item_rows(selected_sale)

    context = {
        'sales': sales,
        'selected_sale': selected_sale,
        'selected_sale_items': selected_sale_items,
        'error_message': error_message,
        'success_message': success_message,
        'user': request.user,
    }
    return render(request, 'returns.html', context)
