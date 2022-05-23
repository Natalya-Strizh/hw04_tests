from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """При отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данных."""
        posts_count = Post.objects.count()
        dict_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=dict_data,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, dict_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group_id, dict_data['group'])


    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных"""
        dict_data = {
            'text': 'Тестовый текст1',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_update', kwargs={'post_id': self.post.id}),
            data=dict_data,
        )
        post = Post.objects.get(
            text=dict_data['text'],
            group=dict_data['group']
        )
        self.assertEqual(post.text, dict_data['text'])
        self.assertEqual(post.group.title, self.group.title)
