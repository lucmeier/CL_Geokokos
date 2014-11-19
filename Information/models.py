from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Information(models.Model):
    content = models.TextField(blank=False)
    date_published = models.DateField(auto_now=True)
    date_changed = models.DateField(auto_now=True)

    def __str__(self):
        return self.content


class NewsPiece(Information):
    author = models.ForeignKey(User)
    title = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return (self.title, self.author, super)

class FaqElement(Information):
    question = models.TextField()
    order = models.IntegerField(unique=True) #smallest number is to be displayed first
