from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса about/author/, about/tech/."""
        urls_texts = {
            '/about/author/': 200,
            '/about/tech/': 200,
        }
        for urls, expected_value in urls_texts.items():
            with self.subTest(urls=urls):
                self.assertEqual(
                    self.guest_client.get(urls).status_code, expected_value)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса about/author/, about/tech/."""
        urls_texts = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for urls, expected_value in urls_texts.items():
            with self.subTest(urls=urls):
                self.assertTemplateUsed(
                    self.guest_client.get(urls), expected_value)
