"""
Creating Custom Authentication Backend

Django uses the authentication backends in the authentication backend settings to authenticate user
it does not stop till at least one backend authenticates the user. authntication falls only if all of them fail
to authenticate the user.

A custom auth backend just has to have the methods 'authenticate' and 'get_user' for it to become a auth backend

"""
from .models import User, Wallet

class EmailAuthBackend:
    """
    Authenticate using email address
    """

    def authenticate(self,request,username = None, password = None):
        try:
            user = User.objects.get(email = username)
            if user.check_password(password):
                return user
            return None
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None
    def get_user(self,user_id):
        try:
            user = User.objects.get(pk  = user_id)
            return user
        except User.DoesNotExist:
            return None
        
"""
After Creating the backend, you add it to the AUTHENTICATION_BACKENDS settings in settings.py
e.g
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend', 
        'account.authentication.EmailAuthBackend',
        ]
initially, the AUTHENTICATION_BACKENDS settings is not in your project settings.py so you add it
"""


# for social auth incase there is a profile or another model object that is needed to be crated immediately after login
def create_wallet(backend,user,*args,**kwargs):
    # This is added to the SOCIAL_PIPELINE settings
    Wallet.objects.create(user = user)

