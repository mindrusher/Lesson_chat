from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from lessons.models import InteractionRecord
from lessons.question_bank import questions
import json
from unittest.mock import patch, Mock

class ChatViewsTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.session = self.client.session
        self.session.save()
    
    def test_chat_view_get(self):
        """
            Тест главной страницы чата
        """
        response = self.client.get(reverse('chat'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')
        self.assertContains(response, str(len(questions)))
    
    def test_start_lesson(self):
        """
            Тест начала урока
        """
        response = self.client.post(
            reverse('start_lesson'),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['session_id'])
        self.assertEqual(data['question'], questions[0]['question'])
        self.assertEqual(data['question_number'], 1)
        self.assertEqual(data['total_questions'], len(questions))
        
        self.assertEqual(InteractionRecord.objects.count(), 1)
        record = InteractionRecord.objects.first()
        self.assertEqual(record.question, questions[0]['question'])
        self.assertEqual(record.status, 'pending')
    
    def test_start_lesson_clears_previous(self):
        """
            Тест очистки предыдущих записей при новом уроке
        """
        self.client.post(reverse('start_lesson'))
        self.assertEqual(InteractionRecord.objects.count(), 1)

        self.client.post(reverse('start_lesson'))
        self.assertEqual(InteractionRecord.objects.count(), 1)
    
    def test_submit_answer_success(self):
        """
            Тест отправки ответа
        """
        start_response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = start_response.json()['session_id']
        
        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': 'Это правильный ответ',
                'question_order': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        record = InteractionRecord.objects.first()
        self.assertEqual(record.user_answer, 'Это правильный ответ')
        self.assertEqual(record.status, 'processing')
        self.assertIsNotNone(record.answered_at)
    
    def test_submit_answer_not_found(self):
        """
            Тест отправки ответа для несуществующей записи
        """
        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': 'invalid',
                'answer': 'Ответ',
                'question_order': 999
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_submit_answer_last_question(self):
        """
            Тест отправки ответа на последний вопрос
        """
        start_response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = start_response.json()['session_id']

        for i, q in enumerate(questions[:-1]):
            InteractionRecord.objects.create(
                session_id=session_id,
                question=q['question'],
                correct_answer=q['correct_answer'],
                question_order=i,
                status='checked'
            )
        
        last_order = len(questions) - 1
        last_question = questions[last_order]

        InteractionRecord.objects.create(
            session_id=session_id,
            question=last_question['question'],
            correct_answer=last_question['correct_answer'],
            question_order=last_order,
            status='pending'
        )

        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': 'Ответ на последний вопрос',
                'question_order': last_order
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get('is_last', False))
        self.assertIsNone(data.get('next_question'))
        self.assertIsNone(data.get('next_question_number'))
    
    def test_empty_answer_on_timeout(self):
        """
            Тест пустого ответа при таймауте
        """
        start_response = self.client.post(reverse('start_lesson'), content_type='application/json')
        session_id = start_response.json()['session_id']
        
        response = self.client.post(
            reverse('submit_answer'),
            data=json.dumps({
                'session_id': session_id,
                'answer': '',
                'question_order': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        record = InteractionRecord.objects.first()
        self.assertEqual(record.user_answer, '')
        self.assertEqual(record.status, 'processing')
