from django.contrib import admin, messages

from .models import PaymentEvent
from .processing import replay


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ["id", "event_type", "provider_order_id", "status", "attempts", "next_run_at", "created_at"]
    list_filter = ["status", "event_type", "provider"]
    search_fields = ["event_id", "provider_order_id", "payment_id"]
    readonly_fields = [f.name for f in PaymentEvent._meta.fields]
    actions = ["replay_selected"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Replay selected events (back to the queue)")
    def replay_selected(self, request, queryset):
        n = replay(list(queryset.values_list("pk", flat=True)))
        self.message_user(request, f"{n} event(s) put back in the queue.", messages.SUCCESS)
