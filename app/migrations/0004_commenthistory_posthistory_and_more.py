# Generated by Django 5.1.2 on 2024-10-23 23:44

import django.db.models.deletion
import pgtrigger.compiler
import pgtrigger.migrations
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_commentcontentevent_posttitleevent_and_more"),
        ("pghistory", "0006_delete_aggregateevent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CommentHistory",
            fields=[
                ("pgh_id", models.AutoField(primary_key=True, serialize=False)),
                ("pgh_created_at", models.DateTimeField(auto_now_add=True)),
                ("pgh_label", models.TextField(help_text="The event label.")),
                ("id", models.BigIntegerField()),
                ("content", models.TextField(max_length=10000)),
                ("votes", models.IntegerField(default=1)),
                ("date", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PostHistory",
            fields=[
                ("pgh_id", models.AutoField(primary_key=True, serialize=False)),
                ("pgh_created_at", models.DateTimeField(auto_now_add=True)),
                ("pgh_label", models.TextField(help_text="The event label.")),
                ("id", models.BigIntegerField()),
                ("title", models.CharField(max_length=120)),
                ("url", models.CharField(max_length=300)),
                ("votes", models.IntegerField(default=1)),
                ("date", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RemoveField(
            model_name="commentcontentevent",
            name="pgh_context",
        ),
        migrations.RemoveField(
            model_name="commentcontentevent",
            name="pgh_obj",
        ),
        migrations.RemoveField(
            model_name="posttitleevent",
            name="pgh_context",
        ),
        migrations.RemoveField(
            model_name="posttitleevent",
            name="pgh_obj",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="comment",
            name="insert_insert",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="comment",
            name="update_update",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="post",
            name="insert_insert",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="post",
            name="update_update",
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="comment",
            trigger=pgtrigger.compiler.Trigger(
                name="content_changed_update",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    condition='WHEN (OLD."content" IS DISTINCT FROM (NEW."content"))',
                    func='INSERT INTO "app_commenthistory" ("content", "date", "id", "parent_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "post_id", "user_id", "votes") VALUES (OLD."content", OLD."date", OLD."id", OLD."parent_id", _pgh_attach_context(), NOW(), \'content_changed\', OLD."id", OLD."post_id", OLD."user_id", OLD."votes"); RETURN NULL;',
                    hash="4f843d11da7bc54e830fb4803209e900eea1fba5",
                    operation="UPDATE",
                    pgid="pgtrigger_content_changed_update_880c3",
                    table="app_comment",
                    when="AFTER",
                ),
            ),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="post",
            trigger=pgtrigger.compiler.Trigger(
                name="title_changed_update",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    condition='WHEN (OLD."title" IS DISTINCT FROM (NEW."title"))',
                    func='INSERT INTO "app_posthistory" ("board_id", "date", "id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "title", "url", "user_id", "votes") VALUES (OLD."board_id", OLD."date", OLD."id", _pgh_attach_context(), NOW(), \'title_changed\', OLD."id", OLD."title", OLD."url", OLD."user_id", OLD."votes"); RETURN NULL;',
                    hash="9e8184d554e55ca48b1c5be5cdaae7d20a2fcdc6",
                    operation="UPDATE",
                    pgid="pgtrigger_title_changed_update_34f81",
                    table="app_post",
                    when="AFTER",
                ),
            ),
        ),
        migrations.AddField(
            model_name="commenthistory",
            name="parent",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="app.comment",
            ),
        ),
        migrations.AddField(
            model_name="commenthistory",
            name="pgh_context",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="pghistory.context",
            ),
        ),
        migrations.AddField(
            model_name="commenthistory",
            name="pgh_obj",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="events",
                to="app.comment",
            ),
        ),
        migrations.AddField(
            model_name="commenthistory",
            name="post",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="app.post",
            ),
        ),
        migrations.AddField(
            model_name="commenthistory",
            name="user",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="posthistory",
            name="board",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="app.board",
            ),
        ),
        migrations.AddField(
            model_name="posthistory",
            name="pgh_context",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="pghistory.context",
            ),
        ),
        migrations.AddField(
            model_name="posthistory",
            name="pgh_obj",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="events",
                to="app.post",
            ),
        ),
        migrations.AddField(
            model_name="posthistory",
            name="user",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.DeleteModel(
            name="CommentContentEvent",
        ),
        migrations.DeleteModel(
            name="PostTitleEvent",
        ),
    ]