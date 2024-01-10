from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def manage_session(sender, user, request,**kwargs):
    print([x for x in request.session.keys()])
