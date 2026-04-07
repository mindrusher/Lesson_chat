from django.test import TestCase
from django.utils import timezone
from lessons.models import InteractionRecord
from lessons.views import check_answer_task
from unittest.mock import patch, Mock
import requests

class CeleryTasksTest(TestCase):
    
    def setUp(self):
        self.record = InteractionRecord.objects.create(
            session_id='test_session',
            question='Что такое Python?',
            correct_answer='Python - это язык программирования',
            user_answer='Язык программирования',
            question_order=0,
            status='processing'
        )
    
    @patch('lessons.views.requests.post')
    def test_check_answer_task_success(self, mock_post):
        """
            Тест успешной проверки ответа
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'is_correct': 1}
        mock_post.return_value = mock_response
        
        check_answer_task(self.record.id)
        
        self.record.refresh_from_db()
        
        self.assertEqual(self.record.status, 'checked')
        self.assertTrue(self.record.is_correct)
        self.assertIsNotNone(self.record.checked_at)
        mock_post.assert_called_once()
    
    @patch('lessons.views.requests.post')
    def test_check_answer_task_incorrect(self, mock_post):
        """
            Тест неправильного ответа
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'is_correct': 0}
        mock_post.return_value = mock_response
        
        check_answer_task(self.record.id)
        self.record.refresh_from_db()
        
        self.assertEqual(self.record.status, 'checked')
        self.assertFalse(self.record.is_correct)
    
    @patch('lessons.views.requests.post')
    def test_check_answer_task_ml_error(self, mock_post):
        """
            Тест ошибки ML сервиса
        """
        mock_response = Mock()
        mock_response.status_code = 503
        mock_post.return_value = mock_response
        
        check_answer_task(self.record.id)
        self.record.refresh_from_db()
        
        self.assertEqual(self.record.status, 'error')
        self.assertIsNone(self.record.is_correct)
        self.assertIsNotNone(self.record.error_message)
    
    @patch('lessons.views.requests.post')
    def test_check_answer_task_network_error(self, mock_post):
        """
            Тест сетевой ошибки
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        check_answer_task(self.record.id)
        self.record.refresh_from_db()
        
        self.assertEqual(self.record.status, 'error')
        self.assertIn('Connection refused', self.record.error_message)
    
    @patch('lessons.views.requests.post')
    def test_check_answer_task_timeout(self, mock_post):
        """
            Тест таймаута запроса
        """
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        check_answer_task(self.record.id)
        self.record.refresh_from_db()
        
        self.assertEqual(self.record.status, 'error')
        self.assertIsNotNone(self.record.error_message)
