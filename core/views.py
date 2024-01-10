from typing import Any, Dict
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect,get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import FileResponse, HttpRequest, HttpResponse,HttpResponseNotFound, HttpResponseBadRequest, Http404, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
from django.views.generic import FormView, View, ListView, DetailView
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login,logout, authenticate
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST



import csv
import io
import weasyprint
# from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw
from io import BytesIO
# import requests
from decimal import Decimal


from .models import Product, Review, Favourite,Order,Transaction,User, Wallet, Address, WalletTransaction, Inbox
from .filters import ProductFilter, session_filter_pack
from .cart import Cart
from .payment import Paystack
from .forms import ImageForm, SearchForm, ReviewForm, ContactForm, CheckoutForm, UserCreationForm
from .recommender import Recommender
from .tasks import order_created


# Create your views here.

# def test_pdf(request):
#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer)

#     p.drawString(100,100,"Hello Wold")

#     p.showPage()
#     p.save()

#     buffer.seek(0)
#     return FileResponse(buffer,as_attachment=True,filename="text-pdf.pdf")



# Install 'markdown' to use markdown


def test_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(response)
    writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response

def placeholder(width, height):
    image = Image.new('RGB',(width,height))

    draw = ImageDraw.Draw(image)
    text = "{} x {}".format(width,height)
    textwidth, textheight = draw.textsize(text)
    draw.text((((width - textwidth) // 2 ),((height - textheight) // 2)),text,(255,255,255))

    content = BytesIO()
    image.save(content,"PNG")
    content.seek(0)
    return content

def generate_placeholder(request, width, height):
    form = ImageForm({"width": width,"height":height})
    if form.is_valid():
        content = placeholder(form.cleaned_data['width'],form.cleaned_data['height'])
        return HttpResponse(content,content_type = "image/png")
    else:
        return HttpResponseBadRequest("Invalid Image Request")

def placeholder_generator_view(request):
    example = reverse('placeholder',kwargs={'width':500,'height':500})
    context = {'example':request.build_absolute_uri(example)}
    response =  render(request,"pl-example.html",context)
    return response

def search(request):
    form = SearchForm(request.GET)
    if not form.valid():
        return HttpResponseBadRequest("Invalid Query")
    query = form.cleaned_data['query']
    search_vector = SearchVector('name','description')
    search_query = SearchQuery(query)

    results = Product.objects.active().annotate(search = search_vector, rank = SearchRank(search_vector,search_query))\
    .filter(search = search_query).order_by('-rank')

    return render(request,'search.html',{
        'results':results,
        'query':query,
    })


# Eccommerce Start

# Home Page View - /
class IndexView(View):
    def get(self,request):
        recent_products = Product.objects.all().order_by("-created")[:12]
        most_purchased = Product.objects.annotate(num_orders = Count("order_items",filter=Q(order_items__order__paid= True)))[:12]
        context = {
            "recent_products": recent_products,
            "featured_products": most_purchased,
        }

        return render(request,"index.html", context)

# Shop page view - /shop/
class ShopListView(ListView):
    template_name = "shop.html"
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if not "filters" in self.request.session:
            self.request.session['filters'] = session_filter_pack
        return super().get(request, *args, **kwargs)
    def get_queryset(self):
        sorting_options={'recent':self.sort_recent,'mp':self.sort_most_popular,
                        'rating':self.sort_best_rating
                        }
        queryset = Product.objects.active()
        filter = ProductFilter(self.request.GET, queryset = queryset)
        filter_qs = filter.qs
        sort_params = self.request.GET.get("sort")
        
        if sort_params and sort_params in sorting_options:
            self.request.session['filters']['sort_by'] = sort_params
            filter_qs = sorting_options[sort_params](filter_qs)
        
        return filter_qs

    def get_paginate_by(self, queryset):
        showing = self.request.GET.get("showing")
        if showing and showing.isnumeric():
            self.request.session['filters']['page_size'] = int(showing)
            num_of_items = int(showing)
        else:
            num_of_items = self.request.session['filters']['page_size']
        return num_of_items
    def sort_most_popular(self,queryset):
        return queryset.annotate(
            reviews_count = Count("reviews")
            ).order_by("-reviews_count")
        
    def sort_recent(self,queryset):
        return queryset.order_by("-created")
    def sort_best_rating(self,queryset):
        return queryset
    

class ShopDetailView(DetailView):
    model = Product
    template_name = "detail.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.get_object()
        recommendation = Recommender()
        recommended_products = recommendation.suggest_products_for([object],4)
        context['recommendation'] = list(set(recommended_products))

        # related post
        category = object.tags.all()
        print(category)
        same_category_product =  Product.objects.filter(tags__in = category).exclude(id = object.id)
        context['category_products'] = list(set(same_category_product))
        return context
    

class ShopSearch(ListView):
    template_name = "search.html"
    paginate_by = 12
    context_object_name = "products"
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if not "search" in self.request.GET:
            return redirect("shop")
        return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET['search']
        return context
    def get_queryset(self):
        search = self.request.GET['search']
        print(search)
        filter = ProductFilter({'search':search})
        return filter.qs

class ShopReviewCreateView(LoginRequiredMixin,FormView):
    http_method_names = ['post']
    model = Review
    form_class  = ReviewForm
    def form_valid(self, form):
        return super().form_valid(form)
    
class ShopFavoriteListView(LoginRequiredMixin, ListView):
    model = Favourite
    template_name = "favourite.html"
    def get_paginate_by(self, queryset):
        showing = self.request.GET.get("showing")
        if showing and showing.isnumeric():
            num_of_items = int(showing)
        else:
            num_of_items = 12
        return num_of_items
    def get_queryset(self):
        return Favourite.objects.filter(user = self.request.user).\
        order_by("-created")
class ShopFavoriteAddView(LoginRequiredMixin,View):
    def get(self,request,id):
        user = request.user
        try:
            product = Product.objects.get(id = id)
            favourite, created = Favourite.objects.get_or_create(product = product,user = user)
            if created:
                messages.success(request,_("Product added to favourites"))
            else:
                favourite.delete()
                messages.success(request,_("Product removed to favourites"))
            return redirect(reverse("shop"))
        except Product.DoesNotExist:
            messages.error(request,_("Product does not exist"))
            return redirect(reverse("shop"))
class AddToCart(View):
    def get(self,request,id):
        quantity = request.GET.get("quantity","1")
        redirect_url = request.GET.get("redirect_url")
        if quantity.isnumeric():
            quantity = int(quantity)
        else:
            quantity = 1
        try:
            if not Product.objects.active().filter(id = id).exists():
                messages.error(request,_("Product cannot be added to cart"))
                return redirect(reverse("shop"))
            product = Product.objects.get(id = id)
            cart = Cart(request)
            cart.add(product,quantity,override_quantity=True)
            messages.success(request,_("Successfully added to cart"))
            return redirect( redirect_url if redirect_url else reverse("shop"))
        except Product.MultipleObjectsReturned:
            messages.error(request,_("Product does not exist"))
            return redirect(redirect_url if redirect_url else reverse("shop"))
class RemoveFromCart(View):
    def get(self,request,id):
        try:
            product = Product.objects.get(id = id)
            cart = Cart(request)
            cart.remove(product)
            messages.success(request,_("Successfully removed from cart"))
            return redirect(reverse("cart"))
        except Product.DoesNotExist:
            messages.error(request,_("Product does not exist"))
            return redirect(reverse("cart"))
        

class CartView(View):
    def get(self,request):
        return render(request,"cart.html")
    def post(self,request):
        cart = Cart(request)
        for item in cart:
            quantity = request.POST.get(str(item.id))
            if int(quantity) != item.quantity:
                cart.change_quantity(item,int(quantity))
        messages.success(request,_("Cart Updated Successfully"))
        return redirect(reverse("cart"))
                


            
class ContactFormView(FormView):
    form_class  = ContactForm
    template_name = "contact.html"
    success_url = reverse_lazy("contact-us")
    def form_valid(self, form):
        form.send_mail()
        messages.success(self.request,_("Form Sent Successfully. You will recieve a reply shortly."))
        return super().form_valid(form)

class ProfileView(LoginRequiredMixin,View):
    def get(self,request):

        context = {
            "wallet": Wallet.objects.get_or_create(user = request.user)[0],
            "address": Address.objects.filter(user = request.user).first() if Address.objects.filter(user = request.user).exists()\
            else {}
        }
        return render(request,"profile.html", context)

class FundWalletView(LoginRequiredMixin,View):
    def post(self,request):
        amount = request.POST['amount']
        if int(amount) < 500:
            messages.error(request,"Amount should not be less than 500")
            return redirect("account")
        transaction = WalletTransaction()
        transaction.user = self.request.user
        transaction.amount = amount
        transaction.type = "c"
        transaction.save()
        payment = Paystack()
        response = payment.initalize_payment(
            request.user.email,amount,
            ref = transaction.ref, 
            success_url= self.request.build_absolute_uri(
            reverse("verify-wallet-payment", kwargs={'ref':transaction.ref}))
            )
        if response['status']:
            return redirect(response["data"]["authorization_url"])
        else:
            messages.error(self.request,_(response['message']))
            return redirect("account")

@login_required
def verify_wallet_payment(request,ref):
    payment = Paystack()
    response = payment.verify_payment(ref)
    if response['status']:
        try:
            transaction = WalletTransaction.objects.get(ref = ref, user = request.user)
            if not transaction.verified:
                transaction.verified = True
                transaction.save()
                wallet = Wallet.objects.get(user = request.user)
                wallet.amount += transaction.amount
                wallet.save()
                messages.success(request,_("Wallet funded successfully"))
            else:
                messages.error(request,_("Transaction Already Verified"))
                return redirect("account")

        except WalletTransaction.DoesNotExist:
            messages.error(request,_("unknown transaction"))
            return redirect(reverse("account"))
    else:
        messages.error(request,_(response['message']))
        return redirect(reverse("account"))
    # messages.success(request,_("Order and Payment Successfully Made"))
    return redirect(reverse("account"))



@require_POST
def get_banks(request):
    if request.is_ajax():
        payment = Paystack()
        data = payment.banks()
        # print(data)
        return JsonResponse(data,safe=False)
    return redirect("account")

@require_POST
def resolve_account(request):
    account_number = request.POST['account_number']
    bank_code = request.POST['bank_code']
    payment = Paystack()
    data = payment.resolve_account(account_number,bank_code)
   
    return JsonResponse(data)

class DebitWalletView(LoginRequiredMixin,View):
    def post(self,request):
        payment = Paystack()
        type = request.POST['type']
        account_name = request.POST['name']
        account_number = request.POST['account_number']
        bank_code = request.POST['bank_code']
        amount = request.POST['amount']
        wallet = Wallet.objects.get(user = request.user)
        if Decimal(amount) > wallet.amount:
            print(Decimal(amount))
            messages.error(request,_("Insufficient Funds"))
            return redirect("account")
        response = payment.bank_recipient(type,account_name,account_number,bank_code)
        if response['status']:
            data = response['data']
            transaction = WalletTransaction()
            transaction.amount = Decimal(amount)
            transaction.save()
            transfer_response = payment.make_transfer(amount,transaction.ref,data['recipient_code'])
            if transfer_response['status']:
                wallet.amount -= transfer_response['data']['amount']
                wallet.save()
                messages.success(request,_("Withdrawal Successful. You will recieve your money shortly"))
                return redirect("account")
            else:
                messages.error(request,_(transfer_response["message"]))
                return redirect("account")
        else:
            messages.error(request,_("Your Account could not be reolved properly"))
            return redirect("account")
   



class OrdersView(LoginRequiredMixin,ListView):
    template_name = "order.html"
    context_object_name = "orders"
    
    def get_queryset(self):
        return Order.objects.filter(user = self.request.user).order_by("-created")

class OrderDetailView(LoginRequiredMixin,View):
    def get(self,request,id):
        try:
            order = Order.objects.get(id = id)
            if order.user != request.user:
                return HttpResponseForbidden()
            transaction = Transaction.objects.get(ref = order.transaction_ref)
            transaction_type = transaction.get_payment_type_display()
        except Order.DoesNotExist:
            return HttpResponseNotFound
        except Transaction.DoesNotExist:
            transaction_type = "Not Available"
        return render(request,"order-details.html",{'order':order, "transaction_type":transaction_type})

@login_required
def view_order_invoice(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user:
        return HttpResponseForbidden() 
    html = render_to_string('order-pdf.html', 
                            {'order': order})
    buffer = io.BytesIO()
    
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'filename=order_{order.id}.pdf' 
    weasyprint.HTML(string=html).write_pdf(buffer,
        stylesheets=[weasyprint.CSS(settings.STATIC_ROOT / "css/pdf.css")])
    buffer.seek(0)
    response = FileResponse(buffer,filename=f"order_{order.id}.pdf")
    return response
    
class CheckoutView(LoginRequiredMixin,FormView):
    template_name = "checkout.html"
    success_url = reverse_lazy("checkout")
    form_class = CheckoutForm
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        address = Address.objects.filter(user = self.request.user)
        if address.exists():
            address = address.first()
            context = {
                'address': address.address,
                'country': address.country,
                'postal_code': address.postal_code,
                'state': address.state
            }
            kwargs['initial'] = context
        kwargs['request'] = self.request
        return kwargs
    def form_valid(self, form):
        payment_option = form.cleaned_data['payment']
        payment_methods = {
            'paystack': self.paystack_payment,
            'wallet': self.wallet_payment
        }
        if payment_option not in payment_methods.keys():
            messages.error(self.request,_("Invalid Payment Method"))
            self.success_url = reverse("checkout")
            return super().form_valid(form)
        order = form.create_order(self.request)
        

        if not order:
            messages.error(self.request,_("An error occured: Cannot Make Order"))
            self.success_url = reverse("checkout")
            return super().form_valid(form)
        payment_func = payment_methods[payment_option](order)
        if payment_func:
            self.success_url = payment_func
        
        return super().form_valid(form)
    
    def wallet_payment(self,order):
        transaction = Transaction()
        transaction.user = self.request.user
        transaction.amount = order.get_total_cost()
        transaction.payment_type = "w"
        transaction.save()
        
        wallet = Wallet.objects.get(user = self.request.user)
        wallet.amount -= order.get_total_cost()
        wallet.save()
        order.status = Order.OrderStatus.PAID
        order.transaction_ref = transaction.ref
        order.paid = True
        order.save()
        # Send asynchorous email notification
        order_created.delay(order.id)

        cart = Cart(self.request)
        cart.clear()
        messages.success(self.request,_("Order and Payment Successfully Made"))
        return reverse("cart")
    def paystack_payment(self, order):
        transaction = Transaction()
        transaction.user = self.request.user
        transaction.amount = order.get_total_cost()
        transaction.save()
        payment = Paystack()
        response = payment.initalize_payment(
            self.request.user.email,order.get_total_cost(),
            ref = transaction.ref, 
            success_url= self.request.build_absolute_uri(
            reverse("verify-payment", kwargs={'ref':transaction.ref}))
            )
        if response['status']:
            order.transaction_ref = response['data']['reference']
            order.save()
            return  response["data"]["authorization_url"]
        else:
            messages.error(self.request,_(response['message']))
            return None

@login_required
def verify_payment(request, ref):
    payment = Paystack()
    response = payment.verify_payment(ref)
    if response['status']:
        try:
            transaction = Transaction.objects.get(ref = ref, user = request.user)
            transaction.verified = True
            transaction.save()
            order = Order.objects.filter(transaction_ref = transaction.ref)
            if order.exists():
                order = order.first()
                order.status = Order.OrderStatus.PAID
                order.paid = True
                order.save()
                # Send asynchorous email notification
                order_created.delay(order.id)
        except Transaction.DoesNotExist:
            messages.error(request,_("unknown transaction"))
            return redirect(reverse("cart"))
    else:
        messages.error(request,_(response['message']))
        return redirect(reverse("cart"))
    cart = Cart(request)
    cart.clear()
    messages.success(request,_("Order and Payment Successfully Made"))
    return redirect(reverse("cart"))
        

class InboxListView(LoginRequiredMixin, ListView):
    template_name = "inbox.html"
    paginate_by = 15

    def get_queryset(self):
        return Inbox.objects.filter(user = self.request.user).order_by("-created")
class InboxDetailView(LoginRequiredMixin, DetailView):
    model = Inbox
    template_name = "inbox-details.html"

    def get(self,request, *args,**kwargs):
        object = self.get_object()
        object.read = True
        object.save()
        return super().get( request,*args, **kwargs)


class SignUpView(FormView):
    template_name = 'signup.html'
    form_class = UserCreationForm

    def get_success_url(self):
        redirect_to = self.request.GET.get('next','/')
        return redirect_to
    def form_valid(self,form):
        response = super().form_valid(form)
        form.save()
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(email = email, password = password)
        form.send_mail()
        cart_session = self.request.session.get(f"{settings.CART_SESSION_ID}")
        if cart_session:
            cart_session = cart_session.copy()
        login(self.request,user,backend="django.contrib.auth.backends.ModelBackend")
        if cart_session:
            self.request.session[settings.CART_SESSION_ID] = cart_session
        messages.info(self.request,_('You signed up Successfully'))
        return response
class PasswordResetView(auth_views.PasswordResetView):
    template_name = "reset-password.html"
    
    def get_success_url(self):
        url = reverse_lazy("login")
        messages.success(self.request,_("Password Reset Email has been sent. Go to your registered email to confirm the password reset request "))
        return url

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "new-password.html"

    def get_success_url(self):
        url = "/login"
        messages.success(self.request,_("Password have been reset successfully"))
        return url


class LogoutView(View):
    def get(self, request):
        cart_session = request.session.get(f"{settings.CART_SESSION_ID}")
        if cart_session:
            cart_session = cart_session.copy()
        logout(request)
        if cart_session:
            request.session[settings.CART_SESSION_ID] = cart_session
        messages.success(request,_("Logout Successful"))
        return redirect(reverse("login"))
