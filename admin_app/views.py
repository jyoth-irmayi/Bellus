from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from user_app.models import UserDetails
from .models import categorys,Product,Variant,VariantSize,VariantImage,Order,OrderItem,Coupon
import cloudinary, cloudinary.uploader
from PIL import Image
from django.http import JsonResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.contrib.auth import logout
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from util.decorator import admin_required



def admin_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(f"Login attempt for email: {email}")  

        try:
            # Retrieve the user by email
            user = UserDetails.objects.get(email=email)
            print(f"Found user: {user.email}")  

            if check_password(password, user.password):
                print("Password is correct") 
                if user.is_superuser:
                    user.backend = 'django.contrib.auth.backends.ModelBackend' 
                    auth_login(request, user) 
                    return redirect('admin_dashboard')  
                else:
                    messages.error(request, 'You do not have admin access.')
            else:
                print("Password does not match")  
                messages.error(request, 'Invalid email or password.')
        
        except UserDetails.DoesNotExist:
            print("User not found") 
            messages.error(request, 'Invalid email or password.')

    return render(request, 'admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@admin_required
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')
    return render(request, 'admin_dashboard.html')



def toggle_user_status(request, user_id):
    try:
        user = UserDetails.objects.get(user_id=user_id) 
        user.is_active = not user.is_active  # Toggle the status
        user.save()
    except UserDetails.DoesNotExist:
        
        pass

    return redirect('customer_search')


@admin_required
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def customer_search(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        users = UserDetails.objects.filter(
            Q(firstname__icontains=search_query) | Q(lastname__icontains=search_query)
        )
    else:
        users = UserDetails.objects.all()  

    return render(request, 'admin_customer.html', {'users': users})


@login_required
@admin_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def admin_category(request):
     if request.method == 'POST':
        name = request.POST.get('categoryName')
        status = request.POST.get('status') == 'on'
        if categorys.objects.filter(name__iexact=name, is_delete=False).exists():
            messages.error(request, "Category already exists.")
        else:
           
            categorys.objects.create(name=name, is_active=status)
            messages.success(request, "Category added successfully.")
            return redirect('admin_category')  
     categories = categorys.objects.filter(is_delete=False)  
     return render(request, 'admin_category.html', {'categories': categories})


def category_search(request):
    search_query = request.GET.get('search', '')
    print('hi:',search_query)
    if search_query:
        categories = categorys.objects.filter(name__icontains=search_query,is_delete=False) 
        print('category:',categories)
    else:
        categories = categorys.objects.all()
    
    return render(request, 'admin_category.html', {'categories': categories})


def admin_editcategory(request, id):
    # Get the category to edit
    category = get_object_or_404(categorys, id=id)

    if request.method == 'POST':
        # Get the updated data from the POST request
        category_name = request.POST.get('categoryName')
        status = request.POST.get('status') == 'on'  # Checkbox returns 'on' if checked

        if categorys.objects.filter(name__iexact=category_name, is_delete=False).exclude(id=id).exists():
            messages.error(request, "Category already exists.")

        else:
       
            category.name = category_name
            category.is_active = status
            category.save()  # Save changes to the database
            messages.success(request, "Category updated successfully")

      
        return redirect('admin_category')

   
    return render(request, 'admin_editcategory.html', {'category': category})
                                 
                                                                 
def admin_deletecategory(request, id):
    category = get_object_or_404(categorys, id=id)
    if category.is_delete:
        category.is_delete = False  # Un-delete
        category.save()
        return redirect('admin_category')
    
    category.is_delete = True  
    category.save()
    return redirect('admin_category')  


from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
import re  # For regex validation
import cloudinary.uploader  # Ensure Cloudinary is properly configured

@login_required
@admin_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)


def admin_add_product(request):
    if request.method == "POST":
        # Process product-level data (unchanged)
        product_name = request.POST.get("product_name", "").strip()
        price = request.POST.get("price", "").strip()
        category_id = request.POST.get("category", "").strip()
        brand = request.POST.get("brand", "").strip()
        description = request.POST.get("description", "").strip()
        discount = request.POST.get("discount", "0").strip()

        # --- Create Product ---
        try:
            product = Product(
                product_name=product_name,
                price=float(price),
                discount=float(discount),
                brand=brand,
                description=description,
                category_id=category_id,
            )
            product.full_clean()
            product.save()
        except ValidationError as e:
            messages.error(request, f"Validation error: {e.messages}")
            return redirect("admin_add_product")

        # --- Process Variants ---
        variants_data = {}
        for key in request.POST:
            if key.startswith("variants["):
                match = re.match(r"variants\[(\d+)]\[(.+)]", key)
                if match:
                    variant_id, field_name = match.groups()
                    if variant_id not in variants_data:
                        variants_data[variant_id] = {}
                    if field_name == "sizes[]":
                        variants_data[variant_id].setdefault("sizes", []).extend(request.POST.getlist(key))
                    elif "stocks" in field_name:
                        size = field_name.split("[")[1].rstrip("]")
                        variants_data[variant_id].setdefault("stocks", {})[size] = int(request.POST[key])
                    else:
                        variants_data[variant_id][field_name] = request.POST[key]

        # Debug collected data
        print("Debug: Collected variants data -", variants_data)

        # Process each variant
        for variant_id, fields in variants_data.items():
            print(f"Debug: Processing variant {variant_id} - {fields}")
            color = fields.get("color")
            variant_price = fields.get("price")
            sizes = fields.get("sizes][", [])
            stocks = fields.get("stocks", {})
            print(size)
            print(stocks)

            # Create variant
            variant = Variant(product=product, color=color, actual_price=float(variant_price))
            variant.save()

            # Create sizes and stocks
            for size ,stock  in stocks.items():
                variant_size = VariantSize(variant=variant, size=size, quantity=stock)
                variant_size.save()

            # Upload images
            images = request.FILES.getlist(f"variants[{variant_id}][images][]")
            for image in images:
                cloudinary_response = cloudinary.uploader.upload(image)
                VariantImage.objects.create(variant=variant, image=cloudinary_response['secure_url'])


        messages.success(request, "Product and variants added successfully.")
        return redirect("admin_product")

    # Render Add Product Page
    categories = categorys.objects.filter(is_delete=False)
    return render(request, "admin_addproduct.html", {"categories": categories})



@login_required
@admin_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def admin_product(request):
   
     products = Product.objects.filter(is_delete=False).order_by('-created_at')

    # Prepare a list of products with their first variant and image
     products_with_details = []
     for product in products:
        first_variant = product.variants.first()
        firstSize =first_variant.sizes.first()  # Fetch the first variant
        first_image = None
        if first_variant:
            first_image = first_variant.images.first()  # Fetch the first image of the variant
        
        products_with_details.append({
            "product": product,
            "variant": first_variant,
            "image": first_image.image.url if first_image else None,
            "firstSize":firstSize,
        })
     return render(request, 'admin_product.html', {"products_with_details":products_with_details})

def product_search(request):
    search_query = request.GET.get('search', '')
    products = Product.objects.filter(is_delete = False)

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) | 
            Q(category__name__icontains=search_query)
        )
        if not products.exists():
            messages.error(request, 'No products match your search query.')

    # Prepare products with details
    products_with_details = []
    for product in products:
        first_variant = product.variants.first()  # Fetch the first variant
        first_image = None
        if first_variant:
            first_image = first_variant.images.first()  # Fetch the first image of the variant

        products_with_details.append({
            "product": product,
            "variant": first_variant,
            "image": first_image.image.url if first_image else None,
        })

    return render(request, 'admin_product.html', {"products_with_details": products_with_details})


   
from django.core.files.base import ContentFile
import base64
from cloudinary.uploader import upload
from cloudinary.exceptions import Error

@login_required
@admin_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def admin_editproduct(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    categories = categorys.objects.all()
    variants = product.variants.all()
    total_quantity = sum(variant.stock for variant in variants)

    if request.method == "POST":
        # Update product details
        product.product_name = request.POST.get("product_name")
        product.description = request.POST.get("description")
        product.discount = request.POST.get("discount")
        product.brand = request.POST.get("brand")
        product.price = request.POST.get("actual_price")
        category_id = request.POST.get("category")
        product.category = categorys.objects.get(id=category_id)
        product.save()
    
            
        # Process cropped images
        cropped_images = request.POST.getlist("cropped_images[]")
        cropped_image_ids = request.POST.getlist("cropped_image_ids[]")

        for cropped_image_data, image_id in zip(cropped_images, cropped_image_ids):
            try:
                # Decode Base64 image
                format, imgstr = cropped_image_data.split(";base64,")
                decoded_image = BytesIO(base64.b64decode(imgstr))
                
                # Upload to Cloudinary
                upload_result = upload(decoded_image, folder="product_variants/")
                image_url = upload_result.get("secure_url")  # Get the URL of the uploaded image

                # Save the image in the VariantImage model
                image = VariantImage.objects.get(id=image_id)
                image.image = image_url
                image.save()

            except Error as e:
                print(f"Cloudinary upload failed: {e}")
            except Exception as ex:
                print(f"Error processing image for variant {image_id}: {ex}")

        # Continue with other updates
        # Update existing variants and images as in your original code.
        
        for variant in variants:
            # Update existing images
            existing_image_ids = request.POST.getlist(f"variant_{variant.id}_existing_images")
            new_images = request.FILES.getlist(f"variant_{variant.id}_new_images")

            # Delete images not in the list of existing images
            VariantImage.objects.filter(variant=variant).exclude(id__in=existing_image_ids).delete()

            # Replace existing images if new images are uploaded
            for image_id in existing_image_ids:
                new_image = request.FILES.get(f"variant_{variant.id}_replace_image_{image_id}")
                if new_image:
                    variant_image = VariantImage.objects.get(id=image_id, variant=variant)
                    variant_image.image = new_image
                    variant_image.save()

            # Add new images to the variant
            for new_image_file in new_images:
                VariantImage.objects.create(variant=variant, image=new_image_file)


        # Handle variant deletion
        variants_to_delete = request.POST.getlist("delete_variants[]")
        for variant_id in variants_to_delete:
            variant = Variant.objects.filter(id=variant_id, product=product).first()
            if variant:
                variant.images.all().delete()  # Delete associated images
                variant.delete()

        # Update existing variants
        for variant in variants:
            size = request.POST.get(f"variant_{variant.id}_size")
            color = request.POST.get(f"variant_{variant.id}_color")
            price = request.POST.get(f"variant_{variant.id}_price")
            stock = request.POST.get(f"variant_{variant.id}_stock")
            variant.size = size
            variant.color = color
            variant.price = price
            variant.stock = stock
            variant.save()

            # Update existing variant images
            existing_image_ids = request.POST.getlist(f"variant_{variant.id}_existing_images")
            if existing_image_ids:
             # Remove images not selected in the existing images list
                VariantImage.objects.filter(variant=variant).exclude(id__in=existing_image_ids).delete()

            # Add new images for this variant
            variant_images = request.FILES.getlist(f"variant_{variant.id}_images")
            for image_file in variant_images:
                VariantImage.objects.create(variant=variant, image=image_file)


        # Add new variants
        new_sizes = request.POST.getlist("new_variant_size[]")
        new_colors = request.POST.getlist("new_variant_color[]")
        new_stocks = request.POST.getlist("new_variant_stock[]")
        new_prices = request.POST.getlist("new_variant_price[]")

        for i in range(len(new_sizes)):
            new_variant = Variant.objects.create(
                product=product,
                size=new_sizes[i],
                color=new_colors[i],
                stock=new_stocks[i],
                price=new_prices[i],
            )
            # Dynamically access the corresponding file input for this variant
            image_field_name = f"new_variant_images_{i}[]"
            variant_image_files = request.FILES.getlist(image_field_name)


            if not variant_image_files:
                messages.error(request, f"No images uploaded for variant {new_sizes[i]} ({new_colors[i]}).")
                continue  # Skip to the next variant

            # Save each image for this variant
            for index, image_file in enumerate(variant_image_files):
                # Upload the image to Cloudinary
                cloudinary_response = cloudinary.uploader.upload(
                    image_file,
                    folder=f"product_images/{product.id}/variants/{new_variant.id}/",
                    public_id=f"{new_variant.id:03d}_{index + 1:03d}",
                    overwrite=False,
                    format="webp",
                    quality=85
                )
                cloudinary_url = cloudinary_response['secure_url']

                    # Save the image URL to VariantImage model
                VariantImage.objects.create(variant=new_variant, image=cloudinary_url)

        # Handle variant deletion
        variants_to_delete = request.POST.getlist("delete_variants[]")  # Get the IDs of variants to delete
        for variant_id in variants_to_delete:
            variant = Variant.objects.filter(id=variant_id, product=product).first()  # Find the variant
            if variant:
                variant.images.all().delete()  # Delete associated images
                variant.delete()  # Delete the variant

    return render(request, "admin_editproduct.html", {
        "product": product,
        "categories": categories,
        "total_quantity": total_quantity,
        "variants": variants,
    })



# @login_required
# @admin_required
# @cache_control(no_cache=True, no_store=True, must_revalidate=True)
# def admin_editproduct(request, product_id):
#     product = get_object_or_404(Product, product_id=product_id)
#     categories = categorys.objects.all()
#     variants = product.variants.all()
#     total_quantity = sum(variant.stock for variant in variants)

#     if request.method == "POST":
#         # Validate product details
#         product_name = request.POST.get("product_name")
#         if not product_name:
#             messages.error(request, "Product name is required.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         description = request.POST.get("description")
#         if not description:
#             messages.error(request, "Product description is required.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         try:
#             discount = float(request.POST.get("discount") or 0)
#             if discount < 0 or discount > 100:
#                 raise ValueError
#         except ValueError:
#             messages.error(request, "Discount must be a percentage between 0 and 100.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         brand = request.POST.get("brand")
#         if not brand:
#             messages.error(request, "Brand is required.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         try:
#             price = float(request.POST.get("actual_price"))
#             if price <= 0:
#                 raise ValueError
#         except ValueError:
#             messages.error(request, "Price must be a positive number.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         category_id = request.POST.get("category")
#         if not category_id or not categorys.objects.filter(id=category_id).exists():
#             messages.error(request, "Invalid category selected.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         # Update product details
#         product.product_name = product_name
#         product.description = description
#         product.discount = discount
#         product.brand = brand
#         product.price = price
#         product.category = categorys.objects.get(id=category_id)
#         product.save()

#         # Validate and process cropped images
#         cropped_images = request.POST.getlist("cropped_images[]")
#         cropped_image_ids = request.POST.getlist("cropped_image_ids[]")
#         if len(cropped_images) != len(cropped_image_ids):
#             messages.error(request, "Mismatch in image and ID count.")
#             return render(request, "admin_editproduct.html", {
#                 "product": product, "categories": categories, 
#                 "total_quantity": total_quantity, "variants": variants,
#             })

#         for cropped_image_data, image_id in zip(cropped_images, cropped_image_ids):
#             try:
#                 # Decode and upload image
#                 format, imgstr = cropped_image_data.split(";base64,")
#                 decoded_image = BytesIO(base64.b64decode(imgstr))
#                 upload_result = upload(decoded_image, folder="product_variants/")
#                 image_url = upload_result.get("secure_url")
#                 image = VariantImage.objects.get(id=image_id)
#                 image.image = image_url
#                 image.save()
#             except Exception as ex:
#                 messages.error(request, f"Error processing image for variant {image_id}: {ex}")

#         # Handle variant validation and updates
#         for variant in variants:
#             size = request.POST.get(f"variant_{variant.id}_size")
#             color = request.POST.get(f"variant_{variant.id}_color")
#             try:
#                 price = float(request.POST.get(f"variant_{variant.id}_price"))
#                 stock = int(request.POST.get(f"variant_{variant.id}_stock"))
#                 if stock < 0:
#                     raise ValueError
#             except ValueError:
#                 messages.error(request, f"Invalid price or stock for variant ID {variant.id}.")
#                 continue

#             variant.size = size
#             variant.color = color
#             variant.price = price
#             variant.stock = stock
#             variant.save()

#         # Add new variants with validation
#         new_sizes = request.POST.getlist("new_variant_size[]")
#         new_colors = request.POST.getlist("new_variant_color[]")
#         new_stocks = request.POST.getlist("new_variant_stock[]")
#         new_prices = request.POST.getlist("new_variant_price[]")
#         for i in range(len(new_sizes)):
#             try:
#                 size = new_sizes[i]
#                 color = new_colors[i]
#                 stock = int(new_stocks[i])
#                 price = float(new_prices[i])
#                 if stock < 0 or price <= 0:
#                     raise ValueError
#             except ValueError:
#                 messages.error(request, f"Invalid data for new variant {size} ({color}).")
#                 continue

#             new_variant = Variant.objects.create(
#                 product=product, size=size, color=color, stock=stock, price=price
#             )
#             variant_image_files = request.FILES.getlist(f"new_variant_images_{i}[]")
#             if not variant_image_files:
#                 messages.error(request, f"No images uploaded for variant {size} ({color}).")
#                 continue
#             for image_file in variant_image_files:
#                 VariantImage.objects.create(variant=new_variant, image=image_file)

#     return render(request, "admin_editproduct.html", {
#         "product": product,
#         "categories": categories,
#         "total_quantity": total_quantity,
#         "variants": variants,
#     })




def admin_deleteproduct(request,id):
    product = get_object_or_404(Product, id=id)
    product.is_delete = True  # Mark as deleted
    product.save()
    return redirect('admin_product')


def admin_order(requst):
    """Fetch and list all orders in the admin view."""
    orders = Order.objects.prefetch_related('order_items__variant__product', 'user', 'address').all()

    # order_data = []
    # for order in orders:
    #     items = order.order_items.all()
    #     total = sum(item.total_price for item in items)  # Using total_price property from OrderItem

        # order_data.append({
        #     'order_id': order.id,
        #     'user_email': order.user.email,
        #     'address': order.address,  # Assuming address has a readable __str__ method
        #     'order_date': order.order_date,
        #     'status': order.status,
        #     'payment_method': order.payment_method,
        #     'total': total,
        #     'is_paid': order.is_paid,
        #     'is_delivered': order.is_delivered,
        # })

    context = {'orders': orders}
    return render(requst,'week2/admin_order.html', context)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def view_admin_order(request, order_id):
    """View and update statuses for individual items in an order."""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.select_related('variant', 'variant__product')

    # Handle the status update form submission for individual items
    if request.method == 'POST':
        for item in order_items:
            new_status = request.POST.get(f'order_status_{item.id}')
            if new_status in dict(OrderItem.ORDER_STATUS_CHOICES).keys():
                item.status = new_status
                item.save()

    # Add images to each order item (not just the primary image)
    for item in order_items:
        # Fetch all images for the variant
        item.variant_images = item.variant.images.all()

    # Pagination for order items
    paginator = Paginator(order_items, 5)  # Show 5 items per page
    page_number = request.GET.get('page')
    try:
        paginated_order_items = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_order_items = paginator.page(1)
    except EmptyPage:
        paginated_order_items = paginator.page(paginator.num_pages)

    context = {
        'order': order,
        'paginated_order_items': paginated_order_items,
        'customer_name': f"{order.user.firstname} {order.user.lastname}",
        'customer_email': order.user.email,
        'customer_phone': order.user.phone,
        'total_amount': order.total_amount,
        'order_time': order.order_date,
        'delivery_date': order.delivery_date,
    }

    return render(request, 'week2/view_admin_order.html', context)


def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Handle the form submission to update the status of each order item
    if request.method == 'POST':
        # Handle status update for each order item individually
        for item in order.order_items.all():
            new_status = request.POST.get(f'order_status_{item.id}')
            if new_status in dict(OrderItem.ORDER_STATUS_CHOICES).keys():
                item.status = new_status
                item.save()

    return redirect('view_admin_order', order_id=order.id)

def admin_coupon(request):
    if request.method == 'POST':
        # Get data from POST request
        coupon_name = request.POST.get('couponName')
        coupon_code = request.POST.get('couponCode')
        coupon_condition = request.POST.get('couponCondition')
        offer_rate = request.POST.get('offerRate')
        coupon_validity = request.POST.get('couponValidity')
        discount_type = request.POST.get('discountType')
        discount_value = request.POST.get('discountValue')
        max_uses = request.POST.get('maxUses')

        # Ensure offer_rate is converted to a decimal
        try:
            offer_rate = float(offer_rate)
        except ValueError:
            offer_rate = 0.0  # Default value in case of invalid input

        # Use discount_type to assign discount_value properly
        if discount_type == 'percentage':
            discount_value = offer_rate  # percentage
        elif discount_type == 'fixed':
            discount_value = float(discount_value)  # fixed value

        # Save coupon to the database
        coupon = Coupon(
            name=coupon_name,
            code=coupon_code,
            condition=coupon_condition,
            offer_rate=offer_rate,
            validity_date=coupon_validity,
            discount_value=discount_value,
            max_uses=max_uses
        )
        coupon.save()

        # Return a JSON response indicating success
        return JsonResponse({'status': 'success', 'message': 'Coupon added successfully!'})
    
    # If the request method is not POST, return the form page
    context = {'coupons': Coupon.objects.all()}
    return render(request, 'week3/admin_coupon.html', context)

def admin_edit_coupon(request,id):
    coupon = get_object_or_404(Coupon, id=id)

    if request.method == 'POST':
        # Get data from the form
        coupon.name = request.POST.get('couponName')
        coupon.code = request.POST.get('couponCode')
        coupon.condition = request.POST.get('couponCondition')
        coupon.offer_rate = request.POST.get('offerRate')
        coupon.discount_type = request.POST.get('discountType')
        coupon.discount_value = request.POST.get('discountValue')
        coupon.validity_date = request.POST.get('couponValidity')
        coupon.max_uses = request.POST.get('maxUses')

        # Save the updated coupon
        coupon.save()

        # Show success message
        messages.success(request, "Coupon updated successfully.")
        return redirect('admin_coupon')
    return render(request, 'week3/admin_edit_coupon.html',{'coupon': coupon})



def admin_delete_coupon(request, id):
    if request.method == 'POST':
        # Fetch the coupon by ID
        coupon = get_object_or_404(Coupon, id=id)
        # Delete the coupon
        coupon.delete()
        # Redirect to the coupon list page
        return redirect('admin_coupon')  

from django.db.models import Sum, Avg, Count,F
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from datetime import datetime
import logging
from datetime import date

logger = logging.getLogger(__name__)

def salesreport(request):
    """
    Fetch data for the sales report page and render the template.
    """

    today = date.today().strftime('%Y-%m-%d')
    # Fetch total sales (sum of total amount from orders)
    total_sales = Order.objects.filter(is_paid=True).aggregate(
        total_sales=Sum('total_amount')
    )['total_sales'] or 0

    
    # Fetch total orders (count of paid orders)
    total_orders = Order.objects.filter(is_paid=True).count()

    # Fetch average order value
    avg_order_value = Order.objects.filter(is_paid=True).aggregate(
        avg_order_value=Sum('total_amount') / Count('id')
    )['avg_order_value'] or 0

    # Fetch conversion rate (number of paid orders divided by total orders)
    total_visits = 1000  # Example value for total site visits, replace with actual count if available
    conversion_rate = (total_orders / total_visits) * 100 if total_visits > 0 else 0

    # Get all orders initially for rendering
    orders = Order.objects.all().prefetch_related('order_items__variant__product', 'order_items__variant__product__category')

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'conversion_rate': conversion_rate,
        'orders': orders,
        'today': today

    }
    return render(request, 'week3/salesreport.html', context)



from django.db.models import Sum, Count, F, Case, When, IntegerField
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models import Prefetch
from .models import Order, OrderItem, Product
def sales_report_data(request):
    # Get filter parameters from the GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category = request.GET.getlist('category')  # Multiple categories
    status = request.GET.getlist('status')  # Multiple statuses
    date_filter = request.GET.get('date_filter', 'day')

    # Initialize queryset for orders
    queryset = Order.objects.all()

    # Apply date range filter if provided
    if start_date and end_date:
        queryset = queryset.filter(order_date__range=[start_date, end_date])

    # Apply category filter if provided (excluding 'all')
    if 'all' not in category and category:
        queryset = queryset.filter(order_items__variant__product__category__name__in=category)

    # Apply status filter if provided (excluding 'all')
    if 'all' not in status and status:
        queryset = queryset.filter(order_items__status__in=status)

    # Apply date grouping based on the selected filter
    if date_filter == 'day':
        queryset = queryset.annotate(grouped_date=TruncDay('order_date'))
    elif date_filter == 'month':
        queryset = queryset.annotate(grouped_date=TruncMonth('order_date'))
    elif date_filter == 'year':
        queryset = queryset.annotate(grouped_date=TruncYear('order_date'))

    # Calculate the total number of products sold (delivered only), total price, and sales breakdown
    queryset = queryset.annotate(
        total_products_sold=Sum(Case(
            When(order_items__status='delivered', then=F('order_items__quantity')),
            default=0,
            output_field=IntegerField()
        )),
        total_price=Sum(F('order_items__quantity') * F('order_items__price')),
        
        returned_products=Sum(Case(
            When(order_items__status='returned', then=F('order_items__quantity')),
            default=0,
            output_field=IntegerField()
        )),
        canceled_products=Sum(Case(
            When(order_items__status='canceled', then=F('order_items__quantity')),
            default=0,
            output_field=IntegerField()
        )),
        
        total_orders=Count('id'),
        
        # Count delivered products and calculate sales accordingly
        delivered_products=Sum(Case(
            When(order_items__status='delivered', then=F('order_items__quantity')),
            default=0,
            output_field=IntegerField()
        ))
    )

    # Calculate actual sales (total sales - returns and cancellations)
    queryset = queryset.annotate(
        actual_sales=F('total_price') - F('returned_products') - F('canceled_products')
    )

    # Calculate total sales, total products sold, and total orders across all results
    total_sales = queryset.aggregate(Sum('actual_sales'))['actual_sales__sum'] or 0
    total_orders = queryset.aggregate(Count('id'))['id__count'] or 0
    total_products_sold = queryset.aggregate(Sum('delivered_products'))['delivered_products__sum'] or 0

    # Prepare the context for rendering
    context = {
        'sales_data': queryset,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products_sold': total_products_sold,
        'start_date': start_date,
        'end_date': end_date,
        'category': category,
        'status': status,
        'date_filter': date_filter,
    }

    return render(request, 'week3/salesreport.html', context)


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse
from .models import Order, OrderItem

def export_sales_report(request):
    # Retrieve filter parameters from the GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category = request.GET.getlist('category')  # Multiple categories
    status = request.GET.getlist('status')  # Multiple statuses

    # Initialize queryset for orders
    queryset = Order.objects.all()

    # Apply date range filter if provided
    if start_date and end_date:
        queryset = queryset.filter(order_date__range=[start_date, end_date])

    # Apply category filter if provided (excluding 'all')
    if 'all' not in category and category:
        queryset = queryset.filter(order_items__variant__product__category__name__in=category)

    # Apply status filter if provided (excluding 'all')
    if 'all' not in status and status:
        queryset = queryset.filter(order_items__status__in=status)

    # If queryset is empty, return a message
    if not queryset.exists():
        return HttpResponse("No data found for the given filters.", content_type="text/plain")

    # Prepare response as PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Define table data
    data = [
        ["Order ID", "Order Date", "Customer Name", "Customer Email", "Product Name", "Price", "Status"]
    ]

    # Populate table data
    for order in queryset:
        for order_item in order.order_items.all():
            variant = order_item.variant
            product = variant.product
            customer_name = f"{order.user.firstname} {order.user.lastname}"
            customer_email = order.user.email
            order_id = order.id
            order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S')
            product_name = product.product_name
            price = order_item.total_price  # Total price for the order item
            status = order_item.status

            data.append([order_id, order_date, customer_name, customer_email, product_name, price, status])

    # Create the table
    table = Table(data)

    # Define table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SIZE', (0, 0), (-1, -1), 8),
    ])
    table.setStyle(style)

    # Add table to elements
    elements.append(table)

    # Build the PDF
    doc.build(elements)

    return response

import pandas as pd
from django.http import HttpResponse
from .models import Order, OrderItem, Variant, Product  # Import your models

def export_sales_report_excel(request):
    # Fetch the data
    orders = Order.objects.all()
    data = []

    for order in orders:
        for order_item in order.order_items.all():
            variant = order_item.variant
            product = variant.product
            customer_name = f"{order.user.first_name} {order.user.last_name}"
            customer_email = order.user.email
            order_id = order.id
            order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S')
            product_name = product.product_name
            price = order_item.total_price  # Ensure this property is defined in your OrderItem model
            status = order_item.status

            data.append({
                'Order ID': order_id,
                'Order Date': order_date,
                'Customer Name': customer_name,
                'Customer Email': customer_email,
                'Product Name': product_name,
                'Price': price,
                'Status': status,
            })

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create the HTTP response with Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    # Write the DataFrame to the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response
