from django.db import models

class InteractionRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает проверки'),
        ('processing', 'Проверяется'),
        ('checked', 'Проверено'),
        ('error', 'Ошибка проверки'),
        ('timeout', 'Таймаут ответа'),
    ]
    
    session_id = models.CharField(max_length=100, db_index=True)
    question = models.TextField()
    correct_answer = models.TextField()
    user_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    asked_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    question_order = models.IntegerField()

    class Meta:
        ordering = ['question_order']
        indexes = [
            models.Index(fields=['session_id', 'question_order']),
        ]

    def __str__(self):
        return f"Q{self.question_order}: {self.question[:50]}"
