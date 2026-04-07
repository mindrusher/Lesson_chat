from django.test import TestCase, Client
from django.urls import reverse
from lessons.models import InteractionRecord
from lessons.question_bank import questions
from unittest.mock import patch, Mock
import json
import time

class IntegrationTest(TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_full_lesson_flow(self):
        """
            Тест полного прохождения урока
        """
        response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = response.json()['session_id']
        
        for i, q in enumerate(questions):
            response = self.client.post(
                reverse('submit_answer'),
                data=json.dumps({
                    'session_id': session_id,
                    'answer': f'Ответ на вопрос {i}',
                    'question_order': i
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            if i == len(questions) - 1:
                self.assertTrue(data['is_last'])
            else:
                self.assertEqual(data['next_question'], questions[i+1]['question'])

        records = InteractionRecord.objects.filter(session_id=session_id)
        self.assertEqual(records.count(), len(questions))
        
        for i, record in enumerate(records):
            self.assertEqual(record.question_order, i)
            self.assertEqual(record.question, questions[i]['question'])
    
    def test_timeout_handling(self):
        """
            Тест обработки таймаута
        """
        response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = response.json()['session_id']

        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': '',
                'question_order': 0
            }),
            content_type='application/json'
        )
        
        record = InteractionRecord.objects.first()
        self.assertEqual(record.user_answer, '')
        self.assertEqual(record.status, 'processing')
    
    @patch('lessons.views.requests.post')
    def test_ml_error_handling_in_flow(self, mock_post):
        """
            Тест обработки ошибки ML в реальном потоке
        """
        mock_response = Mock()
        mock_response.status_code = 503
        mock_post.return_value = mock_response
        
        response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = response.json()['session_id']
        
        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': 'Тестовый ответ',
                'question_order': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        from lessons.views import check_answer_task
        check_answer_task(InteractionRecord.objects.first().id)
        
        record = InteractionRecord.objects.first()
        self.assertEqual(record.status, 'error')
        self.assertIsNone(record.is_correct)
    
    def test_session_persistence(self):
        """
            Тест сохранения сессии между запросами
        """
        response1 = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = response1.json()['session_id']
        
        response2 = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': 'Ответ',
                'question_order': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 200)
        
        record = InteractionRecord.objects.first()
        self.assertEqual(record.session_id, session_id)
