from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import secrets
from decimal import Decimal
from django.db.models import Avg

# Create your models here.
class SubmittedTaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status = Task.STATUS.SUBMITTED)
    def today(self):
        return self.get_queryset().filter(created__year = timezone.now().year) #access this Task.submitted.today()

class ActiveManager(models.Manager):
    def active(self):
        return self.filter(active = True)


User  = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=15)
    slug = models.SlugField(max_length=20,unique=True)
    image = models.ImageField(upload_to="categories", blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "category"
        verbose_name_plural = "categories"

    def product_count(self):
        return self.product_set.count()
    def __str__(self):
        return self.name
    

class Product(models.Model):
    user = models.ForeignKey(User, null=True, blank=True ,on_delete=models.SET_NULL)
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    tags = models.ManyToManyField(Category,blank=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="product-images/%Y/%m/%d", blank=True)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    objects = ActiveManager()

    class Meta:
        ordering = ("created","name")
        permissions = [("edit_power","can edit products")]
    
    def review_count(self):
        return self.reviews.count()
    def average_rating(self):
        return self.reviews.aggregate(rating = Avg("rating"))['rating']
    
    def get_absolute_url(self):
        return reverse("details",kwargs={"pk":self.pk})
    
    def __str__(self):
        return self.name

class ProductFeature(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.product.name

class ProductFeatureLine(models.Model):
    feature = models.ForeignKey(ProductFeature, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.feature.name + " - " + self.name

class Wallet(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created",)

class Task(models.Model):
    SUBMITTED = 1
    ONGOING = 2
    COMPLETED = 3
    class STATUS(models.TextChoices):
        SUBMITTED = 1,"submitted"
        ONGOING = 2,"ongoing"
        COMPLETED = 3,"completed"
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    name = models.CharField(max_length = 100)
    assigned = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=2, choices=STATUS.choices, default=STATUS.SUBMITTED)
    created = models.DateTimeField(auto_now_add=True)

    submitted = SubmittedTaskManager()

    def get_absolute_url(self):
        return reverse('product',args=[self.id])


class Review(models.Model):
    user = models.ForeignKey(User, blank=True ,null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product,related_name="reviews", on_delete=models.CASCADE)
    alias = models.CharField(max_length=20, blank=True)
    rating  = models.IntegerField()
    comment = models.TextField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created",)
        verbose_name = "review"
        verbose_name_plural = "reviews"

class UserFollow(models.Model):
    user_to = models.ForeignKey(User,on_delete=models.CASCADE, related_name="followers")
    user_from = models.ForeignKey(User, on_delete=models.CASCADE,related_name="following")
    created = models.DateTimeField(auto_now_add=True)

    class Meta: 
        indexes = [
            models.Index(fields=['-created']), 
        ]
        ordering = ['-created']
    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'


# User.add_to_class('following', models.ManyToManyField('self',through = UserFollow,related_name="followers")) # i don't know what this is for

class Action(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name="actions")
    verb = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    target_ct = models.ForeignKey(ContentType,on_delete=models.CASCADE,
                                  blank=True, null=True, related_name="target_obj")
    target_id = models.PositiveIntegerField(null=True,blank=True)

    target = GenericForeignKey('target_ct','target_id')

    class Meta:
        indexes = [
            models.Index(fields=['-created'])
        ]
        ordering = ('-created',)

class Transaction(models.Model):
    user = models.ForeignKey(User,related_name="transactions",on_delete=models.SET_NULL, blank=True, null=True)
    ref = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    payment_type = models.CharField(max_length=3,choices=(("ps","Paystack"),("w","Wallet")), default="ps")
    verified = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering= ('created',)

    def save(self,*args,**kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            similar_ref =Transaction.objects.filter(ref=ref)
            if not similar_ref.exists():
                self.ref = ref
                break
        super().save(*args,**kwargs)


class WalletTransaction(models.Model):
    user = models.ForeignKey(User,related_name="wallet_transactions",on_delete=models.SET_NULL, blank=True, null=True)
    ref = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    type = models.CharField(max_length=2, choices=(("c","Credit"),("d","Debit")))
    verified = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering= ('created',)

    def save(self,*args,**kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            similar_ref = WalletTransaction.objects.filter(ref=ref)
            if not similar_ref.exists():
                self.ref = ref
                break
        super().save(*args,**kwargs)

class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True) 
    address = models.CharField(max_length=1000)

    def __str__(self):
        return self.user.get_username() +" -- " +self.country

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        NOT_PAID = "1","not paid"
        PAID = "2","paid"
        PROCESSING = "3","processing"
        COMPLETED = "4","completed"
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True) 
    address = models.CharField(max_length=1000)
    phonenumber = models.CharField(max_length=12)
    city = models.CharField(max_length=100) 
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=2,choices=OrderStatus.choices, default=OrderStatus.NOT_PAID)
    transaction_ref = models.CharField(max_length=200,blank=True)
    created = models.DateTimeField(auto_now_add=True) 
    updated = models.DateTimeField(auto_now=True) 
   
    class Meta:
            ordering = ['-created'] 
            indexes = [
                models.Index(fields=['-created']), 
            ]
    def __str__(self):
        return f'Order {self.id}' 
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    def get_absolute_url(self):
        return reverse("order-details",kwargs={"id":self.id})


    
class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items', 
                              on_delete=models.CASCADE) 
    product = models.ForeignKey(Product,
                         related_name='order_items', 
                                on_delete=models.CASCADE) 
    price = models.DecimalField(max_digits=10,
                                decimal_places=2) 
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id) 
    def get_cost(self):
        return self.price * self.quantity

class Favourite(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.product.name,self.user.get_username())

class Inbox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("inbox-details",kwargs={"pk":self.id})

    def __str__(self):
        return self.user.get_username() + " -- " + self.subject

    

