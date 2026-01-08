from django.db import models

from mongoengine import (
    Document, StringField, DateTimeField, ImageField
)
from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    ReferenceField,
    ImageField
)
from datetime import datetime

from mongoengine import Document, StringField, DateTimeField, ImageField, ReferenceField, IntField
from datetime import datetime

class Complaint(Document):
    complaint_no = IntField(required=True, unique=True)  # 👈 NEW

    citizen_id = StringField(required=True)
    title = StringField(required=True)
    description = StringField(required=True)

    before_image = ImageField(required=True)

    waste_type = StringField(required=True)
    area = StringField(required=True)
    sub_area = StringField()

    status = StringField(default="PENDING")

    complaint_date = DateTimeField(default=datetime.utcnow)

    after_image = ImageField(null=True)
    assigned_karmachari = ReferenceField("SafaiKarmachari", null=True)
    assigned_contractor = ReferenceField("StaffUser", null=True)
    completion_date = DateTimeField(null=True)

    meta = {"collection": "complaints"}

class ComplaintWorkflowLog(Document):
    complaint_id = StringField()
    citizen_id = StringField()
    contractor_id = StringField()
    title = StringField()
    area = StringField()
    status = StringField()
    received_at = DateTimeField()
    assigned_to_contractor_at = DateTimeField()


from django.db import models

# api/models.py
from mongoengine import Document, StringField, EmailField

class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)
    phone = StringField()
    email = EmailField(required=True, unique=True)


from mongoengine import Document, StringField


class StaffUser(Document):
    phone_number = StringField(required=True)
    full_name = StringField(required=True)
    password = StringField(required=True)
    user_role = StringField(required=True)   # ADMIN / MANAGER / CONTRACTOR
    assigned_area = StringField()

class SafaiKarmachari(Document):
    phone_no = StringField(required=True)
    username = StringField(required=True)
    password = StringField(required=True)
    area = StringField()
    status = StringField(default="FREE") 

    meta = {
        "collection": "safai_karmachari"  # 🔥 MUST MATCH MONGODB
    }

from mongoengine import Document, StringField, IntField

class StaffUser(Document):
    user_id = IntField()  # optional, Mongo auto id exists
    full_name = StringField(max_length=100)
    phone_number = StringField(max_length=20, required=True)
    password = StringField(max_length=100)
    user_role = StringField(
        max_length=30,
        required=True,
        choices=["ADMIN", "MANAGER", "CONTRACTOR"]
    )
    assigned_area = StringField(max_length=100)
    address = StringField(max_length=255)

    meta = {
        "collection": "staff_users"
    }


class SafaiKarmachari(Document):
    username = StringField(max_length=100)
    password = StringField(max_length=100)
    email = StringField(max_length=150)
    phone_no = StringField(max_length=20)
    status = StringField(max_length=50)
    area = StringField(max_length=25)
    landmark = StringField(max_length=100)
    points = IntField(default=0)
    address = StringField(max_length=255)

    meta = {
        "collection": "safai_karmachari"
    }


# api/models.py
from mongoengine import Document, StringField, IntField

class Counter(Document):
    name = StringField(required=True, unique=True)
    value = IntField(default=0)
