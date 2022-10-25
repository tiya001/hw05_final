from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Follow, Post, Group
from ..forms import CommentForm, PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=image,
            content_type='image/image'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i+1}',
                group=cls.group,
                image=uploaded,
            )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='authorized_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostViewsTests.user)

    def test_auth_follow(self):
        '''Авторизованный пользователь может подписываться'''
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post.author})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.post.author,
            ).exists()
        )

    def test_auth_unfollow(self):
        '''Авторизованный пользователь может отписываться'''
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.post.author})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.post.author
            ).exists()
        )

    def test_new_post_for_follower(self):
        '''Новый пост появляется в ленте тех, кто подписан'''
        Follow.objects.create(user=self.user,
                              author=self.post.author)
        index = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_post = Post.objects.create(author=self.post.author,
                                       text='пост после подписки')
        self.assertIn(new_post, index.context['posts'])

    def test_new_post_for_non_follower(self):
        '''Новый пост не появляется в ленте тех, кто не подписан'''
        index = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_post = Post.objects.create(author=self.post.author,
                                       text='пост после подписки')
        self.assertNotIn(new_post, index.context['posts'])

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}): 'posts/'
                                                       'post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): 'posts/'
                                                       'create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator(self):
        page_list = (
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        for reverse_name in page_list:
            with self.subTest(reserse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_main_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, f'Тестовый пост {first_object.pk}')
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, f'Тестовый пост {first_object.pk}')
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'author'}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_text_0, f'Тестовый пост {first_object.pk}')
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:post_detail',
                                   kwargs={'post_id': self.post.pk}))
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, f'Тестовый пост {first_object.pk}')
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_id_0, self.post.id)
        self.assertEqual(post_image_0, self.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_conxtext(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author.get(reverse('posts:post_edit',
                                   kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_group(self):
        """Пост группы не появляется на странице другой группы"""
        Group.objects.create(
            title='Пустая группа',
            slug='empty-slug',
            description='Пустое описание',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'empty-slug'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_guest_comment_redirect(self):
        response = self.guest_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code, 302)

    def test_cache_index(self):
        '''проверка кэширования index'''
        test_post = Post.objects.create(
            text='textik',
            author=self.user,
            group=self.group
        )
        count_posts = Post.objects.count()

        self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(count_posts, 14)
        test_post.delete()
        cache.clear()

        count_posts = Post.objects.count()
        self.assertEqual(count_posts, 13)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_add_comment(self):

        comments_count = self.post.comments.count()
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTests.post.id}
            ),
            data=form_data,
        )
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTests.post.id}
        ))
        self.assertTrue(self.post.comments.filter(
            post=CommentFormTests.post,
            author=CommentFormTests.author,
            text='Тестовый комментарий',
        ).exists())
