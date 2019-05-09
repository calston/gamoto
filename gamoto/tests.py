from django.test import TestCase, Client
from django.urls import reverse, exceptions
from django.urls.resolvers import URLPattern


# Create your tests here.
class TestRockfaceCase(TestCase):
    def test_authentication_required(self):
        from gamoto import urls

        redirect_map = []
        for url in urls.urlpatterns:
            if not isinstance(url, URLPattern):
                continue
            try:
                url = reverse(url.name)
                redirect_map.append((url.name, url))
            except exceptions.NoReverseMatch:
                pass

        print(redirect_map)
        r = self.client.get(reverse('index'))
        self.assertRedirects(r, reverse('login')+'?next=/')

    def test_login(self):
        self.client.login(username='test', password='test')
