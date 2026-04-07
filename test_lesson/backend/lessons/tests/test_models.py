from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from lessons.models import InteractionRecord
from datetime import timedelta

class InteractionRecordModelTest(TestCase):
    
    def setUp(self):
        """
            Создаем тестовую запись
        """
        self.record = InteractionRecord.objects.create(
            session_id='test_session_123',
            question='Что такое переменная?',
            correct_answer='Именованная область памяти',
            user_answer='Переменная это имя для данных',
            question_order=0,
            status='pending'
        )
    
    def test_create_record(self):
        """
            Тест создания записи
        """
        self.assertEqual(self.record.session_id, 'test_session_123')
        self.assertEqual(self.record.question, 'Что такое переменная?')
        self.assertEqual(self.record.status, 'pending')
        self.assertIsNone(self.record.is_correct)
        self.assertIsNotNone(self.record.asked_at)
    
    def test_status_choices(self):
        """
            Тест всех возможных статусов
        """
        statuses = ['pending', 'processing', 'checked', 'error', 'timeout']
        
        for status in statuses:
            self.record.status = status
            self.record.save()
            self.assertEqual(self.record.status, status)
    
    def test_timestamp_auto_now_add(self):
        """
            Тест автоматической установки времени
        """

        self.assertIsNotNone(self.record.asked_at)
        self.assertIsNone(self.record.answered_at)
        self.record.answered_at = timezone.now()
        self.record.save()
        self.assertIsNotNone(self.record.answered_at)
    
    def test_nullable_fields(self):
        """
            Тест nullable полей
        """
        record2 = InteractionRecord.objects.create(
            session_id='test_456',
            question='Тест',
            correct_answer='Ответ',
            user_answer=None,
            question_order=1,
            status='timeout'
        )
        
        self.assertIsNone(record2.user_answer)
        self.assertIsNone(record2.is_correct)
        self.assertIsNone(record2.checked_at)
    
    def test_string_representation(self):
        """
            Тест строкового представления
        """
        expected = f"Q{self.record.question_order}: {self.record.question[:50]}"
        self.assertEqual(str(self.record), expected)
    
    def test_default_ordering(self):
        """
            Тест сортировки по умолчанию
        """
        record1 = InteractionRecord.objects.create(
            session_id='test',
            question='Вопрос 1',
            correct_answer='Ответ 1',
            question_order=0,
            status='pending'
        )
        record2 = InteractionRecord.objects.create(
            session_id='test',
            question='Вопрос 2',
            correct_answer='Ответ 2',
            question_order=1,
            status='pending'
        )
        
        records = InteractionRecord.objects.all()
        self.assertEqual(records[0].question_order, 0)
    
    def test_session_index(self):
        """
            Тест индексации по session_id
        """
        for i in range(3):
            InteractionRecord.objects.create(
                session_id=f'session_{i}',
                question=f'Q{i}',
                correct_answer=f'A{i}',
                question_order=i,
                status='pending'
            )
        
        records = InteractionRecord.objects.filter(session_id='session_1')
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().question, 'Q1')
