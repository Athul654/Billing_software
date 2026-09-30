from django.shortcuts import render, redirect, get_object_or_404
from .models import Product


def products_view(request):
    products = Product.objects.all().order_by('-created_at')
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    inactive_products = products.filter(is_active=False).count()
    total_stock = sum(product.stock_quantity for product in products)
    
    context = {
        'products': products,
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'total_stock': total_stock,
    }
    return render(request, "products/products.html", context)


def add_product_view(request):
    if request.method == "POST":
        name = request.POST.get('product_name')
        sku = request.POST.get('sku_code')
        category = request.POST.get('product_category')
        purchase_price = request.POST.get('purchase_price')
        selling_price = request.POST.get('selling_price')
        stock_quantity = request.POST.get('stock_quantity', 0)
        description = request.POST.get('product_description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        Product.objects.create(
            name=name,
            sku=sku,
            purchase_price=purchase_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity,
            description=description,
            is_active=is_active
        )
        return redirect('products')
    
    return render(request, "products/add_product.html")


def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        product.name = request.POST.get('product_name')
        product.sku = request.POST.get('sku_code')
        product.purchase_price = request.POST.get('purchase_price')
        product.selling_price = request.POST.get('selling_price')
        product.stock_quantity = request.POST.get('stock_quantity', 0)
        product.description = request.POST.get('product_description', '')
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()
        return redirect('products')
    
    context = {
        'product': product,
    }
    return render(request, "products/add_product.html", context)


def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('products')
