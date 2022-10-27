from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='authorized_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostURLTests.user)

    def test_guest_client_urls(self):
        guest_urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{PostURLTests.user}/',
            f'/posts/{self.post.pk}/',
        ]
        for url in guest_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/authorized_user/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_post(self):
        response = self.author.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_guest(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_non_author_user(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_edit_guest(self):
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_guest_index_follow_redirect(self):
        response = self.guest_client.get('/follow/')
        self.assertRedirects(response,
                             '/auth/login/?next=/follow/')

    def test_guest_follow_redirect(self):
        response = self.guest_client.get(f'/profile/{self.user}/follow/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/profile/{self.user}/follow/')

    def test_guest_unfollow_redirect(self):
        response = self.guest_client.get(f'/profile/{self.user}/unfollow/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/profile/{self.user}/unfollow/')
