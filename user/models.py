# -*- coding: utf-8 -*-
import uuid
from django.db import models

class Document(models.Model):
	docfile = models.ImageField(uuid.uuid4(),upload_to='DATA/%Y/%m/%d')
