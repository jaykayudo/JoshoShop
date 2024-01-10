from typing import Any, Dict, Mapping, Optional, Type, Union
from django import forms
from django.contrib.auth import authenticate
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib import messages

from .models import Review, Order, OrderItem, User, Address, Wallet
import logging
from .cart import Cart


class ImageForm(forms.Form):
    width = forms.IntegerField()
    height = forms.IntegerField()
    

class SearchForm(forms.Form):
    query = forms.CharField()

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    def __init__(self,request,*args,**kwargs):
        self.request = request
        self.user = None
        super().__init__(*args,**kwargs)
    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        self.user = authenticate(self.request,username = username, password = password)
        if not self.user:
            raise forms.ValidationError(_("Invalid Credentation"))
        return self.cleaned_data
    def get_user(self):
        return self.user
    
class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ['username','email']
        # field_classes = {'email':UsernameField}

    def send_mail(self):
        logger.info('sending Mail to Customer')
        message = "Welcome {0}, ".format(self.cleaned_data['email'])

        send_mail(
                "Welcome to JoshoShop",
                message,
                "site@joshoshop.domain",
                [self.cleaned_data['email'],],
                fail_silently=True
            )

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = ['created']

logger = logging.getLogger(__name__)
class ContactForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','max-length':'100','placeholder':'Name'}))
    email = forms.EmailField()
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','max-length':'600','rows':'10','cols':'85'}))

    def send_mail(self):
        logger.info('Sending email to customer service')
        subject = self.cleaned_data['subject']
        message = "From:{0}\n{1}\nemail: {2}".format(self.cleaned_data['name'],self.cleaned_data['message'],
                    self.cleaned_data['email'])

        send_mail(
            subject,
            message,
            "site@joshoshop.domain",
            ["customerservice@joshoshop.domain"],
            fail_silently=False
        )
class CheckoutForm(forms.Form):
    country = forms.CharField()
    state = forms.CharField()
    postal_code = forms.CharField(required=False)
    phonenumber = forms.CharField()
    address = forms.CharField()
    save_address = forms.BooleanField(required=False)
    payment = forms.CharField()

    def __init__(self,request, *args,**kwargs):
        self.request = request
        super().__init__(*args,**kwargs)
    
    def clean(self):
        payment = self.cleaned_data['payment']
        if payment == "wallet":
            cart = Cart(self.request)
            wallet = Wallet.objects.get(user = self.request.user)
            if int(wallet.amount) < cart.get_total_price():
                messages.error(self.request,_("Insufficient Wallet Balance"))
                raise forms.ValidationError("Insufficient Wallet Balance")
        return super().clean()

    def create_order(self, request):
        """
        Create Order after form is filled.
        """
        cart = Cart(request)
        if len(cart) < 1:
            return None
        phonenumber = self.cleaned_data['phonenumber']
        address = self.cleaned_data['address']
        state = self.cleaned_data['state']
        country = self.cleaned_data['country']
        postal_code = self.cleaned_data.get('postal_code',"")
        save_address = self.cleaned_data.get("save_address")
       
        order = Order()
        order.phonenumber = phonenumber
        order.address = address
        order.country = country
        order.state = state
        order.postal_code = postal_code
        order.user = request.user
        order.save()
        
        for item in cart:
            OrderItem.objects.create(
                order = order,
                product = item,
                price = item.price,
                quantity = item.quantity
            ) 
        if save_address:
            model_address = Address.objects.filter(user = request.user)
            if model_address.exists():
                model_address  = model_address.first()
                model_address.address = address
                model_address.country = country
                model_address.state = state
                model_address.postal_code = postal_code
                model_address.save()
            else:
                model_address = Address()
                model_address.user = request.user
                model_address.address = address
                model_address.country = country
                model_address.state = state
                model_address.postal_code = postal_code
                model_address.save()            
        return order

