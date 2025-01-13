
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import logout, login
from django.core.mail import send_mail
from django.utils import timezone
from django.http import HttpResponseNotFound
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.conf import settings
import random
from datetime import timedelta
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from .models import UserDetails,Address,Wishlist,Wallet,Transaction
from admin_app.models import Product,Review,Cart,CartItem,Variant,VariantImage,categorys,Order,OrderItem, Coupon
from django.contrib.auth import get_backends
from .forms import UserLoginForm
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

def user_signup(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname',"").strip()
        lastname = request.POST.get('lastname',"").strip()
        phone = request.POST.get('phone',"").strip()
        email = request.POST.get('email',"").strip()
        password = request.POST.get('password',"").strip()
        re_password = request.POST.get('re_password',"").strip()


        if not firstname.isalpha() or len(firstname) < 2:
            messages.error(request, "First name must contain at least 2 alphabetic characters and no spaces, numbers, or special characters.")
            return redirect("user_signup")


        # Check if the phone number contains only digits
        if not phone.isdigit():
            messages.error(request,"Phone number must contain only digits.")
            return redirect('user_signup')
        
        # Check if the phone number is at least 10 digits
        if len(phone) < 10:
            messages.error(request,"Phone number must be at least 10 digits long.")
            return redirect('user_signup')
        
        # Check for empty or space-only fields
        if not firstname or not lastname or not phone or not email or not password or not re_password:
            messages.error(request, 'All fields are required. Please fill in all fields.')
            return redirect('user_signup')

        if password != re_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_signup')

        if UserDetails.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('user_signup')
        
        # Validate email format
        validator = EmailValidator()
        try:
            validator(email)  # This will raise a ValidationError if the email format is wrong
        except ValidationError:
            messages.error(request, 'Invalid email format. Please enter a valid email address.')
            return redirect('user_signup')

     
        user_data = {
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'phone': phone,
            'password': password,
        }
        request.session['user_data'] = user_data

        # Generate OTP and save user details in session
        otp = random.randint(100000, 999999)
        print(otp)
        otp_creation_time = timezone.now()

        request.session['otp'] = otp
        request.session['otp_creation_time'] = otp_creation_time.isoformat()

        # Send OTP email
        subject = "Your OTP Code"
        message = f"Your OTP code is {otp}. It is valid for 10 minutes."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        messages.success(request, 'Signup successfully. Please check your email for the OTP.')
        return redirect('user_otp')

    return render(request, 'signup.html')


def user_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp',"").strip()

        # Get the user data from session
        user_data = request.session.get('user_data')
        email = user_data['email']
        print('hi',email)
        if not user_data:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect('user_signup')

        if email != user_data.get('email'):
            messages.error(request, "Invalid email.")
            return redirect('user_otp')

        # Verify OTP within a time limit (10 minutes)
        otp_creation_time_str = request.session.get('otp_creation_time')
        if not otp_creation_time_str:
            messages.error(request, "OTP session expired. Please request a new OTP.")
            return redirect('user_signup')

        try:
            otp_creation_time = datetime.fromisoformat(otp_creation_time_str)
        except ValueError:
            messages.error(request, "Invalid OTP creation time.")
            return redirect('user_signup')

        current_time = timezone.now()
        time_diff = current_time - otp_creation_time
        otp_valid_duration = timedelta(minutes=2)

        if time_diff > otp_valid_duration:
            messages.error(request, "OTP expired. Please request a new OTP.")
            return redirect('user_signup')

        # Check if OTP matches
        if str(request.session.get('otp')) == entered_otp:
            # Create the user after OTP validation
            user = UserDetails.objects.create(
                firstname=user_data.get('firstname'),
                lastname=user_data.get('lastname'),
                email=user_data.get('email'),
                phone=user_data.get('phone'),
            )
            user.set_password(user_data.get('password'))
            user.is_active = True  # Mark the user as active
            user.save()

            # Clean up session data
            request.session.flush()

            messages.success(request, "OTP verified! You are now registered and logged in.")
            return redirect('user_login')  # Redirect to the login page or dashboard
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'otp.html')



def resend_otp(request):
    # Check if user session exists
    user_data = request.session.get('user_data')
    if user_data:
        # Generate and resend OTP
        otp = random.randint(100000, 999999)
        print('otp',otp)
        otp_creation_time = timezone.now().isoformat()

        request.session['otp'] = otp
        request.session['otp_creation_time'] = otp_creation_time

        # Send OTP email
        subject = "Your OTP Code"
        message = f"Your OTP code is {otp}. It is valid for 10 minutes."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user_data['email']]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        messages.success(request, 'A new OTP has been sent to your email.')
    else:
        messages.error(request, 'Session expired. Please sign up again.')

    return redirect('user_otp')



@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def user_login(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == "POST":
        form = UserLoginForm(request.POST)


        # Get the email from the form (assuming the form includes an email field)
        email = request.POST.get('email')

        # Validate email format before proceeding with form validation
        validator = EmailValidator()
        try:
            validator(email)  # This will raise a ValidationError if the email format is wrong
        except ValidationError:
            messages.error(request, "Invalid email format. Please enter a valid email address.")
            return render(request, "login.html", {"form": form})
        

        if form.is_valid():
            user = form.cleaned_data['user']
            user = UserDetails.objects.get(email=email)
            if not user.is_active:
                messages.error(request, 'Account blocked, contact support.')
                return redirect('user_login')
            # Log the user in
            backend = 'django.contrib.auth.backends.ModelBackend'
            user.backend = backend
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect('homepage')  # Adjust this to your desired redirect URL
        else:
            # Form errors are already handled by the form
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserLoginForm()

    return render(request, "login.html", {"form": form})




from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
def user_recovary(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip()

        # Validate email format
        if not email:
            messages.error(request, 'Email field cannot be empty.')
            return redirect('user_recovary')

        try:
            user = UserDetails.objects.get(email=email)
        except UserDetails.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('user_recovary')

        if user.is_blocked:
            messages.error(request, 'Your account is blocked. Please contact support.')
            return redirect('user_recovary')

        # Generate OTP
        otp = random.randint(100000, 999999)
        print(otp)
        otp_creation_time = timezone.now()

        # Save OTP and creation time to session
        request.session['otp'] = otp
        request.session['otp_creation_time'] = otp_creation_time.isoformat()
        request.session['reset_email'] = email  # Store the email for later use

        # Send OTP to user's email
        subject = "Password Reset OTP"
        message = f"Your OTP code is {otp}. It is valid for 10 minutes."
        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [email], fail_silently=False)

        messages.success(request, 'An OTP has been sent to your email address.')
        return redirect('verify_otp')

    return render(request,'recovary.html')



def recovary_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp').strip()
        email = request.session.get('reset_email')

        # Verify OTP session exists
        if not email:
            messages.error(request, "Session expired. Please request OTP again.")
            return redirect('user_recovary')
        
        try:
            user = UserDetails.objects.get(email=email)
        except UserDetails.DoesNotExist:
            messages.error(request, "Invalid user.")
            return redirect('user_recovary')


        otp_creation_time_str = request.session.get('otp_creation_time')
        if not otp_creation_time_str:
            messages.error(request, "OTP session expired. Please request a new OTP.")
            return redirect('user_recovary')

        try:
            otp_creation_time = datetime.fromisoformat(otp_creation_time_str)
        except ValueError:
            messages.error(request, "Invalid OTP creation time.")
            return redirect('user_recovary')

        current_time = timezone.now()
        time_diff = current_time - otp_creation_time
        otp_valid_duration = timedelta(minutes=10)  # OTP validity: 10 minutes

        # Check if OTP has expired
        if time_diff > otp_valid_duration:
            messages.error(request, "OTP expired. Please request a new OTP.")
            return redirect('user_recovary')

        # Check if entered OTP matches session OTP
        if str(request.session.get('otp')) == entered_otp:
            return redirect('reset_password')  # OTP verified, allow password reset
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'verify_otp.html')


from django.contrib.auth.hashers import make_password

def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password','').strip()
        confirm_password = request.POST.get('confirm_password','').strip()
        email = request.session.get('email')

        # Validate passwords
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password')

        # if len(new_password) < 6:
        #     messages.error(request, 'Password must be at least 6 characters long.')
        #     return redirect('reset_password')

        email = request.session.get('reset_email')
        if not email:
            messages.error(request, 'Session expired. Please request OTP again.')
            return redirect('user_recovary')

         # Update the user's password
        try:
            user = UserDetails.objects.get(email=email)
        except UserDetails.DoesNotExist:
            messages.error(request, "Invalid user.")
            return redirect('')

        user.set_password(new_password)
        user.otp = None  # Clear OTP after successful password reset
        user.otp_created_at = timezone.now()
        user.save()

        # Clean up session data
        request.session.flush()

        messages.success(request, 'Your password has been reset successfully.')
        return redirect('user_login')

    return render(request, 'reset_password.html')


@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def homepage(request):
    # Fetch the two most recently added products
    recent_products = Product.objects.filter(is_delete=False).order_by('-created_at')[:8]
    products_with_images = []

    for product in recent_products:
        first_variant = product.variants.first()  # Get the first variant
        first_image = None
        if first_variant:
            # Get primary image or the first image
            first_image = (
                first_variant.images.filter(is_primary=True).first() or
                first_variant.images.first()
            )
        products_with_images.append({
            "product": product,
            "image": first_image.image.url if first_image else None,
            "discount_price": first_variant.price if first_variant else product.price,
            "actual_price": product.price,
            'discount':product.discount
        })
    
    # Pass products to the template
    return render(request, 'homepage.html', {'products_with_images': products_with_images})





def user_logout(request):
    logout(request)  # Logs out the user
    messages.success(request, 'Logout successfully')
    return redirect('user_login')

 # Replace with your actual model imports


@login_required
@login_required
def product_detail(request, product_id):
    # Fetch the product
    product = get_object_or_404(Product.objects.prefetch_related('variants__images'), id=product_id)
    variants_with_size = product.variants.exclude(size__isnull=True, size='')

    # Get the variant from the query parameters (uses default id field)
    variant_id = request.GET.get('variant_id')
    if variant_id:
        try:
            selected_variant = product.variants.get(id=variant_id)
        except Variant.DoesNotExist:
            return HttpResponseNotFound("Variant not found")
    else:
        selected_variant = product.variants.first()

    # Check if the selected variant is in the wishlist
    is_in_wishlist = Wishlist.objects.filter(user=request.user, variant=selected_variant.id).exists()

    # Gather images for the selected variant
    images = selected_variant.images.all() if selected_variant else []

    # Prepare related variants (exclude the current variant)
    related_variants = []
    for variant in product.variants.exclude(id=selected_variant.id if selected_variant else None):
        primary_image = variant.images.filter(is_primary=True).first() or variant.images.first()
        if primary_image:
            related_variants.append({
                'variant': variant,
                'image': primary_image.image.url,
            })

    # Fetch related products including their variants from the same category
    related_products_with_variants = Product.objects.filter(
        Q(category=product.category) & Q(is_delete=False)
    ).exclude(id=product.id)

    related_products = []
    for related_product in related_products_with_variants:
        variants = related_product.variants.all()
        for variant in variants:
            primary_image = variant.images.filter(is_primary=True).first() or variant.images.first()
            if primary_image:
                related_products.append({
                    'product': related_product,
                    'variant': variant,
                    'image': primary_image.image.url,
                    'actual_price': related_product.price,
                    'discount': related_product.discount,
                    'discounted_price': variant.price,
                })

    context = {
        'product': product,
        'selected_variant': selected_variant,
        'images': images,
        'related_variants': related_variants,
        'variants_with_size': variants_with_size,
        'selected_variant_price': selected_variant.price,
        'related_products': related_products,
        'is_in_wishlist': is_in_wishlist,
    }
    return render(request, 'product_display.html', context)




def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        
        # Ensure the user is logged in before submitting a review
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to submit a review.")
            return redirect('login')  # Redirect to login if not logged in

        # Create a new review
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            review_text=comment
        )
        
        messages.success(request, "Your review has been submitted successfully!")
        return redirect('product_detail', product_id=product.id)  # Redirect to product detail page

    return redirect('product_detail', product_id=product.id)





from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def user_profile(request):
    # Ensure the user is authenticated
    if request.user.is_authenticated:
        # Fetch the profile of the currently logged-in user using email
        profile = get_object_or_404(UserDetails, email=request.user.email)
    if request.method == 'POST':
        firstname=request.POST.get('firstname',"").strip()
        lastname=request.POST.get('lastname','').strip()
        phone=request.POST.get('phone','').strip()
        email = request.POST.get('email')
        
        if email != profile.email:
            messages.error(request, "You cannot change the email address.")
            return redirect('user_profile')

        if not firstname.strip() or not lastname.strip():
            messages.error(request, "First name and last name cannot be empty.")
            return redirect('user_profile')
        
        if len(phone) != 10 or not phone.isdigit():
            messages.error(request, "Phone number cannot be empty and must be 10 digits.")
            return redirect('user_profile')

        profile.firstname=firstname
        profile.lastname=lastname
        profile.phone=phone
        profile.save()
        return redirect ('user_profile')
    
    return render(request, 'week2/profile.html', {'profile': profile})
    
from django.core.validators import RegexValidator



@login_required
def user_address(request):  
    user = request.user
    addresses = Address.objects.filter(user=user)  
    fullname = f"{user.firstname} {user.lastname}".strip()

    edit_address = None
    edit_id = request.GET.get('edit')
    if edit_id:
        edit_address = get_object_or_404(Address, id=edit_id, user=user)

    if request.method == 'POST':
        # # Enforce 3-address limit for new addresses
        # if addresses.count() >= 3 and not edit_address:
        #     messages.error(request, "You can only add a maximum of 3 addresses.")
        #     return redirect('user_address')

        # Collect form data
        name = request.POST.get('name', "").strip()
        phone_number = request.POST.get('phone', "").strip()
        address_line = request.POST.get('address', "").strip()
        location = request.POST.get('location', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        address_type = request.POST.get('addressType', "").strip()

        # Check required fields
        if not all([name, phone_number, address_line, city, pincode, address_type]):
            messages.error(request,"All required fields must be filled.")
            return redirect('user_address')

        # Maximum length validations
        if len(name) > 15:
            messages.error(request,"Name cannot exceed 15 characters.")
            return redirect('user_address')
        if len(phone_number) > 10:
            messages.error(request,"Phone number must be exactly 10 digits.")
            return redirect('user_address')
        if len(address_line) > 100:
            messages.error(request,"Address line cannot exceed 100 characters.")
            return redirect('user_address')
        if len(location) > 25:
            messages.error(request,"Location cannot exceed 20 characters.")
            return redirect('user_address')
        if len(landmark) > 25:
            messages.error(request,"Landmark cannot exceed 25 characters.")
            return redirect('user_address')
        if len(city) > 25:
            messages.error(request,"City name cannot exceed 25 characters.")
            return redirect('user_address')
        if len(district) > 20:
            messages.error(request,"District name cannot exceed 20 characters.")
            return redirect('user_address')
        if len(state) > 20:
            messages.error(request,"State name cannot exceed 20 characters.")
            return redirect('user_address')
        if len(pincode) != 6:
            messages.error(request,"Pincode must be exactly 6 digits.")
            return redirect('user_address')
        if len(address_type) > 20:
            messages.error(request,"Address type cannot exceed 20 characters.")
            return redirect('user_address')

        # Numeric validations
        if not phone_number.isdigit():
            messages.error(request,"Phone number must contain only digits.")
            return redirect('user_address')
        if not pincode.isdigit():
            messages.error(request,"Pincode must contain only digits.")
            return redirect('user_address')


        # Save or update the address
        if edit_address:
            edit_address.name = name
            edit_address.phone_number = phone_number
            edit_address.address_line = address_line
            edit_address.location = location
            edit_address.landmark = landmark
            edit_address.city = city
            edit_address.district = district
            edit_address.state = state
            edit_address.pincode = pincode
            edit_address.address_type = address_type
            edit_address.save()
            messages.success(request, "Address updated successfully.")
        else:
            Address.objects.create(
                user=user,
                name=name,
                phone_number=phone_number,
                address_line=address_line,
                location=location,
                landmark=landmark,
                city=city,
                district=district,
                state=state,
                pincode=pincode,
                address_type=address_type,
            )
            messages.success(request, "Address added successfully.")

        return redirect('user_address')

    return render(request, 'week2/address.html', {'addresses': addresses, 'edit_address': edit_address, 'fullname': fullname})




@login_required
def edit_address(request, address_id):
    user_address = get_object_or_404(Address, id=address_id, user=request.user)
    fullname = f"{request.user.firstname} {request.user.lastname}".strip()
    if request.method == 'POST':
        name = request.POST.get('name', "").strip()
        phone_number = request.POST.get('phone', "").strip()
        address_line = request.POST.get('address', "").strip()
        location = request.POST.get('location', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        address_type = request.POST.get('addressType', '').strip()
    
        user_address.name = name
        user_address.phone_number = phone_number
        user_address.address_line = address_line
        user_address.location = location
        user_address.landmark = landmark
        user_address.city = city
        user_address.district = district
        user_address.state = state
        user_address.pincode = pincode
        user_address.address_type = address_type
        user_address.save()
        messages.success(request, 'Address updated...')
        return redirect ('user_address')

    # data = {
    #     'user_address': user_address,
    # }
    return render (request, 'week2/edit_address.html', {'user_address':user_address, 'fullname': fullname,})


# def delete_address(request, address_id):
#     address = get_object_or_404(Address, id=address_id)
#     if address.is_delete:
#         address.is_delete = False  # Un-delete
#         address.save()
#         return redirect('user_address')
    
#     address.is_delete = True  
#     address.save()
#     return redirect('user_address')


def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    address.is_delete = not address.is_delete  # Toggle the delete status
    address.save()
    return redirect('user_address')




@login_required
@login_required
def add_to_cart(request, product_id):
    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        
        if not variant_id:
            return JsonResponse({"success": False, "message": "No variant selected"}, status=400)

        variant = Variant.objects.filter(product_id=product_id, id=variant_id).first()

        if not variant:
            return JsonResponse({"success": False, "message": "Variant not found"}, status=404)

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

        if cart_item:
            # Check stock and max quantity constraints
            if cart_item.quantity >= variant.stock:
                return JsonResponse({"success": False, "message": "Stock limit reached"}, status=400)
            if cart_item.quantity >= 5:
                return JsonResponse({"success": False, "message": "Maximum quantity per product is 5"}, status=400)

            # Increment the quantity
            cart_item.quantity += 1
            cart_item.save()
            return JsonResponse({"success": True, "message": "Product quantity updated in cart"})

        # Set default discount if not provided
        discount = getattr(variant, 'discount', 0)

        # Add new cart item
        if variant.stock > 0:
            cart_item = CartItem.objects.create(
                cart=cart,
                variant=variant,
                price=variant.price,
                discount=discount,
                quantity=1
            )
            return JsonResponse({"success": True, "message": "Product added to cart!"})
        else:
            return JsonResponse({"success": False, "message": "Out of stock"}, status=400)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)




from decimal import Decimal
@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_amount = Decimal(0)
    total_discount = Decimal(0)

    for item in cart_items:
        # Ensure all calculations are done with Decimal
        item_total = Decimal(item.price) * Decimal(item.quantity)
        discount_value = item_total * (Decimal(item.discount) / Decimal(100))
        total_amount += item_total
        total_discount += discount_value

    # Tax calculation (10% of total amount)
    tax = total_amount * Decimal('0.10')

    # Grand total calculation
    grand_total = total_amount + tax
    
    # for item in cart_items:
    #     # Fetch the product associated with the variant in the cart item
    #     product = item.variant.product

    #     # Calculate the original price without discount
    #     original_price = item.quantity * product.price

    #     # Calculate the discount amount for this item (product discount applied)
    #     discount_amount = (product.discount / Decimal(100)) * original_price

    #     # Add to the total price after discount
    #     total_amount += original_price - discount_amount

    #     # Add to the total discount
    #     total_discount += discount_amount
    
    # Example tax and shipping calculations
    # tax = total_amount * Decimal('0.10')
    # grand_total = total_amount + tax - total_discount
    
    context = {
        "cart": cart,
        "cart_items": cart_items,
        "total": total_amount,
        'total_discount': total_discount,
        "tax": tax,
        "grand_total": grand_total,
    }
    
    return render(request, "week2/cart.html", context)



import json
from django.http import JsonResponse

@login_required
@login_required
@login_required
@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        quantity = data.get('quantity')

        cart_item = CartItem.objects.get(id=item_id)

        # Check if the requested quantity exceeds the stock
        if quantity > cart_item.variant.stock:
            return JsonResponse({'success': False, 'message': f'Cannot increase quantity above stock. Only {cart_item.variant.stock} items available.'})
        
        # Max quantity allowed (5)
        if quantity > 5:
            return JsonResponse({'success': False, 'message': 'You cannot have more than 5 items of the same product in the cart.'})

        # Update the quantity
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})





@login_required
def delete_cart_item(request, item_id):
    if request.method == "POST":
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            return JsonResponse({"success": True, "message": "Item successfully deleted from cart."})
        except CartItem.DoesNotExist:
            return JsonResponse({"success": False, "message": "CartItem not found."}, status=404)
    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)





from django.db.models import Q
@login_required
def shop(request):
    # Get all categories and brands
    categories = categorys.objects.filter(is_active=True, is_delete=False)
    brands = Product.objects.values_list('brand', flat=True).distinct()

    # Get filter and sort values from GET request
    selected_category = request.GET.get('category')
    selected_brand = request.GET.get('brand')
    selected_price_range = request.GET.get('price_range')
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort_by')

    # Filter products based on the selected filters
    products = Product.objects.filter(is_active=True, is_delete=False)

    if selected_category:
        products = products.filter(category__id=selected_category)

    if selected_brand:
        products = products.filter(brand=selected_brand)

    # Price Range Filtering
    if selected_price_range:
        if selected_price_range == "0-100":
            products = products.filter(price__gte=0, price__lte=100)
        elif selected_price_range == "100-200":
            products = products.filter(price__gte=100, price__lte=200)
        elif selected_price_range == "200+":
            products = products.filter(price__gte=200)

    # Search products if search query is provided
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Sorting options
    if sort_by == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-price')
    elif sort_by == 'name_a_to_z':
        products = products.order_by('product_name')
    elif sort_by == 'name_z_to_a':
        products = products.order_by('-product_name')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')

    # Prepare products with images
    products_with_images = []
    for product in products:
        first_variant = product.variants.first()  # Get the first variant
        first_image = None
        if first_variant:
            first_image = (
                first_variant.images.filter(is_primary=True).first() or
                first_variant.images.first()
            )  # Get primary image or the first image
        products_with_images.append({
            "product": product,
            "image": first_image.image.url if first_image else None,
        })

    context = {
        'products_with_images': products_with_images,
        'categories': categories,
        'brands': brands,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'selected_price_range': selected_price_range,
        'search_query': search_query,
        'sort_by': sort_by,
    }

    return render(request, 'week2/shop.html', context)


from decimal import Decimal

def checkout_address(request):
    user = request.user
    addresses = Address.objects.filter(user=user, is_delete=False)  # Fetch user's addresses
    if request.method == 'POST':
        address_id = request.POST.get('address')  # Get the selected address ID
        if address_id:
            address = Address.objects.get(id=address_id, user=user)
            request.session['selected_address'] = address.id  # Store selected address in session
            return redirect('order_summary')  # Redirect to order summary page

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_amount = Decimal(0)

    # Calculate total amount using the variant price
    for item in cart_items:
        # Fetch the price directly from the variant table
        variant_price = Decimal(item.variant.price)  # Assuming 'price' is a field in the Variant table
        item_total = variant_price * Decimal(item.quantity)  # Calculate total price for the item
        total_amount += item_total  # Add to the total amount

    # Tax calculation (10% of total amount)
    tax = total_amount * Decimal('0.10')

    # Grand total calculation (total amount + tax)
    grand_total = total_amount + tax
    
    context = {
        'addresses': addresses,
        "cart": cart,
        "cart_items": cart_items,
        "total": total_amount,
        "tax": tax,
        "grand_total": grand_total,
    }

    return render(request, 'week2/checkout_address.html', context)





@login_required
def add_address_checkout(request):  
    user = request.user
    addresses = Address.objects.filter(user=user)  
     # Get the user's full name
    fullname = f"{user.firstname} {user.lastname}".strip()

    edit_address = None
    edit_id = request.GET.get('edit') 
    print('edit ',edit_id)
    if edit_id:
        edit_address = get_object_or_404(Address, id=edit_id, user=user)

    if request.method == 'POST':
        name = request.POST.get('name', "").strip()
        phone_number = request.POST.get('phone', "").strip()
        address_line = request.POST.get('address', "").strip()
        location = request.POST.get('location', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        address_type = request.POST.get('addressType', "").strip()

        # Check required fields
        if not all([name, phone_number, address_line, city, pincode, address_type]):
            messages.error(request,"All required fields must be filled.")
            return redirect('checkout_address')

        # Maximum length validations
        if len(name) > 15:
            messages.error(request,"Name cannot exceed 15 characters.")
            return redirect('checkout_address')
        if len(phone_number) > 10:
            messages.error(request,"Phone number must be exactly 10 digits.")
            return redirect('checkout_address')
        if len(address_line) > 100:
            messages.error(request,"Address line cannot exceed 100 characters.")
            return redirect('checkout_address')
        if len(location) > 25:
            messages.error(request,"Location cannot exceed 20 characters.")
            return redirect('checkout_address')
        if len(landmark) > 25:
            messages.error(request,"Landmark cannot exceed 25 characters.")
            return redirect('checkout_address')
        if len(city) > 25:
            messages.error(request,"City name cannot exceed 25 characters.")
            return redirect('checkout_address')
        if len(district) > 20:
            messages.error(request,"District name cannot exceed 20 characters.")
            return redirect('checkout_address')
        if len(state) > 20:
            messages.error(request,"State name cannot exceed 20 characters.")
            return redirect('checkout_address')
        if len(pincode) != 6:
            messages.error(request,"Pincode must be exactly 6 digits.")
            return redirect('checkout_address')
        if len(address_type) > 20:
            messages.error(request,"Address type cannot exceed 20 characters.")
            return redirect('checkout_address')

        # Numeric validations
        if not phone_number.isdigit():
            messages.error(request,"Phone number must contain only digits.")
            return redirect('checkout_address')
        if not pincode.isdigit():
            messages.error(request,"Pincode must contain only digits.")
            return redirect('checkout_address')


        # Save or update the address
        if edit_address:
            edit_address.name = name
            edit_address.phone_number = phone_number
            edit_address.address_line = address_line
            edit_address.location = location
            edit_address.landmark = landmark
            edit_address.city = city
            edit_address.district = district
            edit_address.state = state
            edit_address.pincode = pincode
            edit_address.address_type = address_type
            edit_address.save()
            messages.success(request, "Address updated successfully.")
        else:
            Address.objects.create(
                user=user,
                name=name,
                phone_number=phone_number,
                address_line=address_line,
                location=location,
                landmark=landmark,
                city=city,
                district=district,
                state=state,
                pincode=pincode,
                address_type=address_type,
            )
            messages.success(request, "Address added successfully.")


    return render(request, 'week2/checkout_address.html', {'addresses': addresses, 'edit_address': edit_address, 'fullname': fullname})





def select_address(request):
    user_addresses = Address.objects.filter(user=request.user, is_delete=False)
    
    if request.method == 'POST':
        address_id = request.POST.get('address')
        address = Address.objects.get(id=address_id, user=request.user)
        request.session['selected_address'] = address.id  # Store selected address in session
        return redirect('order_summary')
    
    return render(request, 'checkout/select_address.html', {'addresses': user_addresses})






from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
import razorpay
from django.utils.timezone import now

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def order_summary(request):
   
    # Get or create the cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    # **Update**: Calculate total amount using the variant price
    total_amount = sum(
        Decimal(item.variant.price) * Decimal(item.quantity) for item in cart_items
    )
    
    # Fetch applied coupon
    applied_coupon = cart.coupon if cart.coupon else None
    coupon_discount = Decimal(0)

    # **Update**: Check and calculate coupon discount
    if applied_coupon and applied_coupon.is_valid():
        if applied_coupon.discount_type == 'percentage':
            coupon_discount = total_amount * (applied_coupon.discount_value / Decimal(100))
        else:  # Fixed amount discount
            coupon_discount = applied_coupon.discount_value

        # Ensure the discount does not exceed the total amount
        coupon_discount = min(coupon_discount, total_amount)
        total_amount -= coupon_discount  # Deduct the coupon discount from the total amount
        cart.total_discount = coupon_discount  # **Update**: Save the discount to the cart
        cart.save()
    else:
        cart.total_discount = Decimal(0)  # **Update**: Reset the discount if no valid coupon
        cart.save()

    # Tax calculation (10% of the discounted amount)
    tax = total_amount * Decimal('0.10')

    # Grand total calculation (discounted amount + tax)
    grand_total = total_amount + tax

    # Fetch all active, non-deleted, and valid coupons
    coupons = Coupon.objects.filter(
        is_active=True,
        is_delete=False,
        validity_date__gte=now(),
    )

    # Dynamically filter coupons based on their conditions
    available_coupons = []
    for coupon in coupons:
        try:
            if coupon.condition:
                condition = coupon.condition
                context = {"total_amount": float(total_amount)}

                # Use eval safely
                if eval(condition, {"__builtins__": None}, context):
                    available_coupons.append(coupon)
            else:
                # If no condition is specified, consider it valid
                available_coupons.append(coupon)
        except Exception as e:
            logger.error(f"Error evaluating coupon {coupon.code}: {e}")

    # Check for selected address
    selected_address_id = request.session.get('selected_address')
    if not selected_address_id:
        return redirect('checkout_address')

    selected_address = Address.objects.get(id=selected_address_id, user=request.user)
    wallet = get_object_or_404(Wallet, user=request.user)
    order = None  # Initialize the order variable

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cod')

        # Handle wallet payment
        if payment_method == 'wallet':
            if wallet.balance >= grand_total:
                with transaction.atomic():
                    wallet.balance -= grand_total
                    wallet.save()

                    # Create a transaction record for the wallet deduction
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=grand_total,
                        transaction_type='debit',
                        description=f"Payment for order placed by {request.user.email}",
                    )

                    # Create the order and order items
                    order = Order.objects.create(
                        user=request.user,
                        address=selected_address,
                        payment_method='wallet',
                        total_amount=grand_total,
                        is_paid=True,
                    )

                    for item in cart_items:

                        # Reduce stock quantity
                        variant = item.variant
                        if variant.stock >= item.quantity:
                            variant.stock -= item.quantity
                            variant.save()
                        else:
                            messages.error(request, f"Insufficient stock for {variant.name}.")
                            return redirect('order_summary')
                        
                        OrderItem.objects.create(
                            order=order,
                            variant=item.variant,
                            quantity=item.quantity,
                            price=item.variant.price,
                        )

                    # Clear the cart items after the order is placed
                    cart_items.delete()

                    messages.success(request, "Order placed successfully using wallet balance!")
                    return redirect('order_success')

            else:
                messages.error(request, "Insufficient wallet balance. Please choose another payment method.")

        # Handle Razorpay payment
        elif payment_method == 'razorpay':
            print(payment_method)
            # Create Razorpay order
            amount_in_paisa = int(grand_total * 100)  # Amount in paisa
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            razorpay_order = None
            try:
                razorpay_order = razorpay_client.order.create({
                    "amount": amount_in_paisa,
                    "currency": "INR",
                    "payment_capture": "1"
                })
                print("Razorpay order created:", razorpay_order)
            except Exception as e:
                print("Error creating Razorpay order:", e)
                messages.error(request, "An error occurred while processing your payment. Please try again.")
                return redirect('order_summary')

            if not razorpay_order:
                print("Razorpay order creation failed.")
                messages.error(request, "Payment processing failed. Please try again later.")
                return redirect('order_summary')


            # Create the order with Razorpay payment method
            order = Order.objects.create(
                user=request.user,
                address=selected_address,
                payment_method='razorpay',
                total_amount=grand_total,
                is_paid=False,
                # razorpay_order_id=razorpay_order["id"]
            )

            # Create the order items
            for item in cart_items:

                # Reduce stock quantity
                variant = item.variant
                if variant.stock >= item.quantity:
                    variant.stock -= item.quantity
                    variant.save()
                else:
                    messages.error(request, f"Insufficient stock for {variant.name}.")
                    return redirect('order_summary')
                
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                )

            # Clear the cart items after the order is placed
            cart_items.delete()

            # Pass Razorpay order ID to the frontend
            context = {
                'razorpay_order_id': razorpay_order["id"],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'total': total_amount,
                'coupon_discount': coupon_discount,
                'tax': tax,
                'grand_total': grand_total,
                'selected_address': selected_address,
                'coupon': cart.coupon,
                'available_coupons': available_coupons,
                'wallet': wallet,
                'order': order,
            }

            return render(request, 'week2/razorpay.html', context)


        # Handle other payment methods (e.g., COD)
        else:
            with transaction.atomic():
                # Create the order
                order = Order.objects.create(
                    user=request.user,
                    address=selected_address,
                    payment_method=payment_method,
                    total_amount=grand_total,
                    is_paid=False,
                )

                # Create the order items
                for item in cart_items:

                    # Reduce stock quantity
                    variant = item.variant
                    if variant.stock >= item.quantity:
                        variant.stock -= item.quantity
                        variant.save()
                    else:
                        messages.error(request, f"Insufficient stock for {variant.name}.")
                        return redirect('order_summary')

                    OrderItem.objects.create(
                        order=order,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.variant.price,
                    )

                # Clear the cart items after the order is placed
                cart_items.delete()

                messages.success(request, 'Your order has been placed successfully!')
                return redirect('order_success')

    # Pass the order object to the context
    context = {
        'cart_items': cart_items,
        'total': total_amount,
        'coupon_discount': coupon_discount,  # **Update**: Include the calculated discount
        'tax': tax,
        'grand_total': grand_total,
        'selected_address': selected_address,
        'coupon': cart.coupon,
        'available_coupons': available_coupons,
        'wallet': wallet,
        'order': order,
    }

    return render(request, 'week2/order_summary.html', context)





from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
import json

def razorpay_payment_success(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Verify payment signature
            Utility.verify_payment_signature({
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "razorpay_signature": data["razorpay_signature"]
            })

            # Payment is successful
            # Perform any additional logic here, such as updating order status in the database

            # Redirect to a success page
            return redirect('payment_success')  # Replace with your success page URL name
        except Exception as e:
            # Payment verification failed
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    # Handle non-POST requests
    return JsonResponse({"error": "Invalid request"}, status=400)




# import razorpay
# def create_payment_order(amount):
#     client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#     data = {
#         'amount': amount * 100,  # Amount in paise
#         'currency': 'INR',
#         'payment_capture': '1',
#     }
#     response = client.order.create(data=data)
#     return response['id']


# def payment_view(request):
#     if request.method == 'POST':
#         payment_method = request.POST.get('payment_method')
#         if payment_method == 'razorpay':
#             amount = 100  # Set the amount dynamically or based on your requirements
#             order_id = create_payment_order(amount)
#             context = {
#                 'order_id': order_id,
#                 'amount': amount
#             }
#             return render(request, 'payment.html', context)
#         else:
#             # Handle other payment methods
#             pass
#     else:
#         return render(request, 'order_summary.html')
    

def payment_success(request):

    return render(request, 'payment_success.html')


from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect
import logging

# Initialize logger
logger = logging.getLogger(__name__)

@login_required
def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get('coupon_code', '').strip()

        try:
            # Fetch the coupon and validate its status
            coupon = Coupon.objects.get(code=coupon_code, is_active=True, is_delete=False)

            # Check if the coupon is valid using the `is_valid()` method
            if not coupon.is_valid():
                messages.error(request, "This coupon is expired or has reached its maximum usage.")
                return redirect('order_summary')

            # Fetch the user's cart
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Check if the coupon meets the minimum purchase requirement (if any)
            cart_total = sum(item.variant.price * item.quantity for item in CartItem.objects.filter(cart=cart))
            if cart_total < coupon.offer_rate:
                messages.error(request, f"This coupon requires a minimum purchase of ₹{coupon.offer_rate}.")
                return redirect('order_summary')

            # Apply the coupon to the cart
            cart.coupon = coupon  # **Updated: Save coupon to cart**
            cart.save()

            # Update the coupon's usage count
            coupon.used_count += 1
            coupon.save()

            # Recalculate the total discount after applying the coupon
            total_discount = cart.calculate_discount()  # Assuming `calculate_discount()` is a method in your Cart model
            cart.total_discount = total_discount
            cart.save()

            messages.success(request, f"Coupon '{coupon.code}' applied successfully! Discount: ₹{coupon.discount_value}")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon code.")
        except Exception as e:
            logger.error(f"Error applying coupon: {e}")  # **Updated: Added logging for coupon application errors**
            messages.error(request, "An error occurred while applying the coupon. Please try again.")
    
    return redirect('order_summary')



def order_success(request):
    return render(request, 'week2/order_success.html')





from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def user_order_items(request):
    orders_list = Order.objects.filter(user=request.user).prefetch_related('order_items__variant__product').order_by('-order_date')
    fullname = f"{request.user.firstname} {request.user.lastname}".strip()


    # Pagination
    paginator = Paginator(orders_list, 5)  # Show 5 orders per page
    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        orders = paginator.page(paginator.num_pages)


    context = {
        'orders': orders,
        'fullname': fullname,
    }
    return render(request, 'week2/order_item.html', context)



@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    if order_item.status not in ['delivered', 'canceled']:
        order_item.status = 'canceled'
        order_item.save()

        variant = order_item.variant
        variant.stock = F('stock') + order_item.quantity  # Use F expression for atomic update
        variant.save()
        variant.refresh_from_db()

        messages.success(request, "Order item canceled successfully.")
    else:
        messages.error(request, "Order item cannot be canceled.")
    return redirect('user_order_items')




from django.contrib import messages

from django.db.models import F  # Make sure to import F

@login_required
def return_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if order_item.status == 'delivered':
        # Update the order item status to 'returned'
        order_item.status = 'returned'
        order_item.save()

        variant = order_item.variant
        variant.stock = F('stock') + order_item.quantity  # Use F expression for atomic update
        variant.save()

        variant.refresh_from_db()


        # Get the wallet of the user
        wallet = Wallet.objects.get(user=request.user)

        # Update the wallet balance using F expression (atomically)
        wallet.balance = F('balance') + order_item.total_price
        wallet.save()

        # Refresh the wallet object to get the updated balance in memory
        wallet.refresh_from_db()

        # Create a transaction record for the refund (credit)
        Transaction.objects.create(
            wallet=wallet,
            amount=order_item.total_price,
            transaction_type='credit',  # Refund is a credit
            description=f"Refund for Order Item {order_item.id}"
        )

        messages.success(request, "Your order has been returned, and the amount has been added to your wallet.")
    else:
        messages.error(request, "Only delivered orders can be returned.")
    
    return redirect('user_order_items')




@login_required
def wallet_view(request):
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    fullname = f"{user.firstname} {user.lastname}".strip()

    if created:
        messages.success(request, "Your wallet has been created!")
    
    transactions = wallet.transactions.order_by('-date')

    context = {
        'wallet': wallet,
        'transactions': transactions,
        'fullname': fullname
    }
    return render(request, 'week3/user_wallet.html', context)



@login_required
def add_to_wallet(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount'))
            if amount > 0:
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance = F('balance') + amount
                wallet.save()
                wallet.refresh_from_db()  # To get the updated balance
                
                # Add a transaction record
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='credit',
                    description="User added funds"
                )
                return JsonResponse({'success': True, 'new_balance': wallet.balance})
            else:
                return JsonResponse({'success': False, 'error': "Amount should be greater than 0."})
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'success': False, 'error': "Invalid amount."})
    return JsonResponse({'success': False, 'error': "Invalid request method."})



@login_required
def use_wallet_balance(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if wallet.balance >= order_item.total_price:
        wallet.balance = F('balance') - order_item.total_price
        wallet.save()
        
        # Add a transaction record
        Transaction.objects.create(
            wallet=wallet,
            amount=-order_item.total_price,
            transaction_type='debit',
            description=f"Payment for order item {order_item.id}"
        )
        
        order_item.status = 'paid'
        order_item.save()
        messages.success(request, "Payment successful using wallet balance.")
    else:
        messages.error(request, "Insufficient funds in wallet.")
    return redirect('user_order_items')


from django.shortcuts import redirect
from django.contrib import messages

def process_wallet_payment(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')  # Retrieve the order_id from the form submission
        grand_total = request.POST.get('grand_total')

        try:
            order = Order.objects.get(id=order_id)  # Fetch the order using the order_id
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('order_not_found')  # Handle order not found error

        user = request.user  # Get the logged-in user

        # Check if the user has enough wallet balance
        if user.wallet_balance >= float(grand_total):
            user.wallet_balance -= float(grand_total)  # Deduct the wallet balance
            user.save()

            order.status = 'Paid'  # Update the order status
            order.save()

            messages.success(request, "Payment successful through wallet!")
            return redirect('order_success')  # Redirect to success page
        else:
            messages.error(request, "Insufficient wallet balance!")
            return redirect('order_summary', order_id=order.id)  # Redirect back to the order summary page
    else:
        return redirect('order_summary')  # Handle invalid request method
    


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction

@login_required
def place_order(request):
    # Get the user's wallet and cart details (assuming cart items are passed)
    wallet = Wallet.objects.get(user=request.user)
    
    # Simulate order items, this could be from the user's cart
    order_items = [
        {'product_name': 'Product 1', 'total_price': 100, 'quantity': 1},
        {'product_name': 'Product 2', 'total_price': 150, 'quantity': 2},
    ]
    
    # Calculate order total
    order_total = sum(item['total_price'] for item in order_items)

    # Check if the user has enough wallet balance
    if wallet.balance >= order_total:
        # Process the payment: reduce the wallet balance and create the order
        with transaction.atomic():
            wallet.balance -= order_total
            wallet.save()
            order = Order.objects.create(user=request.user, total_amount=order_total)
            
            # You could add order items to an OrderItem model if needed
            for item in order_items:
                # Assuming you have an OrderItem model to store order details
                pass  # Add order items here
            
            return JsonResponse({'success': True, 'new_balance': wallet.balance, 'order_id': order.id})
    
    else:
        return JsonResponse({'success': False, 'error': 'Insufficient funds'})

#     # Fetch the order based on the order_id (ensure it's for the logged-in user)
#     order = Order.objects.get(id=order_id, user=request.user)
    
#     # Fetch the order items related to this order
#     order_items = OrderItem.objects.filter(order=order)
    
#     # Calculate total price for the order
#     total = sum(item.total_price for item in order_items)
#     total_discount = sum(item.variant.product.discount * item.quantity for item in order_items)

#     # Example tax and grand total
#     tax = total * 0.10  # 10% tax
#     grand_total = total + tax
    
#     context = {
#         'order': order,
#         'order_items': order_items,
#         'total': total,
#         'total_discount': total_discount,
#         'tax': tax,
#         'grand_total': grand_total,
#     }

#     return render(request, 'week2/order_item.html', context)


@login_required
def wishlist_view(request):
    user = request.user
    fullname = f"{request.user.first_name} {request.user.last_name}".strip()
    
    # Fetch wishlist items with related variants, products, and images
    wishlist_items = Wishlist.objects.filter(user=user).select_related('variant__product').prefetch_related('variant__images').order_by('-added_at')
    
    wishlist_with_images = []
    for item in wishlist_items:
        variant = item.variant
        # Use .first() to handle cases where there are no images for the variant
        first_image = variant.images.first() if variant.images.exists() else None
        wishlist_with_images.append({'wishlist_item': item, 'image': first_image})
    
    return render(request, 'week3/wishlist.html', {'wishlist_items': wishlist_with_images, 'fullname': fullname})



@login_required
def add_to_wishlist(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id)
    
    # Ensure the variant is only added once per user
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, variant=variant)
    
    # You may want to redirect back to the product detail page after adding to the wishlist
    return redirect('product_detail', product_id=variant.product.id)

@login_required
def remove_from_wishlist(request,id):
    """View to remove a product from the user's wishlist."""
    variant = get_object_or_404(Variant, id=id)
    Wishlist.objects.filter(user=request.user, variant=variant).delete() 
    return redirect('product_detail',product_id=variant.product.id)
