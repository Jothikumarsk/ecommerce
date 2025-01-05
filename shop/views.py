
import razorpay
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Cart, Order, Category
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def home(request):
    products = Product.objects.filter(published=True).order_by('-id')[:3]
    return render(request, 'home.html', {'products': products})



def products_list(request):
    # Fetch all products that are published
    products = Product.objects.filter(published=True)
    
    # Search functionality
    query = request.GET.get('search')
    if query:
        products = products.filter(name__icontains=query)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Pagination logic
    paginator = Paginator(products, 9)  # Show 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Fetch all categories for the filter dropdown
    categories = Category.objects.all()
    
    return render(request, 'products_list.html', {'page_obj': page_obj, 'categories': categories})



def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    Cart.objects.create(product=product)
    return redirect('cart')

def cart(request):
    cart_items = Cart.objects.all()
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

def checkout(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        total = sum(item.total_price() for item in Cart.objects.all())  # Total amount

        # Create Razorpay Order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(total * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": 1  # Auto capture payment
        })

        # Save order details temporarily (if needed)
        request.session['order_data'] = {
            'name': name,
            'phone': phone,
            'address': address,
            'total': total,
            'razorpay_order_id': razorpay_order['id'],
        }

        # Send payment details to the template
        return render(request, 'checkout.html', {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': total,
        })
    else:
        return render(request, 'checkout.html')


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        import json
        from razorpay.errors import SignatureVerificationError

        # Parse the JSON data
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify the Razorpay signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Save the order to the database
            order_data = request.session.get('order_data')
            Order.objects.create(
                name=order_data['name'],
                phone=order_data['phone'],
                address=order_data['address'],
                total=order_data['total'],
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
            )

            # Clear the cart
            Cart.objects.all().delete()

            return JsonResponse({'status': 'success', 'message': 'Payment successful!'})
        except SignatureVerificationError:
            return JsonResponse({'status': 'error', 'message': 'Payment verification failed!'})
