from .cart import Cart
from .models import Favourite, Category, Inbox


def cart(request):
    return {'cart':Cart(request)}

def favourites(request):
    if request.user.is_authenticated:
        favourite = Favourite.objects.filter(user = request.user).values_list('product',flat=True)
        return {'favourites': favourite}
    else:
        favourite = Favourite.objects.none()
        return {'favourites': favourite }

def categories(request):
    categories = Category.objects.all().order_by("name")
    return {'categories': categories}

def unread_messages(request):
    if request.user.is_authenticated:
        inbox = Inbox.objects.filter(user = request.user, read = False).count()
    else:
        inbox = 0
    return {'unread':inbox}


