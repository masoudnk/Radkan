import ast
import json
from pickle import FALSE

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db.models.signals import pre_save, pre_delete, post_delete, m2m_changed, post_save
from django.dispatch import receiver

from employer.apps import get_this_app_name
from employer.get_request import current_request, current_data


# def receiver_with_multiple_senders(signal, senders, **kwargs):
#     """
#     Based on django.dispatch.dispatcher.receiver
#
#     Allows multiple senders so we can avoid using a stack of
#     regular receiver decorators with one sender each.
#     """
#
#     def decorator(receiver_func):
#         for sender in senders:
#             if isinstance(signal, (list, tuple)):
#                 for s in signal:
#                     s.connect(receiver_func, sender=sender, **kwargs)
#             else:
#                 signal.connect(receiver_func, sender=sender, **kwargs)
#
#         return receiver_func
#
#     return decorator
# @receiver_with_multiple_senders(signal, [mymodel1, mymodel2])
@receiver(pre_save,
          weak=FALSE,
          dispatch_uid='pre_save')
def pre_save_signal(sender, instance, raw, using, update_fields, **kwargs):
    if sender._meta.app_label == get_this_app_name():
        if instance.id and FALSE:
            old_obj = sender.objects.get(pk=instance.pk)
            serialized_obj = serializers.serialize('json', [old_obj, instance])
            # deserialized_obj = ast.literal_eval(serialized_obj)
            deserialized_obj = json.loads(serialized_obj)
            if deserialized_obj[0]['fields'] != deserialized_obj[1]['fields']:
                LogEntry.objects.create(
                    user=current_request().user,
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id,
                    object_repr=str(instance),
                    action_flag=CHANGE,
                    change_message="old:{},new:{}".format(deserialized_obj[0]['fields'], deserialized_obj[1]['fields'])
                )



@receiver(post_save,
          weak=FALSE,
          dispatch_uid='post_save')
def post_save_signal(sender, instance, created, raw, using, update_fields, **kwargs):
    if sender._meta.app_label == get_this_app_name():
        if created:
            LogEntry.objects.create(
                user=current_request().user,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                object_repr=str(instance),
                action_flag=ADDITION,
                change_message=current_data()
            )


@receiver(pre_delete,
          weak=FALSE,
          dispatch_uid='pre_delete')
def pre_delete_signal(sender, instance, using, origin, **kwargs):
    if sender._meta.app_label == get_this_app_name():
        serialized_obj = serializers.serialize('json', [instance])
        LogEntry.objects.create(
            user=current_request().user,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            object_repr=str(instance),
            action_flag=DELETION,
            change_message="deleted:" + serialized_obj
        )


@receiver(post_delete,
          weak=FALSE,
          dispatch_uid='post_delete')
def post_delete_signal(sender, instance, using, origin, **kwargs):
    pass


@receiver(m2m_changed,
          weak=FALSE,
          dispatch_uid='m2m_changed')
def m2m_changed_signal(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action == "pre_add":
        pass
    elif action == "post_add":
        pass
    elif action == "pre_remove":
        pass
    elif action == "post_remove":
        pass
    elif action == "pre_clear":
        pass
    elif action == "post_clear":
        pass
