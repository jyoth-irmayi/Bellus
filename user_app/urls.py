from django.urls import path,include
from . import views

urlpatterns = [
    path('user_login/',views.user_login,name='user_login'),
    path('user_signup/',views. user_signup,name='user_signup'),
    path('user_recovary/',views.user_recovary,name='user_recovary'),
    path('verify-otp/', views.recovary_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('user_otp/',views.user_otp,name='user_otp'),
    path('user_logout/',views.user_logout,name='user_logout'),
    path('resend_otp/',views.resend_otp,name='resend_otp'),
    path('',views.homepage,name='homepage'),
    path('product_detail/<int:product_id>/',views.product_detail,name='product_detail'),
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('user_address/', views.user_address, name='user_address'),  # Add new address
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:address_id>/',views.delete_address,name='delete_address'),
    path("cart_view/", views.cart_view, name="cart_view"),
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('delete-cart-item/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path("shop/", views.shop, name="shop"),
    path("checkout_address/", views.checkout_address, name="checkout_address"),
    path("add_address_checkout/", views.add_address_checkout, name="add_address_checkout"),
    path("order_summary/", views.order_summary, name="order_summary"),
    path('order_summary/<int:order_id>/', views.order_summary, name='order_summary_with_id'),
    path("order_success/", views.order_success, name="order_success"),
    path('user_orders/', views.user_order_items, name='user_order_items'),
    path('order-item/<int:item_id>/cancel/', views.cancel_order_item, name='cancel_order_item'),
    path('order-item/<int:item_id>/return/', views.return_order_item, name='return_order_item'),
    # path('order_item/<int:order_id>/', views.order_item, name='order_it')
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:id>/' ,views.remove_from_wishlist, name='remove_from_wishlist'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    # path('payment/', views.payment_view, name='payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('wallet/', views.wallet_view, name='user_wallet'),
    path('razorpay/payment/success/', views.razorpay_callback, name='razorpay_payment_success'),
    path('wallet/add/', views.add_to_wallet, name='add_to_wallet'),
    path('order-item/<int:order_item_id>/pay-with-wallet/', views.use_wallet_balance, name='pay_with_wallet'),
    path('process-wallet-payment/', views.process_wallet_payment, name='process_wallet_payment'),
    path('place-order/', views.place_order, name='place_order'),


]
