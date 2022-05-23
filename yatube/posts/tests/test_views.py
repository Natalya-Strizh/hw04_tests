from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm

from ..models import Group, Post

User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user = PostViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_update', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def additional_function(self, response, obj):
        """Вспомогательная функция"""
        if obj == 'page_obj':
            post = response.context.get(obj).object_list[0]
        else:
            post = response.context.get('post_number')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_has_correct_context(self):
        """Проверяем что index передаёт правильный контекст"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.additional_function(response, 'page_obj')

    def test_group_post_has_correct_context(self):
        """Проверяем что group_post передаёт правильный контекст"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        group = response.context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.additional_function(response, 'page_obj')

    def test_profile_page_has_correct_context(self):
        """Проверяем что profile передаёт правильный контекст"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        author = response.context.get('author')
        self.assertEqual(author.username, self.user.username)

    def test_post_detail_page_has_correct_context(self):
        """Проверяем что post_detail передаёт правильный контекст"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.additional_function(response, 'post_number')

    def test_post_create_page_has_correct_context(self):
        """Проверяем что create передаёт правильный контекст"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_page_has_correct_context(self):
        """Проверяем что post_edit передаёт правильный контекст"""
        post = self.post
        response = self.authorized_client.get(
            reverse('posts:post_update', kwargs={'post_id': self.post.id}))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('post'), post)
        self.assertTrue(response.context.get('is_edit'))

    def additional_check_when_creating_a_post(self):
        """Дополнительная проверка при создании поста. пост появляется
        на главной странице, странице группы и профайле автора"""
        post = self.post
        dict = {
            reverse('posts:index'): Post.objects.all(),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            Post.objects.filter(group=post.group),
            reverse('posts:profile', kwargs={'username': self.user.username}):
            Post.objects.filter(author=post.author),
        }
        for reverse_name, filter in dict.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTrue(filter.exists())

    def additional_check_when_creating_a_post(self):
        """Дополнительная проверка при создании поста. Пост не появляеться
        в другой группе"""
        post = self.post
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertNotIn(post, response.context.get('page_obj'))


FIRST_PAGE = 10
SECOND_PAGE = 5
POSTS_ALL = 15


class PaginatorViewsTest(TestCase):
    """Класс с тестами пагинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            description='Тестовое описание',
            slug='test-slug',
        )
        for post in range(POSTS_ALL):
            Post.objects.create(
                author = cls.user,
                text = 'Текст №' + str(post + 1),
                group = cls.group,
            )

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_paginator(self):
        dict = {
            reverse('posts:index'): FIRST_PAGE,
            reverse('posts:index') + '?page=2': SECOND_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}): FIRST_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}) + 
        '?page=2': SECOND_PAGE,
            reverse(
                'posts:profile', kwargs={'username': 'author'}): FIRST_PAGE,
            reverse(
                'posts:profile', kwargs={'username': 'author'}) +
        '?page=2': SECOND_PAGE,
        }
        for reverse_page, len_posts in dict.items():
            with self.subTest(reverse_page=reverse_page):
                self.assertEqual(
                    len(self.client.get(reverse_page).context.get('page_obj')), len_posts)

         
        





            







   
        
