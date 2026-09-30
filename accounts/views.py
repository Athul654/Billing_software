from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from products.models import Product
from billing.models import ReturnTransaction
from .models import CustomUser


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            if user.is_superuser or getattr(user, 'role', None) == 'admin':
                return redirect("admin_dashboard")
            else:
                return redirect("staff_dashboard")
        else:
            return render(
                request,
                "accounts/login.html",
                {"error": "Invalid username or password."}
            )

    return render(request, "accounts/login.html")


def admin_dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = Product.objects.filter(is_active=False).count()
    total_stock = Product.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'total_stock': total_stock,
        'recent_products': recent_products,
    }
    return render(request, "accounts/admin.html", context)


def staff_dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, "accounts/staff.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def return_view(request, return_id=None):
    if return_id is not None:
        return_transaction = get_object_or_404(
            ReturnTransaction.objects.select_related(
                'sale',
                'sale__staff',
                'processed_by',
            ).prefetch_related('items__sale_item__product'),
            pk=return_id,
        )
    else:
        return_transaction = ReturnTransaction.objects.select_related(
            'sale',
            'sale__staff',
            'processed_by',
        ).prefetch_related('items__sale_item__product').order_by('-created_at').first()

    if return_transaction is None:
        return render(
            request,
            'accounts/return_view.html',
            {
                'user': request.user,
                'return_transaction': None,
                'return_items': [],
                'is_empty': True,
            }
        )

    return_items = return_transaction.items.select_related('sale_item__product').all()

    context = {
        'user': request.user,
        'return_transaction': return_transaction,
        'return_items': return_items,
        'sale': return_transaction.sale,
        'is_empty': False,
    }
    return render(request, 'accounts/return_view.html', context)


def staff_view(request):
    staff_members = CustomUser.objects.filter(role='staff').order_by('-created_at')
    total_staff = staff_members.count()
    active_staff = staff_members.filter(is_active=True).count()
    inactive_staff = staff_members.filter(is_active=False).count()
    
    context = {
        'staff_members': staff_members,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
    }
    return render(request, "products/staff_view.html", context)


def add_staff_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('fullname', '').split()[0] if request.POST.get('fullname') else ''
        last_name = ' '.join(request.POST.get('fullname', '').split()[1:]) if request.POST.get('fullname') and len(request.POST.get('fullname').split()) > 1 else ''
        phone = request.POST.get('phone', '')
        is_active = request.POST.get('is_active') == 'on'
        
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='staff',
            is_active=is_active
        )
        return redirect('staff_view')
    
    return render(request, "products/add_staff.html")


def edit_staff_view(request, staff_id):
    staff = get_object_or_404(CustomUser, id=staff_id, role='staff')
    
    if request.method == "POST":
        staff.email = request.POST.get('email')
        fullname = request.POST.get('fullname', '')
        if fullname:
            name_parts = fullname.split()
            staff.first_name = name_parts[0]
            staff.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        staff.phone = request.POST.get('phone', '')
        staff.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            staff.set_password(password)
        
        staff.save()
        return redirect('staff_view')
    
    context = {
        'staff': staff,
    }
    return render(request, "products/add_staff.html", context)


def delete_staff_view(request, staff_id):
    staff = get_object_or_404(CustomUser, id=staff_id, role='staff')
    staff.delete()
    return redirect('staff_view')