from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        result = group.title
        self.assertEqual(group.__str__(), result)
        post = PostModelTest.post
        result = post.text[:15]
        self.assertEqual(post.__str__(), result)

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'текст поста',
            'pub_date': 'дата публикации',
            'author': 'автор',
            'group': 'Группа',
        }
        for value, result in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, result)
