from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_logout/',views.admin_logout,name='logout'),
    path('admin_dashboard/',views.admin_dashboard,name='admin_dashboard'),
    # path('admin_customer/',views.admin_customer,name='admin_customer'),
    path('toggle_user_status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('customer_search/',views.customer_search,name='customer_search'),
    path('admin_category/',views.admin_category,name='admin_category'),
    path('category_search/',views.category_search,name='category_search'),
    path('admin_editcategory/<int:id>/', views.admin_editcategory, name='admin_editcategory'),
    path('admin_deletecategory/<int:id>/', views.admin_deletecategory, name='admin_deletecategory'),
    path('admin_product/',views.admin_product,name='admin_product'),
    path('product_search/',views.product_search,name='product_search'),
    path('products_add/', views.admin_add_product, name='admin_add_product'),
    # path('resize_and_crop/',views.resize_and_crop,name='resize__and_crop'),
    path('admin_products_edit/<str:product_id>/', views.admin_editproduct, name='admin_edit_product'),
    path('delete_product/<int:id>/', views.admin_deleteproduct, name='admin_deleteproduct'),
    path('admin_order/', views.admin_order, name='admin_order'),
    path('view_admin_order/<int:order_id>/', views.view_admin_order, name='view_admin_order'),
    path('order/update_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin_coupon/', views.admin_coupon, name='admin_coupon'),
    path('admin_edit_coupon/<int:id>/', views.admin_edit_coupon, name='admin_edit_coupon'),
    path('dashboard/coupons/delete/<int:id>/', views.admin_delete_coupon, name='admin_delete_coupon'),
    path('salesreport', views.salesreport, name='salesreport'),
    path('sales-report-data/', views.sales_report_data, name='sales_report_data'),
    path('export-sales-report/', views.export_sales_report, name='export_sales_report'),
    path('export-sales-report/', views.export_sales_report_excel, name='export_sales_report_excel'),

    
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)