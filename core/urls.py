from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from core.sitemap import ProductSitemap
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from . import views

sitemaps = {
    'products':ProductSitemap
}

urlpatterns = [
    path("",views.IndexView.as_view(),name="index"),
    path("shop/",views.ShopListView.as_view(),name="shop"),
    path("shop/<slug:pk>/",views.ShopDetailView.as_view(),name="details"),
    path("search/",views.ShopSearch.as_view(),name="search"),
    path("add-to-cart/<slug:id>/",views.AddToCart.as_view(),name="add-to-cart"),
    path("remove-from-cart/<slug:id>/",views.RemoveFromCart.as_view(),name="remove-from-cart"),
    path("add-to-favourite/<slug:id>/",views.ShopFavoriteAddView.as_view(),name="add-to-favourite"),
    path("cart/",views.CartView.as_view(),name="cart"),
    path("favorite/",views.ShopFavoriteListView.as_view(),name="favourite"),
    path("orders/",views.OrdersView.as_view(),name="orders"),
    path("orders/<id>/",views.OrderDetailView.as_view(),name="order-details"),
    path("orders/<order_id>/view-invoice/",views.view_order_invoice,name="order-pdf"),
    path("inbox/",views.InboxListView.as_view(),name="inbox"),
    path("inbox/<pk>/",views.InboxDetailView.as_view(),name="inbox-details"),
    path("account/",views.ProfileView.as_view(),name="account"),
    path("account/fund-wallet/",views.FundWalletView.as_view(),name="fund-wallet"),
    path("account/verify-wallet-transaction/<slug:ref>/",views.verify_wallet_payment,name="verify-wallet-payment"),
    path("account/get-banks/",views.get_banks,name="get-banks"),
    path("account/resolve-account/",views.resolve_account,name="resolve-account"),
    path("account/debit-wallet/",views.DebitWalletView.as_view(),name="debit-wallet"),
    path("checkout/",views.CheckoutView.as_view(),name="checkout"),
    path("verify-transaction/<slug:ref>/",views.verify_payment,name="verify-payment"),
    path("contact-us/",views.ContactFormView.as_view(),name="contact-us"),
    
    # path('test-pdf/',views.test_pdf),
    path('test-csv/',views.test_csv),
    path('generate-image/<int:width>X<int:height>/',views.generate_placeholder,name="placeholder"),
    path('placeholder-example',views.placeholder_generator_view,name="placeholder-example"),

    path("reset-password/",views.PasswordResetView.as_view(),name="reset-password"),
    path("reset-password/<uidb64>/<token>/",views.PasswordResetConfirmView.as_view(),name ="new-password"),
    path("signup/",views.SignUpView.as_view(), name = "signup"),
    path('login/',LoginView.as_view(template_name = "login.html", form_class = LoginForm, success_url = "account/"),name="login"),
    path('logout/',views.LogoutView.as_view(),name="logout"),
    path('sitemap.xml', sitemap, {'sitemaps':sitemaps}, name='django.contrib.sitemaps.views.sitemap')
]
