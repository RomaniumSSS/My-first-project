from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    goals: fields.ReverseRelation["Goal"]

    class Meta:
        table = "users"


class Goal(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="goals")
    title = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    image_base64 = fields.TextField(null=True)
    status = fields.CharField(max_length=50, default="active")
    created_at = fields.DatetimeField(auto_now_add=True)

    checkins: fields.ReverseRelation["CheckIn"]

    class Meta:
        table = "goals"


class CheckIn(models.Model):
    id = fields.IntField(pk=True)
    goal = fields.ForeignKeyField("models.Goal", related_name="checkins")
    date = fields.DatetimeField(auto_now_add=True)
    report_text = fields.TextField()
    image_base64 = fields.TextField(null=True)
    ai_feedback = fields.TextField(null=True)

    class Meta:
        table = "checkins"
